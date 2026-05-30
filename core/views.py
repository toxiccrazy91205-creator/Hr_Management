"""
views.py — Django views for the HR Recruitment System.

Views:
  • dashboard_view       — Upload resumes + enter job details → trigger AI pipeline
  • approval_view        — Human-in-the-loop review of shortlist & email drafts
  • approve_and_send_view — Resume the LangGraph to dispatch emails
  • success_view         — Confirmation page after emails are sent
"""

import os
import uuid
import json
import logging
import traceback

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from core.models import JobPosting, Candidate

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: save uploaded files to MEDIA_ROOT/resumes/
# ──────────────────────────────────────────────────────────────────────────────

def _save_uploaded_files(files) -> list[str]:
    """Persist uploaded files to disk and return their absolute paths."""
    upload_dir = os.path.join(settings.MEDIA_ROOT, "resumes")
    os.makedirs(upload_dir, exist_ok=True)
    saved_paths = []
    for f in files:
        # Prefix with uuid to avoid collisions
        filename = f"{uuid.uuid4().hex[:8]}_{f.name}"
        dest = os.path.join(upload_dir, filename)
        with open(dest, "wb+") as fh:
            for chunk in f.chunks():
                fh.write(chunk)
        saved_paths.append(dest)
    return saved_paths


# ──────────────────────────────────────────────────────────────────────────────
# View 1: Dashboard — job form + resume upload
# ──────────────────────────────────────────────────────────────────────────────

def dashboard_view(request):
    """
    GET  → render the dashboard form (optionally pre-filled via ?resume=<job_id>).
    POST → accept job details + resumes, run the AI pipeline (steps 1-6),
           then redirect to the approval page.
    """
    if request.method == "POST":
        # ── Validate inputs ──────────────────────────────────────────────
        title = request.POST.get("job_title", "").strip()
        description = request.POST.get("job_description", "").strip()
        skills = request.POST.get("required_skills", "").strip()
        experience = request.POST.get("experience_years", "0").strip()
        files = request.FILES.getlist("resumes")
        resume_job_id = request.POST.get("resume_job_id", "").strip()

        if not title or not description or not skills:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "dashboard.html", {"recent_jobs": JobPosting.objects.all()[:10]})

        if not files:
            messages.error(request, "Please upload at least one resume (PDF or DOCX).")
            return render(request, "dashboard.html", {"recent_jobs": JobPosting.objects.all()[:10]})

        try:
            experience_years = int(experience)
        except ValueError:
            experience_years = 0

        # ── Save files to disk ───────────────────────────────────────────
        saved_paths = _save_uploaded_files(files)

        # ── Create or reuse JobPosting record ────────────────────────────
        if resume_job_id:
            try:
                job = JobPosting.objects.get(pk=resume_job_id)
                job.title = title
                job.description = description
                job.required_skills = skills
                job.experience_years = experience_years
                job.status = "screening"
                job.save()
                # Clear old candidates from any previous failed run
                job.candidates.all().delete()
            except JobPosting.DoesNotExist:
                job = JobPosting.objects.create(
                    title=title,
                    description=description,
                    required_skills=skills,
                    experience_years=experience_years,
                    status="screening",
                )
        else:
            job = JobPosting.objects.create(
                title=title,
                description=description,
                required_skills=skills,
                experience_years=experience_years,
                status="screening",
            )

        # ── Run the LangGraph (steps 1-6, pauses before send_emails) ────
        thread_id = str(job.id)
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "job_id": str(job.id),
            "job_title": title,
            "job_description": description,
            "required_skills": skills,
            "experience_years": experience_years,
            "uploaded_file_paths": saved_paths,
        }

        try:
            from ai_engine.graph import hr_graph

            # .invoke() runs until interrupt_before pauses the graph
            result = hr_graph.invoke(initial_state, config=config)

            # ── Persist shortlisted candidates into DB ───────────────────
            shortlisted = result.get("shortlisted_candidates", [])
            email_drafts = result.get("email_drafts", [])
            scheduled = result.get("scheduled_candidates", [])

            # Build lookup of email drafts by name
            draft_map = {d.get("name", ""): d for d in email_drafts}

            for candidate_data in shortlisted:
                name = candidate_data.get("name", "Unknown")
                email = candidate_data.get("email", "")
                score = candidate_data.get("match_score", 0)
                matched = candidate_data.get("matched_skills", "")
                slot = candidate_data.get("interview_slot", "TBD")
                source = candidate_data.get("source_file", "")

                # Get corresponding email draft
                draft_info = draft_map.get(name, {})
                subject = draft_info.get("subject", "")
                body = draft_info.get("body", "")
                drafted_email_text = f"Subject: {subject}\n\n{body}" if subject else ""

                Candidate.objects.create(
                    job=job,
                    name=name,
                    email=email if email else None,
                    match_score=float(score),
                    matched_skills=matched,
                    interview_slot=slot,
                    drafted_email=drafted_email_text,
                    resume_source=source,
                    status="email_drafted",
                )

            # Save thread ID and update status
            job.langgraph_thread_id = thread_id
            job.status = "pending_approval"
            job.save()

            messages.success(
                request,
                f"AI screening complete! {len(shortlisted)} candidate(s) shortlisted."
            )
            return redirect("core:approval", job_id=job.id)

        except Exception as exc:
            logger.exception("AI pipeline failed")
            job.status = "draft"
            job.save()
            messages.error(
                request,
                f"AI pipeline error: {exc}. Please check your API key and try again."
            )
            return render(request, "dashboard.html", {
                "recent_jobs": JobPosting.objects.all()[:10],
                "resume_job": job,
            })

    # GET request — check for ?resume=<job_id> to pre-fill form
    recent_jobs = JobPosting.objects.all()[:10]
    resume_job = None
    resume_id = request.GET.get("resume")
    if resume_id:
        try:
            resume_job = JobPosting.objects.get(pk=resume_id)
        except (JobPosting.DoesNotExist, ValueError):
            pass

    return render(request, "dashboard.html", {
        "recent_jobs": recent_jobs,
        "resume_job": resume_job,
    })


