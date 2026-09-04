from django.urls import path
from . import views

urlpatterns = [
    path('booking/<int:booking_id>/start/', views.payment_start, name='payment_start'),
    path('booking/<int:booking_id>/reservation/', views.payment_reservation, name='payment_reservation'),
    path('booking/<int:booking_id>/balance/', views.payment_balance, name='payment_balance'),
    path('booking/<int:booking_id>/invoice/', views.invoice_detail, name='invoice_detail'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/b2c/result/', views.mpesa_b2c_result, name='mpesa_b2c_result'),
    path('mpesa/b2c/timeout/', views.mpesa_b2c_timeout, name='mpesa_b2c_timeout'),
]