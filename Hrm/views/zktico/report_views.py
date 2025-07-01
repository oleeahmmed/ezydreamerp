from django.views.generic import TemplateView
import logging
logger = logging.getLogger(__name__)
class HrmReportListView(TemplateView):
    template_name = 'report/hrm/hrm_report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inventory Reports'
        logger.debug("Rendering inventory reports list page")
        return context