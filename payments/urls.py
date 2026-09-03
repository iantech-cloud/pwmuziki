from django.urls import path
from . import views

urlpatterns = [
    path('booking/<int:booking_id>/start/', views.payment_start, name='payment_start'),
    path('booking/<int:booking_id>/invoice/', views.invoice_detail, name='invoice_detail'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]