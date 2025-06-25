from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('register_user', views.register_user, name='register_user'),
    path('register_client', views.register_client, name='registe_client'),
    path('logout/', views.logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
