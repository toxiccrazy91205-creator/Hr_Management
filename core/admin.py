from django.contrib import admin
from .models import JobPosting, Candidate, EmployeeProfile, CompanyPolicy, FAQ, PerformanceRecord, AttendanceLog


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


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_hr", "department", "leave_balance")
    list_filter = ("is_hr", "department")


@admin.register(CompanyPolicy)
class CompanyPolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "last_updated")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question",)

@admin.register(PerformanceRecord)
class PerformanceRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "review_period", "performance_score", "created_at")
    list_filter = ("review_period",)
    search_fields = ("employee__user__username", "review_period")


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "tap_type", "timestamp", "device_type", "location")
    list_filter = ("tap_type", "device_type")
    search_fields = ("employee_id", "location")
    ordering = ("-timestamp",)
