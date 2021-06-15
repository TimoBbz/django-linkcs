from django.urls import path
from django.contrib.auth.views import LogoutView

from linkcs import views

urlpatterns = [
    path('auth/', views.LinkCSRedirect.as_view(), name='oauth_redirect_uri'),
    path('login/', views.LinkCSLogin.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
