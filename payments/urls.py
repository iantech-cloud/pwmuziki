from django.urls import path
from . import views

urlpatterns = [
    path('booking/<int:booking_id>/start/', views.payment_start, name='payment_start'),
]