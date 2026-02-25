from django.contrib import admin
from django.urls import path, include
from api.services.short_links import redirect_short_link


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:short_code>/',
        redirect_short_link,
        name='short-link-redirect'
    ),
]
