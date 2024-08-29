from django.urls import path
from .views import show_qrng_page, generate_quantum_key

urlpatterns = [
    path('qrng/', show_qrng_page, name='show_qrng_page'),
    path('generate-quantum-key/', generate_quantum_key, name='generate_quantum_key'),
]
