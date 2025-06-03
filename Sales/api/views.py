# This file shows how to properly tag your views for the hierarchical documentation

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from django.db.models import Sum
from rest_framework.views import APIView
from datetime import timedelta

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import (
    SalesEmployee,
    SalesQuotation, SalesQuotationLine,
    SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine,
    Return, ReturnLine,
    ARInvoice, ARInvoiceLine
)
from .serializers import (
    SalesEmployeeSerializer,
    SalesQuotationListSerializer, SalesQuotationDetailSerializer, SalesQuotationCreateUpdateSerializer, SalesQuotationLineSerializer,
    SalesOrderListSerializer, SalesOrderDetailSerializer, SalesOrderCreateUpdateSerializer, SalesOrderLineSerializer,
    DeliveryListSerializer, DeliveryDetailSerializer, DeliveryCreateUpdateSerializer, DeliveryLineSerializer,
    ReturnListSerializer, ReturnDetailSerializer, ReturnCreateUpdateSerializer, ReturnLineSerializer,
    ARInvoiceListSerializer, ARInvoiceDetailSerializer, ARInvoiceCreateUpdateSerializer, ARInvoiceLineSerializer
)
from .permissions import SalesHasDynamicModelPermission

# Add tags to each ViewSet to ensure proper categorization in the documentation

class SalesEmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Sales Employees.
    
    A sales employee is linked to a user account and represents a salesperson in the system.
    Sales employees are assigned to sales documents and can only view their own documents
    unless they have superuser privileges.
    """
    queryset = SalesEmployee.objects.all()
    serializer_class = SalesEmployeeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'department']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'department']
    ordering = ['name']
    swagger_tags = ['Sales Employees']  # Add this line for tag categorization

    @swagger_auto_schema(
        operation_summary="List all sales employees",
        operation_description="Returns a list of all sales employees the user has access to view.",
        tags=['Sales Employees']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new sales employee",
        operation_description="Creates a new sales employee with the provided data.",
        tags=['Sales Employees']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific sales employee",
        operation_description="Returns the details of a specific sales employee.",
        tags=['Sales Employees']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a sales employee",
        operation_description="Updates the specified sales employee with the provided data.",
        tags=['Sales Employees']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a sales employee",
        operation_description="Partially updates the specified sales employee with the provided data.",
        tags=['Sales Employees']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a sales employee",
        operation_description="Deletes the specified sales employee.",
        tags=['Sales Employees']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class SalesQuotationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Sales Quotations.
    
    A sales quotation is a document sent to potential customers with pricing information
    for products or services. Quotations can be converted to sales orders when accepted.
    
    Sales employees can only view their own quotations unless they have superuser privileges.
    """
    queryset = SalesQuotation.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'status', 'customer', 'sales_employee']
    search_fields = ['customer__name', 'remarks']
    ordering_fields = ['document_date', 'valid_until', 'customer__name']
    ordering = ['-document_date']
    swagger_tags = ['Sales Quotations']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return SalesQuotationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SalesQuotationCreateUpdateSerializer
        return SalesQuotationDetailSerializer

    def get_queryset(self):
        queryset = SalesQuotation.objects.select_related(
            'customer', 
            'contact_person',
            'billing_address',
            'shipping_address',
            'currency',
            'payment_terms',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Filter by sales employee if user is not superuser
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all sales quotations",
        operation_description="Returns a list of all sales quotations the user has access to view.",
        tags=['Sales Quotations']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new sales quotation",
        operation_description="Creates a new sales quotation with the provided data, including line items.",
        tags=['Sales Quotations']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific sales quotation",
        operation_description="Returns the details of a specific sales quotation, including line items.",
        tags=['Sales Quotations']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a sales quotation",
        operation_description="Updates the specified sales quotation with the provided data, including line items.",
        tags=['Sales Quotations']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a sales quotation",
        operation_description="Partially updates the specified sales quotation with the provided data.",
        tags=['Sales Quotations']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a sales quotation",
        operation_description="Deletes the specified sales quotation and all its line items.",
        tags=['Sales Quotations']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get quotation line items",
        operation_description="Returns all line items for a specific sales quotation.",
        tags=['Sales Quotations']
    )
    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """
        Retrieve lines for a specific sales quotation
        """
        quotation = self.get_object()
        lines = quotation.lines.all()
        serializer = SalesQuotationLineSerializer(lines, many=True)
        return Response(serializer.data)

