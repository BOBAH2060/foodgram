from django.conf import settings

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
    User,
)
from .constants import MIN_INGREDIENT_AMOUNT, USER_NAME_MAX_LENGTH
from .validators import (
    validate_ingredients,
    validate_tags,
    validate_username_format,
    validate_image,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient model."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag model."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Serializer for writing recipe ingredients."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class IngredientReadSerializer(serializers.ModelSerializer):
    """Serializer for reading recipe ingredients."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Short serializer for recipe list representation."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile representation."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    def get_is_subscribed(self, author):
        """Return True if current user is subscribed to the author."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return author.subscribed.filter(user=request.user).exists()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Serializer for detailed recipe representation."""

    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'author',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'image',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def _check_user_relation(self, recipe, relation):
        """Return True if recipe is related to current user."""
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return getattr(recipe, relation).filter(
            user=request.user
        ).exists()

    def get_is_favorited(self, recipe):
        """Return True if recipe is favorited by current user."""
        return self._check_user_relation(recipe, 'favorited_by')

    def get_is_in_shopping_cart(self, recipe):
        """Return True if recipe is in current user's shopping cart."""
        return self._check_user_relation(recipe, 'in_shopping_cart')

    def get_image(self, recipe):
        """Return absolute or relative image URL."""
        if not recipe.image:
            return None
        if settings.MEDIA_DOMAIN:
            return f'{settings.MEDIA_DOMAIN}{recipe.image.url}'
        return recipe.image.url


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating recipes."""

    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        source='recipeingredient_set',
        required=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'image',
        )

    def validate(self, attrs):
        """Validate required fields and related objects."""
        for required_field in ('ingredients', 'tags', 'image'):
            if required_field not in self.initial_data:
                raise serializers.ValidationError(
                    {required_field: 'Поле обязательно'}
                )

        validate_ingredients(self.initial_data['ingredients'])
        validate_tags(self.initial_data['tags'])
        validate_image(self.initial_data['image'])
        return attrs

    def to_representation(self, instance):
        """Return read serializer representation."""
        return RecipeReadSerializer(instance, context=self.context).data

    def _set_recipe_relations(self, recipe, ingredients_data, tags_data):
        """Set tags and ingredients for a recipe."""
        recipe.tags.set(tags_data)

        recipe.recipeingredient_set.all().delete()

        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients_data
            ]
        )

    def create(self, validated_data):
        """Create recipe with related ingredients and tags."""
        ingredients_data = validated_data.pop('recipeingredient_set')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        self._set_recipe_relations(recipe, ingredients_data, tags_data)

        return recipe

    def update(self, instance, validated_data):
        """Update recipe with related ingredients and tags."""
        ingredients_data = validated_data.pop('recipeingredient_set')
        tags_data = validated_data.pop('tags')

        instance = super().update(instance, validated_data)
        self._set_recipe_relations(instance, ingredients_data, tags_data)

        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    first_name = serializers.CharField(
        required=True,
        max_length=USER_NAME_MAX_LENGTH
    )
    last_name = serializers.CharField(
        required=True,
        max_length=USER_NAME_MAX_LENGTH
    )
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        max_length=USER_NAME_MAX_LENGTH,
        validators=(validate_username_format,),
    )
    password = serializers.CharField(write_only=True, required=True)

    def validate_username(self, username):
        """Ensure username uniqueness."""
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует.'
            )
        return username

    def validate_email(self, email):
        """Ensure email uniqueness."""
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return email

    def create(self, validated_data):
        """Create new user instance."""
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name'
        )


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management."""

    class Meta:
        model = User
        fields = '__all__'


class SubscriptionSerializer(UserSerializer):
    """Serializer for user subscriptions with recipes list."""

    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = fields

    def get_recipes(self, author):
        """Return author's recipes with optional limit."""
        request = self.context.get('request')
        recipes_limit = (
            request.query_params.get('recipes_limit')
            if request else None
        )
        queryset = author.recipes.all()
        if recipes_limit:
            try:
                queryset = queryset[:int(recipes_limit)]
            except (TypeError, ValueError):
                pass
        return RecipeShortSerializer(
            queryset,
            many=True,
            context={'request': request},
        ).data
