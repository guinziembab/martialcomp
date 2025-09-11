from django.urls import path
from apps.competitions.views.auth import signup_view, profile_view, password_change_view, login_view, logout_view
from apps.competitions.views.debug_csrf_login import debug_login_view, test_login_no_csrf

app_name = 'auth'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
    path('password_change/', password_change_view, name='password_change'),
    path('debug-login/', debug_login_view, name='debug_login'),
    path('test-login-no-csrf/', test_login_no_csrf, name='test_login_no_csrf'),
]
