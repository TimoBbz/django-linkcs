from django.urls import path
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView

from linkcs import views

urlpatterns = [
    path('auth/', views.LinkCSRedirect.as_view(), name='oauth_redirect_uri'),
    path('login/', views.LinkCSLogin.as_view(), name='login'),
    path('login/failed/', views.LoginFailedView.as_view(),
         name='login_failed'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
