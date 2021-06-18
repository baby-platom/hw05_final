from django.conf.urls import handler404, handler500
from django.contrib import admin
from django.urls import include, path

handler404 = "posts.views.page_not_found"  # noqa
handler500 = "posts.views.server_error"   # noqa

urlpatterns = [
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("", include("posts.urls")),
    path("admin/", admin.site.urls),
    path('about/', include('about.urls', namespace='about')),
]
