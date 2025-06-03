# BusinessPartnerMasterData/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessPartnerViewSet,
    BusinessPartnerGroupViewSet,
    AddressViewSet,
    BussinessPartnerCodeGenerationView,
    ContactPersonViewSet,
    FinancialInformationViewSet,
    ContactInformationViewSet,
    TestView
)

app_name = 'businesspartner_api'

# Create a router and register our viewsets with it
router = DefaultRouter()
# router.register(r'', BusinessPartnerViewSet)

router.register(r'business-partner', BusinessPartnerViewSet)

# router.register(r'business-partner-groups', BusinessPartnerGroupViewSet)
# router.register(r'addresses', AddressViewSet)
# router.register(r'contact-persons', ContactPersonViewSet)
# router.register(r'financial-information', FinancialInformationViewSet)
# router.register(r'contact-information', ContactInformationViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('code_ger/', BussinessPartnerCodeGenerationView.as_view(), name='bp_code_ger'),
    path('test/', TestView.as_view(), name='test'),

]