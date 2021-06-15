from django.urls import include, path
from django.contrib.auth.views import LoginView

from linkcs import views

urlpatterns = [
    path('auth/', views.LinkCSRedirect.as_view(), name='oauth_redirect_uri'),
    path('login/', views.LoginChoiceView.as_view(), name='login'),
    path('login/credentials/', LoginView.as_view(), name='login_credentials'),
    path('login/linkcs/', views.LinkCSLogin.as_view(), name='login_linkcs'),
    path('password_change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('', include('django.contrib.auth.urls')),
]
