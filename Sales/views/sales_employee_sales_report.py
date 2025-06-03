# views/sales_employee_sales_report.py

from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
from datetime import date
from django.db.models import Sum
from Sales.models import SalesOrder, SalesEmployee

class SalesEmployeeSalesReportView(TemplateView):
    template_name = "sales/sales_employee_sales_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)

        # ✅ All sales employees – Today
        today_sales = (
            SalesOrder.objects.filter(document_date=today)
            .values("sales_employee__name")
            .annotate(total_sales=Sum("total_amount"))
        )

        # ✅ All sales employees – This Month
        month_sales = (
            SalesOrder.objects.filter(document_date__range=[first_day_of_month, today])
            .values("sales_employee__name")
            .annotate(total_sales=Sum("total_amount"))
        )
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        last_30_days = today - timedelta(days=30)
        
        last_30_days_sales = (
            SalesOrder.objects.filter(document_date__gte=last_30_days)
            .values("sales_employee__name")
            .annotate(total_sales=Sum("total_amount"))
        )        
        # ✅ Current user if they are a SalesEmployee
        user_sales_today = []
        user_sales_month = []
        if hasattr(self.request.user, 'sales_employee'):
            emp = self.request.user.sales_employee
            user_sales_today = SalesOrder.objects.filter(
                document_date=today,
                sales_employee=emp
            ).aggregate(total_sales=Sum("total_amount"))

            user_sales_month = SalesOrder.objects.filter(
                document_date__range=[first_day_of_month, today],
                sales_employee=emp
            ).aggregate(total_sales=Sum("total_amount"))

        context.update({
            "today_sales": today_sales,
            "month_sales": month_sales,
            "user_sales_today": user_sales_today,
            "user_sales_month": user_sales_month,
            "is_sales_employee": hasattr(self.request.user, 'sales_employee'),
            "last_30_days_sales": last_30_days_sales,

        })
        return context
