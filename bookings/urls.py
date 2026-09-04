from django.urls import path
from . import views
urlpatterns = [
    path('', views.booking_list, name='booking_list'),
    path('new/', views.booking_create, name='booking_create'),
    path('availability/', views.availability_manage, name='availability_manage'),
    path('availability/<int:pk>/toggle/', views.availability_toggle, name='availability_toggle'),
    path('<int:pk>/edit/', views.booking_update, name='booking_update'),
    path('<int:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('<int:pk>/status/', views.booking_status_update, name='booking_status_update'),
    path('<int:pk>/confirm-arrival/', views.booking_confirm_arrival, name='booking_confirm_arrival'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
]
