from django.urls import path
from .views import generate_quantum_sbox,show_sbox_page, IndexPageView

urlpatterns = [
    path('sbox/', show_sbox_page, name='show_sbox_page'),
    path('generate_quantum_sbox/', generate_quantum_sbox, name='generate_quantum_sbox'),
    path('index_page/', IndexPageView.as_view(), name='index_page'),
]
