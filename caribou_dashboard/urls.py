from django.urls import path, include
from django.views.generic.base import RedirectView
from checklist.admin import caribou_admin_site
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', include([
        path('', caribou_admin_site.urls),
        path('django-admin/', admin.site.urls),
    ])),
    path('checklist/', include(('checklist.urls', 'checklist'), namespace='checklist')),
    path('users/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', RedirectView.as_view(url='/admin/dashboard/', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)