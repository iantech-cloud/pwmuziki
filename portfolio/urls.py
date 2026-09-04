from django.urls import path
from . import views

urlpatterns = [
    path('', views.gallery, name='gallery'),
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
    path('manage/', views.portfolio_manage, name='portfolio_manage'),
    path('albums/new/', views.album_create, name='album_create'),
    path('albums/<int:album_id>/photos/new/', views.photo_upload, name='photo_upload'),
    path('albums/<int:pk>/toggle-public/', views.album_toggle_public, name='album_toggle_public'),
    path('bookings/<int:booking_id>/delivery/', views.delivery_manage, name='delivery_manage'),
    path('bookings/<int:booking_id>/delivery/link/', views.delivery_link, name='delivery_link'),
]