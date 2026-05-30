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
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from core.models import JobPosting, Candidate, EmployeeProfile, CompanyPolicy, FAQ, PerformanceRecord

def is_hr_check(user):
    return user.is_authenticated and hasattr(user, 'employeeprofile') and user.employeeprofile.is_hr

def is_employee_check(user):
    return user.is_authenticated and hasattr(user, 'employeeprofile') and not user.employeeprofile.is_hr

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

@login_required
@user_passes_test(is_hr_check)
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

@login_required
@user_passes_test(is_hr_check)
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

@login_required
@user_passes_test(is_hr_check)
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

@login_required
@user_passes_test(is_hr_check)
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

@login_required
@user_passes_test(is_hr_check)
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

@login_required
@user_passes_test(is_hr_check)
def attendance_report_view(request):
    """Display the AI-generated attendance report from session."""
    reports = request.session.get('attendance_reports', [])
    return render(request, "attendance_report.html", {"reports": reports})


# ──────────────────────────────────────────────────────────────────────────────
# View 7: Attendance Tracker — Download report as PDF
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_hr_check)
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


# ──────────────────────────────────────────────────────────────────────────────
# View 8: Authentication Views (Login, Signup, Logout)
# ──────────────────────────────────────────────────────────────────────────────

def custom_login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, 'employeeprofile') and user.employeeprofile.is_hr:
                return redirect("core:dashboard")
            return redirect("core:employee_chat")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Default new signups to Employee
            EmployeeProfile.objects.create(
                user=user,
                is_hr=False,
                department="General",
                salary=50000.00,
                leave_balance=10,
                attendance_score=100
            )
            login(request, user)
            return redirect("core:employee_chat")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})

def custom_logout_view(request):
    logout(request)
    return redirect("core:login")


# ──────────────────────────────────────────────────────────────────────────────
# View 9: HR Management (CRUD for Policies & FAQs)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_hr_check)
def hr_data_management_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_policy":
            policy_id = request.POST.get("policy_id")
            if policy_id:
                CompanyPolicy.objects.filter(id=policy_id).update(
                    title=request.POST.get("title"),
                    content=request.POST.get("content")
                )
                messages.success(request, "Policy updated successfully.")
            else:
                CompanyPolicy.objects.create(
                    title=request.POST.get("title"),
                    content=request.POST.get("content")
                )
                messages.success(request, "Policy added successfully.")
        elif action == "delete_policy":
            policy_id = request.POST.get("policy_id")
            if policy_id:
                CompanyPolicy.objects.filter(id=policy_id).delete()
                messages.success(request, "Policy deleted successfully.")
        elif action == "add_faq":
            faq_id = request.POST.get("faq_id")
            if faq_id:
                FAQ.objects.filter(id=faq_id).update(
                    question=request.POST.get("question"),
                    answer=request.POST.get("answer")
                )
                messages.success(request, "FAQ updated successfully.")
            else:
                FAQ.objects.create(
                    question=request.POST.get("question"),
                    answer=request.POST.get("answer")
                )
                messages.success(request, "FAQ added successfully.")
        elif action == "delete_faq":
            faq_id = request.POST.get("faq_id")
            if faq_id:
                FAQ.objects.filter(id=faq_id).delete()
                messages.success(request, "FAQ deleted successfully.")
        return redirect("core:hr_manage_data")
        
    policies = CompanyPolicy.objects.all()
    faqs = FAQ.objects.all()
    employees = EmployeeProfile.objects.filter(is_hr=False)
    
    return render(request, "hr_manage_data.html", {
        "policies": policies,
        "faqs": faqs,
        "employees": employees
    })


# ──────────────────────────────────────────────────────────────────────────────
# View 10: Employee Chatbot
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_employee_check)
def employee_chat_view(request):
    return render(request, "employee_chat.html")

@login_required
@user_passes_test(is_employee_check)
def api_chat_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            
            from ai_engine.support_agent import generate_support_response
            response_text = generate_support_response(message, request.user.employeeprofile)
            
            return JsonResponse({"response": response_text})
        except Exception as e:
            logger.exception("Chat API Error")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)


