from django.contrib import admin
from .models import JobPosting, Candidate


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 0
    readonly_fields = (
        "name", "email", "match_score", "matched_skills",
        "interview_slot", "drafted_email", "email_sent", "status",
    )


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "experience_years", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description")
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "match_score", "status", "email_sent", "job")
    list_filter = ("status", "email_sent")
    search_fields = ("name", "email")
