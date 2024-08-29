# urls.py
from django.urls import path
from .views import process_image,image_encryption_form  # Adjust the import according to your views location

urlpatterns = [
    path('image-encryption/', image_encryption_form, name='image_encryption_form'),

    path('process-image/', process_image, name='process_image'),
]