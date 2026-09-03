from django.urls import path
from . import views

urlpatterns = [
    path('booking/<int:booking_id>/new/', views.review_create, name='review_create'),
    path('<int:review_id>/respond/', views.review_respond, name='review_respond'),
]