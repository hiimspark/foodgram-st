import string
import random

from django.db import models
from django.core.validators import MinValueValidator

from users.models import User
from utils.constants import (INGREDIENT_MAX_LEN, MEASUREMENT_UNIT_MAX_LEN,
                             RECIPE_MAX_LEN, RECIPE_COOKING_TIME_VALIDATOR,
                             RECIPEINGREDIENT_AMOUNT_VALIDATOR,
                             SHORTLINK_CODE_LEN, RECIPE_COOKING_TIME_LEN,
                             RECIPEINGREDIENT_AMOUNT_LEN, )


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_MAX_LEN,
        help_text='Введите название.',
        db_index=True,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LEN,
        help_text='Введите единицу измерения (например, кг., шт. и т.д.)',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredients'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=RECIPE_MAX_LEN,
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(RECIPE_COOKING_TIME_LEN,
                              RECIPE_COOKING_TIME_VALIDATOR)
        ],
    )
    image = models.ImageField(
        'Картинка, закодированная в Base64',
        upload_to='recipes/',
        null=False,
        blank=False,
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipes'
            )
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество (вес, и т.д.)',
        validators=[
            MinValueValidator(RECIPEINGREDIENT_AMOUNT_LEN,
                              RECIPEINGREDIENT_AMOUNT_VALIDATOR)
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipeingredient_relation'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class UserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_user_recipe_%(class)s"
            )
        ]
        ordering = ("-user",)

    def __str__(self):
        return f"{self.user} {self.recipe}"


class ShoppingCart(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = "shopping_cart"


class Favorite(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = "Рецепт в избранном"
        verbose_name_plural = "Рецепты в избранном"
        default_related_name = "favorite"


class ShortLink(models.Model):
    recipe_to_link = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
    )
    link_code = models.CharField(
        max_length=SHORTLINK_CODE_LEN,
        unique=True
    )

    class Meta:
        verbose_name = 'Сокращенная ссылка'

    def save(self, *args, **kwargs):
        if not self.link_code:
            self.link_code = ''.join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)
