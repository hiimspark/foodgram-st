from django.contrib import admin
from django.urls import path, include

from recipes.views import ShortLinkNavigate

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("api.urls", namespace="api")),
    path('s/<str:code>/', ShortLinkNavigate.as_view()),

]