class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Sales Orders.
    
    A sales order is a confirmed order from a customer. Sales orders can be created
    directly or converted from sales quotations. They can be further processed into
    deliveries and invoices.
    
    Sales employees can only view their own orders unless they have superuser privileges.
    """
    queryset = SalesOrder.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'status', 'customer', 'sales_employee']
    search_fields = ['customer__name', 'remarks']
    ordering_fields = ['document_date', 'delivery_date', 'customer__name']
    ordering = ['-document_date']
    swagger_tags = ['Sales Orders']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return SalesOrderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SalesOrderCreateUpdateSerializer
        return SalesOrderDetailSerializer

    def get_queryset(self):
        queryset = SalesOrder.objects.select_related(
            'customer', 
            'contact_person',
            'billing_address',
            'shipping_address',
            'currency',
            'payment_terms',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Filter by sales employee if user is not superuser
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all sales orders",
        operation_description="Returns a list of all sales orders the user has access to view.",
        tags=['Sales Orders']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new sales order",
        operation_description="Creates a new sales order with the provided data, including line items.",
        tags=['Sales Orders']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific sales order",
        operation_description="Returns the details of a specific sales order, including line items.",
        tags=['Sales Orders']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a sales order",
        operation_description="Updates the specified sales order with the provided data, including line items.",
        tags=['Sales Orders']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a sales order",
        operation_description="Partially updates the specified sales order with the provided data.",
        tags=['Sales Orders']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a sales order",
        operation_description="Deletes the specified sales order and all its line items.",
        tags=['Sales Orders']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get order line items",
        operation_description="Returns all line items for a specific sales order.",
        tags=['Sales Orders']
    )
    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """
        Retrieve lines for a specific sales order
        """
        order = self.get_object()
        lines = order.lines.all()
        serializer = SalesOrderLineSerializer(lines, many=True)
        return Response(serializer.data)

class DeliveryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Deliveries.
    
    A delivery document represents the physical shipment of goods to a customer.
    Deliveries are typically created from sales orders and can be further processed
    into invoices or returns.
    
    Sales employees can only view their own deliveries unless they have superuser privileges.
    """
    queryset = Delivery.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'status', 'customer', 'sales_employee', 'sales_order']
    search_fields = ['customer__name', 'remarks', 'deliveryemployee']
    ordering_fields = ['document_date', 'posting_date', 'customer__name']
    ordering = ['-document_date']
    swagger_tags = ['Deliveries']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return DeliveryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DeliveryCreateUpdateSerializer
        return DeliveryDetailSerializer

    def get_queryset(self):
        queryset = Delivery.objects.select_related(
            'customer', 
            'contact_person',
            'shipping_address',
            'sales_order',
            'currency',
            'payment_terms',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Filter by sales employee if user is not superuser
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all deliveries",
        operation_description="Returns a list of all deliveries the user has access to view.",
        tags=['Deliveries']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new delivery",
        operation_description="Creates a new delivery with the provided data, including line items.",
        tags=['Deliveries']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific delivery",
        operation_description="Returns the details of a specific delivery, including line items.",
        tags=['Deliveries']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a delivery",
        operation_description="Updates the specified delivery with the provided data, including line items.",
        tags=['Deliveries']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a delivery",
        operation_description="Partially updates the specified delivery with the provided data.",
        tags=['Deliveries']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a delivery",
        operation_description="Deletes the specified delivery and all its line items.",
        tags=['Deliveries']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get delivery line items",
        operation_description="Returns all line items for a specific delivery.",
        tags=['Deliveries']
    )
    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """
        Retrieve lines for a specific delivery
        """
        delivery = self.get_object()
        lines = delivery.lines.all()
        serializer = DeliveryLineSerializer(lines, many=True)
        return Response(serializer.data)

class ReturnViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Returns.
    
    A return document represents goods returned by a customer. Returns are typically
    created from deliveries and may result in credit notes or refunds.
    
    Sales employees can only view their own returns unless they have superuser privileges.
    """
    queryset = Return.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'status', 'customer', 'sales_employee', 'delivery']
    search_fields = ['customer__name', 'remarks', 'return_reason']
    ordering_fields = ['document_date', 'posting_date', 'customer__name']
    ordering = ['-document_date']
    swagger_tags = ['Returns']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return ReturnListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ReturnCreateUpdateSerializer
        return ReturnDetailSerializer

    def get_queryset(self):
        queryset = Return.objects.select_related(
            'customer', 
            'contact_person',
            'return_address',
            'delivery',
            'currency',
            'payment_terms',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Filter by sales employee if user is not superuser
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all returns",
        operation_description="Returns a list of all return documents the user has access to view.",
        tags=['Returns']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new return",
        operation_description="Creates a new return document with the provided data, including line items.",
        tags=['Returns']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific return",
        operation_description="Returns the details of a specific return document, including line items.",
        tags=['Returns']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a return",
        operation_description="Updates the specified return document with the provided data, including line items.",
        tags=['Returns']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update a return",
        operation_description="Partially updates the specified return document with the provided data.",
        tags=['Returns']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a return",
        operation_description="Deletes the specified return document and all its line items.",
        tags=['Returns']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get return line items",
        operation_description="Returns all line items for a specific return document.",
        tags=['Returns']
    )
    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """
        Retrieve lines for a specific return
        """
        return_doc = self.get_object()
        lines = return_doc.lines.all()
        serializer = ReturnLineSerializer(lines, many=True)
        return Response(serializer.data)

class ARInvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing AR Invoices (Accounts Receivable Invoices).
    
    An AR invoice is a billing document sent to customers. Invoices can be created
    directly or from sales orders or deliveries. They represent amounts owed by customers.
    
    Sales employees can only view their own invoices unless they have superuser privileges.
    """
    queryset = ARInvoice.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, SalesHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'status', 'customer', 'sales_employee', 'sales_order', 'delivery']
    search_fields = ['customer__name', 'remarks']
    ordering_fields = ['document_date', 'posting_date', 'due_date', 'customer__name']
    ordering = ['-document_date']
    swagger_tags = ['AR Invoices']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return ARInvoiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ARInvoiceCreateUpdateSerializer
        return ARInvoiceDetailSerializer

    def get_queryset(self):
        queryset = ARInvoice.objects.select_related(
            'customer', 
            'contact_person',
            'billing_address',
            'sales_order',
            'delivery',
            'currency',
            'payment_terms',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Filter by sales employee if user is not superuser
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all AR invoices",
        operation_description="Returns a list of all AR invoices the user has access to view.",
        tags=['AR Invoices']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new AR invoice",
        operation_description="Creates a new AR invoice with the provided data, including line items.",
        tags=['AR Invoices']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific AR invoice",
        operation_description="Returns the details of a specific AR invoice, including line items.",
        tags=['AR Invoices']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an AR invoice",
        operation_description="Updates the specified AR invoice with the provided data, including line items.",
        tags=['AR Invoices']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update an AR invoice",
        operation_description="Partially updates the specified AR invoice with the provided data.",
        tags=['AR Invoices']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an AR invoice",
        operation_description="Deletes the specified AR invoice and all its line items.",
        tags=['AR Invoices']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get invoice line items",
        operation_description="Returns all line items for a specific AR invoice.",
        tags=['AR Invoices']
    )
    @action(detail=True, methods=['get'])
    def lines(self, request, pk=None):
        """
        Retrieve lines for a specific AR invoice
        """
        invoice = self.get_object()
        lines = invoice.lines.all()
        serializer = ARInvoiceLineSerializer(lines, many=True)
        return Response(serializer.data)
    

from rest_framework import status
class SalesOrderStatusViewSet(viewsets.ViewSet):
    """
    ViewSet for retrieving Sales Order status choices.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    

    
    

    def list(self, request):
        """
        Returns the available status options for Sales Orders in the system
        """
        status_choices = dict(SalesOrder.STATUS_CHOICES)
        return Response({'status_choices': status_choices}, status=status.HTTP_200_OK)
    
# Create a specific permission class for this view
class CreateDeliveryPermission(BasePermission):
    """
    Custom permission to check if user has 'Sales.add_delivery' permission.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('Sales.add_delivery')    
