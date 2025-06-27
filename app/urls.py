from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('register_user/', views.register_user, name='register_user'),
    path('event/<int:id>/register/', views.register_client, name='register_client'),
    path('register_profile/', views.register_profile, name='register_profile'),
    path('register_events/', views.register_events, name='register_events'),
    path('register_setor/', views.register_setor, name='register_setor'),
    path('edit_event/<int:id>', views.edit_event, name='edit_event'),
    path('delete_event/<int:id>', views.delete_event, name='delete_event'),
    path('event_deteils/<int:id>', views.event_details, name='event_details'),
    path('buy_ticket/<int:event_id>/', views.buy_ticket, name='buy_ticket'),
    path('logout/', views.logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