# ──────────────────────────────────────────────────────────────────────────────
# View 2: Approval — human-in-the-loop review
# ──────────────────────────────────────────────────────────────────────────────

def approval_view(request, job_id):
    """Display shortlisted candidates and drafted emails for HR approval."""
    job = get_object_or_404(JobPosting, pk=job_id)
    candidates = job.candidates.all()
    return render(request, "approval.html", {
        "job": job,
        "candidates": candidates,
    })


# ──────────────────────────────────────────────────────────────────────────────
# View 3: Approve and Send — resume the LangGraph
# ──────────────────────────────────────────────────────────────────────────────

def approve_and_send_view(request, job_id):
    """
    POST → Resume the LangGraph to execute the send_emails node,
           update candidate records, redirect to success.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed.")

    job = get_object_or_404(JobPosting, pk=job_id)
    thread_id = job.langgraph_thread_id or str(job.id)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        from ai_engine.graph import hr_graph

        # Resume the graph from the interrupt point — pass None as input
        # to continue with the existing state
        result = hr_graph.invoke(None, config=config)

        # Mark candidates as sent
        job.candidates.filter(status="email_drafted").update(
            status="email_sent", email_sent=True
        )
        job.status = "approved"
        job.save()

        messages.success(request, "All emails have been sent successfully!")
        return redirect("core:success", job_id=job.id)

    except Exception as exc:
        logger.exception("Email sending failed")
        messages.error(request, f"Email dispatch error: {exc}")
        return redirect("core:approval", job_id=job.id)


# ──────────────────────────────────────────────────────────────────────────────
# View 4: Success — final confirmation
# ──────────────────────────────────────────────────────────────────────────────

def success_view(request, job_id):
    """Display the final success page with sent-email summary."""
    job = get_object_or_404(JobPosting, pk=job_id)
    candidates = job.candidates.filter(email_sent=True)
    return render(request, "success.html", {
        "job": job,
        "candidates": candidates,
    })


# ──────────────────────────────────────────────────────────────────────────────
# View 5: Attendance Tracker — Upload timesheet
# ──────────────────────────────────────────────────────────────────────────────

def attendance_upload_view(request):
    """
    GET  → Render the upload form.
    POST → Save the uploaded Excel file, generate report, and store in session.
    """
    if request.method == "POST":
        uploaded_file = request.FILES.get("attendance_file")
        if not uploaded_file:
            messages.error(request, "Please upload an Excel file.")
            return render(request, "attendance.html")
            
        if not (uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls')):
            messages.error(request, "Invalid file format. Please upload .xlsx or .xls files only.")
            return render(request, "attendance.html")

        # Save temporarily
        upload_dir = os.path.join(settings.MEDIA_ROOT, "attendance")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb+") as fh:
            for chunk in uploaded_file.chunks():
                fh.write(chunk)
                
        try:
            from ai_engine.attendance import generate_attendance_report
            reports = generate_attendance_report(file_path)
            
            # Store reports in session to pass to the report view
            request.session['attendance_reports'] = reports
            messages.success(request, "Timesheet processed successfully!")
            return redirect("core:attendance_report")
            
        except Exception as exc:
            logger.exception("Attendance processing failed")
            messages.error(request, f"Failed to process timesheet: {exc}")
            return render(request, "attendance.html")

    return render(request, "attendance.html")


# ──────────────────────────────────────────────────────────────────────────────
# View 6: Attendance Tracker — View report
# ──────────────────────────────────────────────────────────────────────────────

def attendance_report_view(request):
    """Display the AI-generated attendance report from session."""
    reports = request.session.get('attendance_reports', [])
    return render(request, "attendance_report.html", {"reports": reports})


# ──────────────────────────────────────────────────────────────────────────────
# View 7: Attendance Tracker — Download report as PDF
# ──────────────────────────────────────────────────────────────────────────────

def attendance_download_pdf_view(request):
    """Download the attendance report from session as a PDF file."""
    reports = request.session.get('attendance_reports', [])
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    elements.append(Paragraph("AI Attendance Report", title_style))
    elements.append(Spacer(1, 20))
    
    data = [['Employee Name', 'Total Hours', 'Leaves Taken', 'AI Score', 'Agent Feedback']]
    
    for report in reports:
        data.append([
            report.get('name', ''),
            str(report.get('total_hours', '')),
            str(report.get('leaves_taken', '')),
            str(report.get('ai_score', '')),
            Paragraph(str(report.get('ai_feedback', '')), styles['Normal'])
        ])
        
    table = Table(data, colWidths=[120, 80, 80, 70, 370])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0a0e1a')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response
