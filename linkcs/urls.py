from django.urls import include, path

from . import views

urlpatterns = [
    path('auth/', views.LinkCSRedirect.as_view()),
    path('login/', views.LinkCSLogin.as_view(), name='linkcs_login'),
]