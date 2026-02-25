from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

from .constants import (
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    MAX_IMAGE_LENGTH
)


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    avatar = models.ImageField(
        upload_to='users/',
        max_length=MAX_IMAGE_LENGTH,
        blank=True,
        null=True,
        verbose_name='Аватар пользователя'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    """Model for recipe tags (categories)."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Model for food ingredients."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Model for cooking recipes."""

    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[MinValueValidator(1)]
    )
    image = models.ImageField(
        upload_to='recipes/',
        max_length=MAX_IMAGE_LENGTH,
        blank=False,
        null=False,
        verbose_name='Картинка, закодированная в Base64'
    )
    author = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='Список id тегов'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Промежуточная модель для связи рецептов и тегов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Связь рецепта и тега'
        verbose_name_plural = 'Связи рецептов и тегов'
        unique_together = ('recipe', 'tag')

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Связь рецепта и ингредиента'
        verbose_name_plural = 'Связи рецептов и ингредиентов'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class Subscription(models.Model):
    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='subscribed',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')


class Favorite(models.Model):
    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт в избранном'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт в корзине'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
