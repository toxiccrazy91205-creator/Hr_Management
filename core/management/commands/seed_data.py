import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import EmployeeProfile, CompanyPolicy, FAQ

class Command(BaseCommand):
    help = 'Seeds the database with test HR and Employee users and dummy policies/FAQs'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Create HR User
        if not User.objects.filter(username="hr@company.com").exists():
            hr_user = User.objects.create_user(
                username="hr@company.com",
                email="hr@company.com",
                password="admin123"
            )
            EmployeeProfile.objects.create(
                user=hr_user,
                is_hr=True,
                department="Human Resources"
            )
            self.stdout.write(self.style.SUCCESS("Created HR user: hr@company.com / admin123"))
        else:
            self.stdout.write("HR user already exists.")

        # 2. Create Employee User
        if not User.objects.filter(username="employee@company.com").exists():
            emp_user = User.objects.create_user(
                username="employee@company.com",
                email="employee@company.com",
                password="pass123"
            )
            EmployeeProfile.objects.create(
                user=emp_user,
                is_hr=False,
                department="Engineering",
                salary=85000.00,
                leave_balance=14,
                attendance_score=95
            )
            self.stdout.write(self.style.SUCCESS("Created Employee user: employee@company.com / pass123"))
        else:
            self.stdout.write("Employee user already exists.")

        # 3. Create Dummy Policies
        policies = [
            {
                "title": "Work From Home Policy",
                "content": "Employees in the Engineering department are allowed to work from home up to 3 days a week. Tuesdays and Thursdays are mandatory office days for all-hands meetings. Equipment provided by the company must remain at the primary remote workspace."
            },
            {
                "title": "Leave Policy",
                "content": "All full-time employees are entitled to 20 days of paid time off (PTO) per year. Sick leave is unlimited but requires a doctor's note for absences longer than 3 consecutive days. Leaves must be requested at least 2 weeks in advance via the HR portal."
            },
            {
                "title": "Reimbursement Policy",
                "content": "Internet and home office expenses can be reimbursed up to $100 per month. Travel for conferences must be pre-approved by the department head. Receipts are mandatory for all expense claims."
            }
        ]

        for p_data in policies:
            CompanyPolicy.objects.get_or_create(
                title=p_data["title"],
                defaults={"content": p_data["content"]}
            )
        self.stdout.write(self.style.SUCCESS("Seeded dummy policies."))

        # 4. Create Dummy FAQs
        faqs = [
            {
                "question": "How do I request a new laptop?",
                "answer": "You can request a new laptop by opening a ticket in the IT Helpdesk portal. Hardware upgrades are typically approved if your current machine is older than 3 years."
            },
            {
                "question": "What is the process for performance reviews?",
                "answer": "Performance reviews are conducted bi-annually in June and December. You will receive a self-evaluation form two weeks prior to your manager 1-on-1."
            },
            {
                "question": "When is payday?",
                "answer": "Salaries are disbursed on the 15th and the last working day of every month."
            }
        ]

        for f_data in faqs:
            FAQ.objects.get_or_create(
                question=f_data["question"],
                defaults={"answer": f_data["answer"]}
            )
        self.stdout.write(self.style.SUCCESS("Seeded dummy FAQs."))

        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))
