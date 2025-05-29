from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError

from users.serializers import UserSerializer
from .models import Ingredient, Recipe, RecipeIngredient


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
    id = serializers.ReadOnlyField(source='ingredient.id',)
    name = serializers.ReadOnlyField(source='ingredient.name',)
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
        return (
            not user.is_anonymous
            and user.shopping_cart.filter(recipe__id=obj.id).exists()
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            not user.is_anonymous
            and user.favorite.filter(recipe__id=obj.id).exists()
        )


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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Количество должно '
                                              'быть больше нуля.')
        return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = NewIngredientSerializer(
        many=True,
        write_only=True,
    )
    image = Base64ImageField(required=True, allow_null=False)
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image', 'name',
            'text', 'cooking_time', 'author',
        )

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError(
                {'image': [
                    'Картинка обязательна.'
                ]
                },
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                {'ingredients': [
                    'Необходимо указать хотя бы один ингредиент.'
                ]
                },
            )

        ingredients = []
        for ingredient in value:
            if ingredient in ingredients:
                raise ValidationError(
                    {'ingredients': [
                        'Ингридиенты повторяются!'
                    ]
                    },
                )
            if int(ingredient['amount']) <= 0:
                raise ValidationError(
                    {'amount': [
                        'Количество должно быть больше 0!'
                    ]
                    },
                )

            ingredients.append(ingredient)
        self._validated_ingredients = ingredients
        return value

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data

    def add_ingredients(self, recipe):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in self._validated_ingredients
        ])

    def validate(self, data):
        if self.instance and 'ingredients' not in self.initial_data:
            raise serializers.ValidationError({
                'ingredients': ['Это поле обязательно.']
            })
        return data

    def create(self, validated_data):
        validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.add_ingredients(recipe)
        return recipe

    def update(self, instance, validated_data):
        validated_data.pop('ingredients', None)
        instance.ingredients.clear()
        self.add_ingredients(instance)
        return super().update(instance, validated_data)


class RecipeForCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image',)
        read_only_fields = fields
