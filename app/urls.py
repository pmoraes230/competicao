from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('register_user/', views.register_user, name='register_user'),
    path('event/<int:id>/register_client/', views.register_client, name='register_client'),
    path('register_profile/', views.register_profile, name='register_profile'),
    path('register_events/', views.register_events, name='register_events'),
    path('list_setor/', views.list_setor, name='list_setor'),
    path('update_setor/<int:id>', views.update_setor, name='update_setor'),
    path('delete_setor/<int:id>', views.delete_setor, name='delete_setor'),
    path('register_setor/', views.register_setor, name='register_setor'),
    path('edit_event/<int:id>', views.edit_event, name='edit_event'),
    path('delete_event/<int:id>', views.delete_event, name='delete_event'),
    path('event_deteils/<int:event_id>', views.event_details, name='event_details'),
    path('event/<int:event_id>/buy/', views.buy_ticket, name='buy_ticket'),
    path('list_users/', views.list_user, name='list_users'),
    path('edit_user/<int:id>', views.edit_user, name='edit_user'),
    path('delete_user/<int:id>', views.delete_user, name='delete_user'),
    path('logout/', views.logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
