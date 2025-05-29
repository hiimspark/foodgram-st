from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import SAFE_METHODS
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from utils.pagination import FoodgramPagination
from utils.permissions import IsAuthorOrReadOnly
from utils.filters import RecipeFilterSet
from .models import (Recipe, Ingredient, ShoppingCart, Favorite,
                     ShortLink, RecipeIngredient, )
from .serializers import (RecipeListSerializer, RecipeWriteSerializer,
                          IngredientSerializer, RecipeForCartSerializer, )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilterSet
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeWriteSerializer

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = ShoppingCart.objects.filter(user=request.user,
                                                    recipe=recipe)
        if request.method == 'POST':
            if shopping_cart.exists():
                return Response(
                    'Нельзя добавить рецепт, уже добавленный в корзину!',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeForCartSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if request.method == 'DELETE':
            cart_item = shopping_cart.first()
            if not cart_item:
                return Response(
                    'Нельзя удалить несуществующий рецепт из корзины!',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(
                    user=request.user, recipe=recipe).exists():
                return Response(
                    'Нельзя добавить рецепт, уже добавленный в корзину!',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeForCartSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        if request.method == 'DELETE':
            fav_item = Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            ).first()
            if not fav_item:
                return Response(
                    'Нельзя удалить несуществующий рецепт из избранного!',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fav_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        if request.user.shopping_cart.exists():
            ingredients = RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values("ingredient__name", "ingredient__measurement_unit"
                     ).annotate(sum=Sum("amount"))

            ingredients_list = "\n".join(
                f"{ingredient['ingredient__name']} - {ingredient['sum']} "
                f"({ingredient['ingredient__measurement_unit']})"
                for ingredient in ingredients
            )
            filename = 'shopping_list.txt'
            response = HttpResponse(ingredients_list,
                                    content_type='text/plain')
            response['Content-Disposition'] = (f'attachment; '
                                               f'filename={filename}')
            return response

        return Response(
            'Список покупок пуст.',
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(['get'],
            detail=True,
            url_path='get-link',)
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        recipe_link, link_code = ShortLink.objects.get_or_create(
            recipe_to_link=recipe)
        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe_link.link_code}/')
        })


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class ShortLinkNavigate(views.APIView):
    permission_classes = [IsAuthorOrReadOnly]

    def get(self, request, link_code):
        short_link = get_object_or_404(ShortLink, link_code=link_code)
        recipe_id = short_link.recipe_to_link.id

        full_url = request.build_absolute_uri(
            f'/recipes/{recipe_id}/'
        )

        return redirect(full_url)
