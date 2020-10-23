from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:game_slug>/', views.game, name='game'),
    path('<slug:game_slug>/stream/', views.stream, name='stream')
]