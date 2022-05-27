from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from linkcs import views

urlpatterns = [
    path('auth/', views.LinkCSRedirect.as_view(), name='oauth_redirect_uri'),
    path('login/', views.UpdatedLoginView.as_view(), name='login'),
    path('login/linkcs/', views.LinkCSLogin.as_view(), name='login_linkcs'),
    path('login/failed/', RedirectView.as_view(url=reverse_lazy('login'))),
    path('password_change/', views.UpdatedPasswordChangeView.as_view(), name='password_change'),
    path('', include('django.contrib.auth.urls')),
]
