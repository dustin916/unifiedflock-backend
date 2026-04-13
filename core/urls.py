from django.urls import path
from . import views, views_api
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Main Pages
    path('', views.user_dashboard, name='user_dashboard'),
    path('church-dashboard/', views.church_dashboard, name='church_dashboard'),
    path('create-church/', views.create_church, name='create_church'),
    path('request-join/', views.request_join, name='request_join'),

    #Church urls
    #Church Announcements
    path('announcements/', views.announcements_page, name='announcements_page'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/edit/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('announcements/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),

    #Church Events
    path('events/', views.events_page, name='events_page'),
    path('add-event/', views.add_event, name='add_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),

    #Church Memberships
    path('members/', views.members_page, name='members'),
    path('manage-requests/', views.manage_join_requests, name='manage_requests'),
    path('handle-request/<int:request_id>/<str:action>/', views.handle_join_request, name='handle_request'),
    path('promote/<int:membership_id>/', views.promote_member, name='promote_member'),
    path('demote/<int:membership_id>/', views.demote_member, name='demote_member'),
    path('remove/<int:membership_id>/', views.remove_member, name='remove_member'),

    #Prayer
    path('prayers/', views.prayer_page, name='prayer_requests'),
    path('prayers/create/', views.create_prayer_request, name='create_prayer'),
    path('prayers/manage/', views.manage_prayers, name='manage_prayers'),
    path('prayers/handle/<int:prayer_id>/<str:action>/', views.handle_prayer_request, name='handle_prayer'),
    path('prayers/edit/<int:prayer_id>/', views.edit_prayer, name='edit_prayer'),
    path('prayers/delete/<int:prayer_id>/', views.delete_prayer, name='delete_prayer'),
    path('prayers/answered/<int:prayer_id>/', views.mark_prayer_answered, name='mark_prayer_answered'),

    # Chat
    path('chat/', views.chat_redirect, name='chat_redirect'),
    path('chat/<int:church_id>/', views.chat_page, name='chat'),
    path('chat/<int:church_id>/load-more/', views.load_more_messages, name='load_more_messages'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-done/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # API
    path('api/login/', views_api.CustomAuthToken.as_view(), name='api_login'),
    path('api/church/<int:church_id>/dashboard/', views_api.church_dashboard_api, name='api_church_dashboard'),
    path('api/church/<int:church_id>/announcements/', views_api.announcements_api, name='api_announcements'),

]

