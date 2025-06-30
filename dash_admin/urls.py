from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_dash, name='home_dash'),
    path('vendas/', views.dash_vendas, name='dash_vendas'),
    path('usuarios/', views.dash_usuarios, name='dash_usuarios'),
    path('eventos/', views.dash_eventos, name='dash_eventos'),
]
