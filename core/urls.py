from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),

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
    path(
        "attendance/download/",
        views.attendance_download_pdf_view,
        name="attendance_download_pdf",
    ),
    path("login/", views.custom_login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.custom_logout_view, name="logout"),
    path("hr/manage/", views.hr_data_management_view, name="hr_manage_data"),
    path("performance/dashboard/", views.hr_performance_dashboard_view, name="hr_performance_dashboard"),
    path("performance/report/", views.view_performance_report_view, name="view_performance_report"),
    path("performance/download-pdf/", views.performance_download_pdf_view, name="performance_download_pdf"),
    path("employee/chat/", views.employee_chat_view, name="employee_chat"),
    path("api/chat/", views.api_chat_view, name="api_chat"),
    path("attendance/export-excel/", views.attendance_export_excel_view, name="attendance_export_excel"),
    path("api/attendance/tap", views.hardware_tap_api, name="hardware_tap_api"),
]
