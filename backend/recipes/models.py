from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (
    INGREDIENT_NAME_MAX_LENGTH,
    MAX_IMAGE_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_INGREDIENT_AMOUNT,
    MIN_RECIPE_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)


class User(AbstractUser):
    """Custom user model with email and avatar."""

    email = models.EmailField('email address', unique=True)
    avatar = models.ImageField(
        upload_to='users/',
        max_length=MAX_IMAGE_LENGTH,
        blank=True,
        null=True,
        verbose_name='Аватар пользователя',
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

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
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Слаг',
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
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='ingredient_unique_name_measurement_unit',
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Model for cooking recipes."""

    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название',
    )
    text = models.TextField(verbose_name='Текст')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[MinValueValidator(MIN_RECIPE_COOKING_TIME)],
    )
    image = models.ImageField(
        upload_to='recipes/',
        max_length=MAX_IMAGE_LENGTH,
        blank=False,
        null=False,
        verbose_name='Картинка, закодированная в Base64',
    )
    author = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='Список id тегов',
    )
    ingredients = models.ManyToManyField(
        'recipes.Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """Intermediate model linking recipes and tags."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    class Meta:
        verbose_name = 'Связь рецепта и тега'
        verbose_name_plural = 'Связи рецептов и тегов'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag_unique_pair',
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class RecipeIngredient(models.Model):
    """Intermediate model linking recipes and ingredients with amount."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)],
    )

    class Meta:
        verbose_name = 'Связь рецепта и ингредиента'
        verbose_name_plural = 'Связи рецептов и ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe_ingredient_unique_pair',
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class Subscription(models.Model):
    """Model representing a user subscription to an author."""

    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='subscribed',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='subscription_unique_pair',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='subscription_no_self_follow',
            ),
        ]


class Favorite(models.Model):
    """Model representing a user's favorite recipes."""

    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт в избранном',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='favorite_unique_pair',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Model representing recipes in a user's shopping cart."""

    user = models.ForeignKey(
        'recipes.User',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт в корзине',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='shopping_cart_unique_pair',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
