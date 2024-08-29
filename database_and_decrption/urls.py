from django.urls import path
from . import views

urlpatterns = [
    path('decrypt_image/', views.decrypt_image, name='decrypt_image'),
    path('encrypted-images/', views.encrypted_image_list, name='encrypted_image_list'),
]
