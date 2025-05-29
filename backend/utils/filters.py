from django_filters.rest_framework import (FilterSet, filters,)

from recipes.models import Recipe


class RecipeFilterSet(FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
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
