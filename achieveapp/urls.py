"""achieveapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin, auth
import django.contrib.auth.urls
import django.contrib.auth.forms

urlpatterns = [
    url(r'^', include('achieve.urls', namespace='achieve')),
    url('^', include(auth.urls)),
    url(r'^admin/', include(admin.site.urls)),
]

# Overrides for auth forms
django.contrib.auth.forms.PasswordChangeForm.declared_fields['old_password'].widget.attrs['class'] = 'form-control'
django.contrib.auth.forms.SetPasswordForm.declared_fields['new_password1'].widget.attrs['class'] = 'form-control'
django.contrib.auth.forms.SetPasswordForm.declared_fields['new_password2'].widget.attrs['class'] = 'form-control'
django.contrib.auth.forms.PasswordResetForm.declared_fields['email'].widget.attrs['class'] = 'form-control'
