from django.urls import include, path
from rest_framework import routers

from users.views import UserViewSet
from recipes.views import RecipeViewSet, IngredientViewSet

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register('ingredients', IngredientViewSet, basename='ingredients')
app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
