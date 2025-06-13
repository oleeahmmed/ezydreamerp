
import pymysql
pymysql.install_as_MySQLdb()


import os
# from decouple import config, Csv 
from pathlib import Path
from django.utils.translation import gettext_lazy as _
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-i3c@wc-ieg!id-8e1$mxo9@0_c_t2*25&@u-nbgvxmdrx2&kio'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*','https://erp.yashglobalsdnbhd.com/']

# Load environment variables
# SECRET_KEY = config('SECRET_KEY')
# DEBUG = config('DEBUG', default=False, cast=bool)
# ALLOWED_HOSTS = config('ALLOWED_HOSTS', default="127.0.0.1,localhost", cast=Csv())



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    'django_filters',
    'adminpanel',

    # Custom apps
    'global_settings',
    "permission",
    'BusinessPartnerMasterData', 
    'Inventory',
    'Production',
    'Sales',  
    'Purchase',
    'Finance',
    'Hrm',
    'Banking',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',

]

CORS_ALLOW_ALL_ORIGINS = True  # Not recommended for production
# or for specific origins:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "https://yourfrontend.com",
# ]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
}


# JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

ROOT_URLCONF = 'config.urls'
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'permission.context_processors.permission_menu_context',
                'BusinessPartnerMasterData.context_processors.business_partner_menu_context',
                'Inventory.context_processors.inventory_menu_context',
                'Sales.context_processors.sales_menu_context',
                'Purchase.context_processors.purchase_menu_context',
                'Finance.context_processors.finance_menu_context',
                'Hrm.context_processors.hrm_menu_context',
                'Banking.context_processors.banking_menu_context',
                'global_settings.context_processors.global_settings_context',
                'Production.context_processors.production_menu_context',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'init_command': 'PRAGMA foreign_keys = ON;'
        }
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'kreakqap_erp_yashglobal',  # আপনার ডাটাবেসের নাম kreakqap_erp_yashglobal
#         'USER': 'kreakqap_erp_yashglobal',      # MySQL ইউজারনেম kreakqap_erp_yashglobal
#         'PASSWORD': 'SIBL$6Y{%3@V',  # MySQL পাসওয়া
#         'HOST': 'localhost',          # লোকালহোস্ট ব্যবহার করুন
#         'PORT': '3306',               # MySQL ডিফল্ট পোর্ট
#         'CONN_MAX_AGE': 300,  # <-- This is important!

#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'charset': 'utf8mb4',
#         },
#     }
# }
# DATABASE CONFIGURATION
# DATABASE_ENGINE = config('DATABASE_ENGINE', default='sqlite')

# if DATABASE_ENGINE == 'sqlite':
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         }
#     }
# elif DATABASE_ENGINE == 'mysql':
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': config('DB_NAME'),
#             'USER': config('DB_USER'),
#             'PASSWORD': config('DB_PASSWORD'),
#             'HOST': config('DB_HOST', default='localhost'),
#             'PORT': config('DB_PORT', default='3306'),
#         }
#     }
# elif DATABASE_ENGINE == 'postgresql':
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': config('DB_NAME'),
#             'USER': config('DB_USER'),
#             'PASSWORD': config('DB_PASSWORD'),
#             'HOST': config('DB_HOST', default='localhost'),
#             'PORT': config('DB_PORT', default='5432'),
#         }
#     }
# else:
#     raise ValueError("Invalid DATABASE_ENGINE in .env file!")
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'en'

USE_I18N = True
USE_L10N = True

LANGUAGES = (
    ('en', _('English')),
    ('bn', _('Bangla')),
)

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# STATIC & MEDIA FILES CONFIGURATION
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Production Static Configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
