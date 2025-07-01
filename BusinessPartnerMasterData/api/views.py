# BusinessPartnerMasterData/api/views.py
import random
import string
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import (
    BusinessPartner, 
    BusinessPartnerGroup,
    FinancialInformation,
    ContactInformation,
    Address,
    ContactPerson
)
from .serializers import (
    BusinessPartnerListSerializer,
    BusinessPartnerDetailSerializer,
    BusinessPartnerCreateUpdateSerializer,
    BusinessPartnerGroupSerializer,
    FinancialInformationSerializer,
    ContactInformationSerializer,
    AddressSerializer,
    ContactPersonSerializer
)
from .permissions import BusinessPartnerHasDynamicModelPermission

class BusinessPartnerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partners.
    
    Business partners can be customers or suppliers. This endpoint provides CRUD operations
    for business partners and their related information.
    """
    queryset = BusinessPartner.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'bp_type', 'group']
    search_fields = ['code', 'name', 'email', 'phone']
    ordering_fields = ['code', 'name', 'bp_type']
    ordering = ['code']
    swagger_tags = ['Business Partner Master']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return BusinessPartnerDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BusinessPartnerCreateUpdateSerializer
        return BusinessPartnerDetailSerializer

    def get_queryset(self):
        queryset = BusinessPartner.objects.select_related(
            'group', 
            'currency', 
            'payment_terms'
        ).prefetch_related(
            'addresses',
            'contact_persons'
        )
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all business partners",
        operation_description="Returns a list of all business partners the user has access to view.",
        tags=['Business Partner Master']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new business partner",
        operation_description="Creates a new business partner with the provided data.",
        tags=['Business Partner Master']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific business partner",
        operation_description="Returns the details of a specific business partner, including related information.",
        tags=['Business Partner Master']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a business partner",
        operation_description="Updates the specified business partner with the provided data.",
        tags=['Business Partner Master']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a business partner",
        operation_description="Partially updates the specified business partner with the provided data.",
        tags=['Business Partner Master']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a business partner",
        operation_description="Deletes the specified business partner and all related information.",
        tags=['Business Partner Master']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get business partner addresses",
        operation_description="Returns all addresses for a specific business partner.",
        tags=['Business Partner Master']
    )
    @action(detail=True, methods=['get'])
    def addresses(self, request, pk=None):
        """
        Retrieve addresses for a specific business partner
        """
        business_partner = self.get_object()
        addresses = business_partner.addresses.all()
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Get business partner contact persons",
        operation_description="Returns all contact persons for a specific business partner.",
        tags=['Business Partner Master']
    )
    @action(detail=True, methods=['get'])
    def contact_persons(self, request, pk=None):
        """
        Retrieve contact persons for a specific business partner
        """
        business_partner = self.get_object()
        contact_persons = business_partner.contact_persons.all()
        serializer = ContactPersonSerializer(contact_persons, many=True)
        return Response(serializer.data)

class BusinessPartnerGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partner Groups.
    
    Business partner groups are used to categorize business partners for reporting
    and organizational purposes.
    """
    queryset = BusinessPartnerGroup.objects.all()
    serializer_class = BusinessPartnerGroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']
    swagger_tags = ['Business Partner Groups']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all business partner groups",
        operation_description="Returns a list of all business partner groups.",
        tags=['Business Partner Groups']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new business partner group",
        operation_description="Creates a new business partner group with the provided data.",
        tags=['Business Partner Groups']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific business partner group",
        operation_description="Returns the details of a specific business partner group.",
        tags=['Business Partner Groups']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a business partner group",
        operation_description="Updates the specified business partner group with the provided data.",
        tags=['Business Partner Groups']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a business partner group",
        operation_description="Partially updates the specified business partner group with the provided data.",
        tags=['Business Partner Groups']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a business partner group",
        operation_description="Deletes the specified business partner group.",
        tags=['Business Partner Groups']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partner Addresses.
    
    Addresses can be of type Billing or Shipping and are associated with business partners.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_partner', 'address_type', 'is_default']
    search_fields = ['street', 'city', 'state', 'country']
    ordering_fields = ['business_partner', 'address_type']
    ordering = ['business_partner', 'address_type']
    swagger_tags = ['Addresses']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all addresses",
        operation_description="Returns a list of all business partner addresses.",
        tags=['Addresses']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new address",
        operation_description="Creates a new address for a business partner with the provided data.",
        tags=['Addresses']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific address",
        operation_description="Returns the details of a specific address.",
        tags=['Addresses']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an address",
        operation_description="Updates the specified address with the provided data.",
        tags=['Addresses']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update an address",
        operation_description="Partially updates the specified address with the provided data.",
        tags=['Addresses']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an address",
        operation_description="Deletes the specified address.",
        tags=['Addresses']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class ContactPersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partner Contact Persons.
    
    Contact persons are individuals associated with business partners who serve as
    points of contact for communication and transactions.
    """
    queryset = ContactPerson.objects.all()
    serializer_class = ContactPersonSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_partner', 'is_default']
    search_fields = ['name', 'position', 'email', 'phone']
    ordering_fields = ['business_partner', 'name']
    ordering = ['business_partner', 'name']
    swagger_tags = ['Contact Persons']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all contact persons",
        operation_description="Returns a list of all business partner contact persons.",
        tags=['Contact Persons']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new contact person",
        operation_description="Creates a new contact person for a business partner with the provided data.",
        tags=['Contact Persons']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific contact person",
        operation_description="Returns the details of a specific contact person.",
        tags=['Contact Persons']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a contact person",
        operation_description="Updates the specified contact person with the provided data.",
        tags=['Contact Persons']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a contact person",
        operation_description="Partially updates the specified contact person with the provided data.",
        tags=['Contact Persons']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a contact person",
        operation_description="Deletes the specified contact person.",
        tags=['Contact Persons']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class FinancialInformationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partner Financial Information.
    
    Financial information includes credit limits, balances, and payment terms
    for business partners.
    """
    queryset = FinancialInformation.objects.all()
    serializer_class = FinancialInformationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business_partner']
    ordering_fields = ['business_partner', 'credit_limit', 'balance']
    ordering = ['business_partner']
    swagger_tags = ['Financial Information']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all financial information records",
        operation_description="Returns a list of all business partner financial information records.",
        tags=['Financial Information']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create new financial information",
        operation_description="Creates new financial information for a business partner with the provided data.",
        tags=['Financial Information']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve specific financial information",
        operation_description="Returns the financial information details for a specific business partner.",
        tags=['Financial Information']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update financial information",
        operation_description="Updates the specified financial information with the provided data.",
        tags=['Financial Information']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update financial information",
        operation_description="Partially updates the specified financial information with the provided data.",
        tags=['Financial Information']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete financial information",
        operation_description="Deletes the specified financial information record.",
        tags=['Financial Information']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class ContactInformationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Business Partner Contact Information.
    
    Contact information includes phone numbers, email addresses, websites, and
    tax identification numbers for business partners.
    """
    queryset = ContactInformation.objects.all()
    serializer_class = ContactInformationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, BusinessPartnerHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_partner']
    search_fields = ['email', 'phone', 'mobile', 'website']
    ordering_fields = ['business_partner', 'email']
    ordering = ['business_partner']
    swagger_tags = ['Contact Information']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all contact information records",
        operation_description="Returns a list of all business partner contact information records.",
        tags=['Contact Information']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create new contact information",
        operation_description="Creates new contact information for a business partner with the provided data.",
        tags=['Contact Information']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve specific contact information",
        operation_description="Returns the contact information details for a specific business partner.",
        tags=['Contact Information']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update contact information",
        operation_description="Updates the specified contact information with the provided data.",
        tags=['Contact Information']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update contact information",
        operation_description="Partially updates the specified contact information with the provided data.",
        tags=['Contact Information']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete contact information",
        operation_description="Deletes the specified contact information record.",
        tags=['Contact Information']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Max
class BussinessPartnerCodeGenerationView(APIView):
    """
    API endpoint for generating Business Partner codes.
    
    This endpoint provides functionality to generate unique codes for new business partners.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generate a new business partner code
        """
        # Logic to generate a new code
        code = generate_unique_code()
        return Response({"code": code}, status=200)
    
def generate_unique_code():
        """Generate a unique code for a new business partner"""
        # Try to get the highest numeric code
        prefix = "BP"
        try:
            # Find the highest numeric code
            last_bp = BusinessPartner.objects.filter(
                code__startswith=prefix
            ).aggregate(
                Max('code')
            )['code__max']
            
            if last_bp:
                # Extract the numeric part
                try:
                    last_num = int(last_bp[len(prefix):])
                    new_num = last_num + 1
                    return f"{prefix}{new_num:04d}"
                except ValueError:
                    pass
        except Exception:
            pass
        
        # Fallback: Generate a random code
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{random_part}"
    
class TestView(APIView):
    permission_classes = [AllowAny]

    print("Test API endpoint accessed")
    def get (self, request):
        """
        Test API endpoint
        """

        print("Test API endpoint accessed")
        return Response({"message": "This is a test endpoint."}, status=200)