# ──────────────────────────────────────────────────────────────────────────────
# View 11: Performance Review Dashboard (Bulk Upload)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_hr_check)
def hr_performance_dashboard_view(request):
    """Handles global Excel upload for bulk Performance Reviews."""
    if request.method == "POST":
        review_period = request.POST.get("review_period")
        excel_file = request.FILES.get("performance_excel")
        
        try:
            import pandas as pd
            if not excel_file:
                raise ValueError("No Excel file uploaded.")
                
            df = pd.read_excel(excel_file)
            
            # Flexible identifier column matching
            identifier_col = None
            is_id = False
            for col in df.columns:
                col_lower = col.lower()
                if 'email' in col_lower or 'username' in col_lower or 'name' in col_lower:
                    identifier_col = col
                    break
                elif 'id' == col_lower or 'employee id' in col_lower:
                    identifier_col = col
                    is_id = True
                    break
            
            if not identifier_col:
                raise ValueError("Excel file must contain an 'Employee Name', 'Username', 'Email', or 'Employee ID' column to identify employees.")
            
            processed_record_ids = []
            
            for index, row in df.iterrows():
                identifier = str(row[identifier_col]).strip()
                
                # Try to find the employee
                employee = None
                try:
                    if is_id and identifier.replace('.','',1).isdigit():
                        employee = EmployeeProfile.objects.get(id=int(float(identifier)), is_hr=False)
                    elif '@' in identifier:
                        employee = EmployeeProfile.objects.get(user__email=identifier, is_hr=False)
                    else:
                        employee = EmployeeProfile.objects.get(user__username=identifier, is_hr=False)
                except EmployeeProfile.DoesNotExist:
                    pass # We will auto-create below
                
                # Auto-create the employee if they don't exist in the DB (great for testing arbitrary Excel files)
                if not employee:
                    from django.contrib.auth.models import User
                    
                    # Try to get an actual name if the identifier was an ID
                    display_name = str(identifier)
                    if is_id:
                        for col in row.index:
                            if 'name' in col.lower():
                                display_name = str(row[col])
                                break
                                
                    safe_username = str(display_name).replace(" ", "_").lower()
                    if not safe_username:
                        continue
                        
                    # Handle case where user might already exist but no EmployeeProfile
                    try:
                        user = User.objects.get(username=safe_username)
                    except User.DoesNotExist:
                        user = User.objects.create(username=safe_username, email=f"{safe_username}@demo.com", first_name=str(display_name))
                        
                    employee, _ = EmployeeProfile.objects.get_or_create(
                        user=user,
                        defaults={'is_hr': False, 'department': 'General'}
                    )
                
                # Process with LLM
                from ai_engine.performance_agent import generate_performance_review
                # Convert row to dict
                row_dict = row.to_dict()
                row_data_str = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
                
                result = generate_performance_review(
                    employee_profile=employee,
                    row_data=row_data_str
                )
                
                # Save the record
                record = PerformanceRecord.objects.create(
                    employee=employee,
                    review_period=review_period,
                    kpi_data=row_data_str, # Store row data here
                    task_completion_rate=0.0, # Deprecated
                    manager_feedback="See Excel Data", # Deprecated
                    performance_score=result.get("performance_score"),
                    kpi_achievement_percent=result.get("kpi_achievement_percent"),
                    strengths=result.get("strengths"),
                    areas_for_improvement=result.get("areas_for_improvement"),
                    recommended_actions=result.get("recommended_actions"),
                )
                processed_record_ids.append(record.id)
            
            if not processed_record_ids:
                raise ValueError("No matching employees found in the Excel file.")
                
            # Store processed IDs in session to display them on the report page
            request.session['latest_performance_records'] = processed_record_ids
            
            messages.success(request, f"Successfully generated {len(processed_record_ids)} performance reviews!")
            return redirect("core:view_performance_report")
            
        except Exception as e:
            logger.exception("Performance bulk generation failed")
            messages.error(request, f"Failed to generate reviews: {str(e)}")
            return redirect("core:hr_performance_dashboard")

    return render(request, "hr_performance_dashboard.html")

# ──────────────────────────────────────────────────────────────────────────────
# View 12: View Performance Report
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_hr_check)
def view_performance_report_view(request):
    """Displays the AI-generated structured performance reports from the bulk upload."""
    record_ids = request.session.get('latest_performance_records', [])
    records = PerformanceRecord.objects.filter(id__in=record_ids)
    
    if not records.exists():
        messages.warning(request, "No recent reports to display.")
        return redirect("core:hr_performance_dashboard")
        
    return render(request, "performance_report.html", {"records": records})

# ──────────────────────────────────────────────────────────────────────────────
# View 13: Download Performance PDF
# ──────────────────────────────────────────────────────────────────────────────
import io
from django.http import HttpResponse

@login_required
@user_passes_test(is_hr_check)
def performance_download_pdf_view(request):
    """Generates a PDF of all recently processed performance reports."""
    record_ids = request.session.get('latest_performance_records', [])
    records = PerformanceRecord.objects.filter(id__in=record_ids)
    
    if not records.exists():
        messages.error(request, "No reports available for download.")
        return redirect("core:hr_performance_dashboard")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    sub_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements.append(Paragraph("Performance Review Reports (Bulk Generated)", title_style))
    elements.append(Spacer(1, 20))
    
    for record in records:
        elements.append(Paragraph(f"Employee: {record.employee.user.username} ({record.employee.user.email})", sub_style))
        elements.append(Paragraph(f"Review Period: {record.review_period}", normal_style))
        elements.append(Paragraph(f"AI Performance Score: {record.performance_score}/100", normal_style))
        elements.append(Paragraph(f"KPI Achievement: {record.kpi_achievement_percent}%", normal_style))
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Strengths:", styles['Heading4']))
        elements.append(Paragraph(record.strengths.replace('\n', '<br/>'), normal_style))
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Areas for Improvement:", styles['Heading4']))
        elements.append(Paragraph(record.areas_for_improvement.replace('\n', '<br/>'), normal_style))
        
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Recommended Actions:", styles['Heading4']))
        elements.append(Paragraph(record.recommended_actions.replace('\n', '<br/>'), normal_style))
        
        elements.append(Spacer(1, 30))
        
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="performance_reports.pdf"'
    return response
