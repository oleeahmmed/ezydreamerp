from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema

from Sales.models import SalesEmployee
from .serializers import UserLoginSerializer, UserPermissionSerializer, PermissionSerializer

class LoginAPIView(APIView):
    """
    API endpoint for user login.
    Handles authentication, token generation, and permission retrieval.
    - Superusers receive all permissions.
    - Non-superusers without a SalesEmployee account have specific
      sales add/edit permissions removed from their assigned set.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserLoginSerializer)
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        # Attempt to authenticate the user
        user = authenticate(request=request, username=username, password=password)

        if user is None:
            return Response({
                'status': 'error',
                'message': 'Invalid username or password.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        sales_employee_id = None
        has_sales_employee_account = False
        try:
            sales_employee_instance = user.sales_employee
            sales_employee_id = sales_employee_instance.id
            has_sales_employee_account = True
        except SalesEmployee.DoesNotExist:
            has_sales_employee_account = False
        except AttributeError:
            has_sales_employee_account = False

        permissions_data = []
        if user.is_superuser:
            all_db_permissions = Permission.objects.all().order_by('content_type__app_label', 'codename')
            permissions_data = PermissionSerializer(all_db_permissions, many=True).data
        else:
            permissions_data = UserPermissionSerializer(user).data.get('permissions', [])


            if not has_sales_employee_account:

                restricted_sales_codenames = {
                    'add_salesorder',
                    'change_salesorder',
                    # Add other specific add/edit codenames if needed, e.g.:
                    # 'add_salesquotation',
                    # 'change_salesquotation',
                    # 'add_delivery',
                    # 'change_delivery',
                    # 'add_return',
                    # 'change_return',
                    # 'add_arinvoice',
                    # 'change_arinvoice',
                }

                permissions_data = [
                    p for p in permissions_data
                    if p.get('codename') not in restricted_sales_codenames
                ]

        response_data = {
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'sales_employee_id': sales_employee_id,
            },
            'permissions': permissions_data, 
            'token': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)