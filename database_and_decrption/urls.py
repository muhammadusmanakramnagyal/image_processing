from django.urls import path
from . import views

urlpatterns = [
    path('decrypt_image/', views.decrypt_image, name='decrypt_image'),
    path('encrypted-images/', views.encrypted_image_list, name='encrypted_image_list'),
    path('', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]
