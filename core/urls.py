from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path(
        "approval/<uuid:job_id>/",
        views.approval_view,
        name="approval",
    ),
    path(
        "approve/<uuid:job_id>/",
        views.approve_and_send_view,
        name="approve_and_send",
    ),
    path(
        "success/<uuid:job_id>/",
        views.success_view,
        name="success",
    ),
    path(
        "attendance/",
        views.attendance_upload_view,
        name="attendance_upload",
    ),
    path(
        "attendance/report/",
        views.attendance_report_view,
        name="attendance_report",
    ),
]
