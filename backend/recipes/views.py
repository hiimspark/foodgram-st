from rest_framework import viewsets, status, views
from django.shortcuts import get_object_or_404, redirect
from api.permissions import IsAuthorOrReadOnly
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import User
from .models import (Recipe, Ingredient, ShoppingCart, Favorite,
                     ShortLink, RecipeIngredient, )
from .serializers import (RecipeListSerializer, RecipeWriteSerializer,
                          IngredientSerializer, RecipeForCartSerializer, )
from rest_framework.permissions import SAFE_METHODS
from api.pagination import FoodgramPagination
from django_filters.rest_framework import (FilterSet,
                                           filters, DjangoFilterBackend, )


class RecipeFilterSet(FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    author = filters.ModelChoiceFilter(
        queryset=User.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'is_in_shopping_cart',
            'is_favorited',
        )

    def filter_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(favorite__user_id=self.request.user.id)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(shopping_cart__user_id=self.request.user.id)


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

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    user=request.user, recipe=recipe).exists():
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
            cart_item = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).first()
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
        user = User.objects.get(id=self.request.user.id)
        if user.shopping_cart.exists():
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
            response['Content-Disposition'] = f'attachment; \
                                                filename={filename}'
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

        return redirect(
            f'http://localhost/recipes/{short_link.recipe_to_link.id}/'
        )
