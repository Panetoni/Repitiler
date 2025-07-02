from django.urls import path, include #type: ignore
from .views import registerReptilerUser, loginReptilerUser,dashboard,home,logoutReptilerUser # type: ignore

urlpatterns = [    
    path("register/", registerReptilerUser, name='register'),  # type: ignore
    path("login/", loginReptilerUser, name='login'),  # type: ignore
    path('dashboard/', dashboard, name='dashboard'), 
    path('', home, name='home'),  # type: ignore
    path('logout/', logoutReptilerUser, name='logout'),  # type
    
]