from rest_framework import serializers

from api.serializers import DecodeBase64ImageField
from users.serializers import UserSerializer
from .models import Ingredient, Recipe, RecipeIngredient
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        read_only_fields = fields


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )

    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )

    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer()

    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
    )

    is_in_shopping_cart = serializers.SerializerMethodField()

    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_in_shopping_cart',
            'is_favorited', 'name', 'image', 'text', 'cooking_time',
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and \
            user.shopping_cart.filter(recipe__id=obj.id).exists()

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and \
            user.favorite.filter(recipe__id=obj.id).exists()


class NewIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = NewIngredientSerializer(
        many=True,
        write_only=True,
    )

    image = DecodeBase64ImageField()

    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image', 'name',
            'text', 'cooking_time', 'author',
        )

    def validate_ingredients(self, value):
        if not value:
            serializers.ValidationError(
                {'ingredients': [
                    'Необходимо указать хотя бы один ингредиент.'
                ]
                },
            )

        ingredients = []
        for item in value:
            ingredient = get_object_or_404(Ingredient, name=item['id'])
            if ingredient in ingredients:
                raise ValidationError(
                    {'ingredients': [
                        'Ингридиенты повторяются!'
                    ]
                    },
                )
            if int(item['amount']) <= 0:
                raise ValidationError(
                    {'amount': [
                        'Количество должно быть больше 0!'
                    ]
                    },
                )

            ingredients.append(ingredient)
        return value

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data

    def add_ingredients(self, ingredients, model):
        for ingredient in ingredients:
            RecipeIngredient.objects.update_or_create(
                recipe=model,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        if ingredients is None or ingredients == []:
            raise serializers.ValidationError(
                {'ingredients': [
                    'Необходимо указать хотя бы один ингредиент!'
                ]
                },
            )
        recipe = super().create(validated_data)
        self.add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is None or ingredients == []:
            raise serializers.ValidationError(
                {'ingredients': [
                    'Необходимо указать хотя бы один ингредиент!'
                ]
                },
            )
        instance.ingredients.clear()
        self.add_ingredients(ingredients, instance)
        return super().update(instance, validated_data)


class RecipeForCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image',)
        read_only_fields = fields
