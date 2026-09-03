from django.urls import path
from . import views

urlpatterns = [
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
]