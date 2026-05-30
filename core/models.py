"""
Data models for the HR Recruitment System.
- JobPosting: Represents a job the recruiter is hiring for.
- Candidate: Represents a candidate matched/shortlisted for a job.
"""
import uuid
from django.db import models


class JobPosting(models.Model):
    """A job posting created by an HR recruiter."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Job role / title")
    description = models.TextField(help_text="Detailed job description")
    required_skills = models.TextField(
        help_text="Comma-separated list of required skills"
    )
    experience_years = models.PositiveIntegerField(
        default=0, help_text="Minimum years of experience required"
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ("draft", "Draft"),
            ("screening", "Screening in progress"),
            ("pending_approval", "Pending HR approval"),
            ("approved", "Approved & emails sent"),
            ("completed", "Completed"),
        ],
        default="draft",
    )
    # LangGraph thread ID for checkpointing / resuming
    langgraph_thread_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Thread ID used by LangGraph for checkpoint resumption"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Candidate(models.Model):
    """A candidate extracted and evaluated from uploaded resumes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        JobPosting, on_delete=models.CASCADE, related_name="candidates"
    )
    name = models.CharField(max_length=255, default="Unknown")
    email = models.EmailField(blank=True, null=True)
    match_score = models.FloatField(
        default=0.0, help_text="AI-assigned match score (0-100)"
    )
    matched_skills = models.TextField(
        blank=True, help_text="Skills that matched the job requirements"
    )
    interview_slot = models.CharField(
        max_length=255, blank=True,
        help_text="Assigned interview time slot"
    )
    drafted_email = models.TextField(
        blank=True, help_text="AI-drafted personalized email"
    )
    email_sent = models.BooleanField(default=False)
    resume_source = models.CharField(
        max_length=500, blank=True,
        help_text="Original filename of the resume"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("shortlisted", "Shortlisted"),
            ("email_drafted", "Email Drafted"),
            ("email_sent", "Email Sent"),
            ("rejected", "Rejected"),
        ],
        default="shortlisted",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-match_score"]

    def __str__(self):
        return f"{self.name} — {self.match_score}% match"
