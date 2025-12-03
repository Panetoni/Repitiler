from django.urls import path, include #type: ignore
from .views import registerReptilerUser, loginReptilerUser,dashboard,home,logoutReptilerUser, video_progress,change_password,upload_video,update_name_public, password_reset_request, password_reset_confirm, redirect_with_token  # type: ignore

# API views
from .api_views import api_login, api_register, api_current_user, api_dashboard, api_upload_video ,api_delete_video, api_video_progresso, api_password_reset_request # type: ignore
from .api_views import api_change_password, api_update_name_public  # type: ignore
urlpatterns = [    
    path("register/", registerReptilerUser, name='register'),  # type: ignore
    path("login/", loginReptilerUser, name='login'),  # type: ignore
    path('dashboard/', dashboard, name='dashboard'), 
    path('', home, name='home'),  # type: ignore
    path('logout/', logoutReptilerUser, name='logout'),  # type
    path('video_progress/<int:video_id>/', video_progress, name='video_progress'),
    path('change_password/', change_password, name='change_password'),
    path('upload_video/', upload_video, name='upload_video'),
    path('update_name_public/', update_name_public, name='update_name_public'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('redirect-to-angular/', redirect_with_token, name='redirect_to_angular'),

    # API endpoints
    path('api/login/', api_login, name='api_login'),  # type: ignore
    path('api/register/', api_register, name='api_register'),  # type: ignore
    path('api/current_user/', api_current_user, name='api_current_user'),  # type: ignore
    path('api/dashboard/', api_dashboard, name='api_dashboard'),  # type: ignore
    path("api/upload-video/", api_upload_video, name="api-upload-video"),
    path("api/videos/<int:pk>/delete/", api_delete_video, name="api-delete-video"),
    path("api/videos/<int:pk>/progresso/", api_video_progresso, name="api-video-progresso"),
    path("api/password-reset-request/", api_password_reset_request, name="api-password-reset-request"),
    path("api/change-password/", api_change_password, name="api-change-password"),
    path("api/update-name-public/", api_update_name_public, name="api-update-name-public"),
]