from .serializers import SalesOrderToDeliverySerializer
from rest_framework.views import APIView
class SalesOrderToDeliveryAPIView(APIView):
    """
    API endpoint for converting a sales order to a delivery.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CreateDeliveryPermission]
    
    @swagger_auto_schema(
        request_body=SalesOrderToDeliverySerializer,
        responses={
            201: DeliveryDetailSerializer,
            400: "Bad Request",
            404: "Not Found"
        },
        operation_summary="Convert sales order to delivery",
        operation_description="Creates a new delivery based on the specified sales order.",
        tags=['Sales Orders']
    )
    def post(self, request, format=None):
        """
        Convert a sales order to a delivery.
        """
        serializer = SalesOrderToDeliverySerializer(data=request.data)
        if serializer.is_valid():
            delivery = serializer.save()
            response_serializer = DeliveryDetailSerializer(delivery)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    


from .serializers import DeliveryToReturnSerializer, DeliveryToARInvoiceSerializer

# Create specific permission classes for these views
class CreateReturnPermission(BasePermission):
    """
    Custom permission to check if user has 'Sales.add_return' permission.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('Sales.add_return')

class CreateARInvoicePermission(BasePermission):
    """
    Custom permission to check if user has 'Sales.add_arinvoice' permission.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('Sales.add_arinvoice')

class DeliveryToReturnAPIView(APIView):
    """
    API endpoint for converting a delivery to a return.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CreateReturnPermission]
    
    @swagger_auto_schema(
        request_body=DeliveryToReturnSerializer,
        responses={
            201: ReturnDetailSerializer,
            400: "Bad Request",
            404: "Not Found"
        },
        operation_summary="Convert delivery to return",
        operation_description="Creates a new return based on the specified delivery.",
        tags=['Deliveries']
    )
    def post(self, request, format=None):
        """
        Convert a delivery to a return.
        """
        serializer = DeliveryToReturnSerializer(data=request.data)
        if serializer.is_valid():
            return_doc = serializer.save()
            response_serializer = ReturnDetailSerializer(return_doc)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryToARInvoiceAPIView(APIView):
    """
    API endpoint for converting a delivery to an AR Invoice.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CreateARInvoicePermission]
    
    @swagger_auto_schema(
        request_body=DeliveryToARInvoiceSerializer,
        responses={
            201: ARInvoiceDetailSerializer,
            400: "Bad Request",
            404: "Not Found"
        },
        operation_summary="Convert delivery to AR Invoice",
        operation_description="Creates a new AR Invoice based on the specified delivery.",
        tags=['Deliveries']
    )
    def post(self, request, format=None):
        """
        Convert a delivery to an AR Invoice.
        """
        serializer = DeliveryToARInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            response_serializer = ARInvoiceDetailSerializer(invoice)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
class SalesEmployeeSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get sales summary grouped by sales employee for today, this month, and last 30 days. Also includes current user's sales if they are a sales employee.",
        responses={
            200: openapi.Response(
                description="Sales Summary",
                examples={
                    "application/json": {
                        "today_sales": [
                            {"sales_employee__name": "Alice", "total_sales": 12000.0}
                        ],
                        "month_sales": [],
                        "last_30_days_sales": [],
                        "user_sales_today": {"total_sales": 1200.0},
                        "user_sales_month": {"total_sales": 3500.0}
                    }
                }
            )
        },
        tags=["Sales Employee Report"]
    )
    def get(self, request, *args, **kwargs):
        today = now().date()
        start_of_month = today.replace(day=1)
        last_30_days = today - timedelta(days=30)

        base_queryset = SalesOrder.objects.filter(is_active=True)

        today_sales = base_queryset.filter(document_date=today) \
            .values('sales_employee__name') \
            .annotate(total_sales=Sum('payable_amount')) \
            .order_by('-total_sales')

        month_sales = base_queryset.filter(document_date__gte=start_of_month) \
            .values('sales_employee__name') \
            .annotate(total_sales=Sum('payable_amount')) \
            .order_by('-total_sales')

        last_30_sales = base_queryset.filter(document_date__gte=last_30_days) \
            .values('sales_employee__name') \
            .annotate(total_sales=Sum('payable_amount')) \
            .order_by('-total_sales')

        user_sales_today = user_sales_month = None
        if hasattr(request.user, 'sales_employee'):
            se = request.user.sales_employee
            user_sales_today = base_queryset.filter(
                document_date=today, sales_employee=se
            ).aggregate(total_sales=Sum('payable_amount'))

            user_sales_month = base_queryset.filter(
                document_date__gte=start_of_month, sales_employee=se
            ).aggregate(total_sales=Sum('payable_amount'))

        return Response({
            "today_sales": list(today_sales),
            "month_sales": list(month_sales),
            "last_30_days_sales": list(last_30_sales),
            "user_sales_today": user_sales_today,
            "user_sales_month": user_sales_month
        })
        