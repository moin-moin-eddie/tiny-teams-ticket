from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include  # add this

urlpatterns = [
    path('admin/', admin.site.urls),          # Django admin route
    path('hijack/', include('hijack.urls', namespace='hijack')),
    path("", include("authentication.urls")), # Auth routes - login / register
    path("", include("ticket.urls")),          # UI Kits Html files
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
