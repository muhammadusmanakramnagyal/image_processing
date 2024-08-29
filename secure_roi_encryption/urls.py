"""
URL configuration for secure_roi_encryption project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.urls import path, include

from secure_roi_encryption import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('qrng.urls')),
    path('', include('encrpyt.urls')),
    path('', include('sbox.urls')),
    path('', include('database_and_decrption.urls')),  # Include URLs from the second app
    #index.html ka page ha uska bhi url route karliye ga menu ka page index.html ma


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)