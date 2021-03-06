"""
Django settings for chatbot project.

Generated by 'django-admin startproject' using Django 1.10.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qwccqsiudkz+g9(&56ddk--hgp4)o5%9^=40makexhav$8*4h!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chatbot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chatbot',
        'USER': 'chatbot',
        'PASSWORD': 'chatbot',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'


# FACEBOOK SETTINGS
FB_ACCESS_TOKEN = 'EAAMuTCnOmSIBAM2syZCoK0MEq3hhvtAvr7QQKZCZBNbZCJZB17bqxGeIysK0zkE1IedsgRx5AZCO2tCFRzgZAvPvJtzCLnl8bQu9W4JQZAo3kqrYJZC9oT2vt63ihzbUNtZBHhRPn2lciZCU2gspPtTDkYdnnH8P5OI8Gu8bzHiZCgejgQZDZD'
# FB_ACCESS_TOKEN = 'EAABb5LddmFgBAIpxlOXwfqwWPN4b1IlZCDmsSfgaq2dC8TRTuWw33jtXRsCS7FZBGvZBpP28PerTZBk51p5Cw1hX0TblakqrEHuPXTlIGeIp4Yr0mnv4JOTZAN471bhnA9Ubr7toNjabVfW4wjZCFSHgkJialU1Iy3PjxxmPgk4gZDZD'
FB_APP_SECRET = '93B82DU57LE2BGLSBJQCREQW9AAWE24VRZMB8GFW9VMXPSUZZ8QNJQ9ZUTPQKZJK'

CSRF_COOKIE_SECURE = False