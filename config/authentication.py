from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Define request and response schemas for better documentation
login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'password'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
    }
)

token_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
    }
)

refresh_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['refresh'],
    properties={
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
    }
)

refresh_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='New JWT access token'),
    }
)

verify_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['token'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT token to verify'),
    }
)

# Custom views with better documentation
class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        operation_summary="Login to obtain JWT token",
        operation_description="Provide username and password to obtain JWT access and refresh tokens",
        request_body=login_request_schema,
        responses={
            200: token_response_schema,
            400: 'Invalid credentials',
            401: 'Unauthorized'
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_summary="Refresh JWT token",
        operation_description="Provide a valid refresh token to obtain a new access token",
        request_body=refresh_request_schema,
        responses={
            200: refresh_response_schema,
            400: 'Invalid token',
            401: 'Unauthorized'
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class CustomTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        operation_summary="Verify JWT token",
        operation_description="Verify that a JWT token is valid",
        request_body=verify_request_schema,
        responses={
            200: 'Token is valid',
            400: 'Invalid token',
            401: 'Unauthorized'
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
