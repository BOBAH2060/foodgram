import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.conf import settings

from recipes.models import (
    Recipe,
    Ingredient,
    Tag,
    ShoppingCart,
    Favorite,
    Subscription,
    User,
    RecipeIngredient
)
from .validators import (
    validate_username_format, validate_ingredients, validate_tags
)


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise serializers.ValidationError(
                        'Неверные учётные данные'
                    )
                if not user.is_active:
                    raise serializers.ValidationError(
                        'Аккаунт неактивен'
                    )
                self.user = user
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'Пользователь с таким email не найден'
                )
        else:
            raise serializers.ValidationError(
                'Необходимо указать email и пароль'
            )
        return attrs

    def to_representation(self, instance):
        token, created = Token.objects.get_or_create(user=self.user)
        return {'auth_token': token.key}


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Ингредиент с таким ID не существует'
            )
        return value


class IngredientReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed', 'avatar'
        ]


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        source='recipeingredient_set',
        required=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'author', 'text', 'cooking_time',
            'ingredients', 'tags', 'image', 'is_favorited',
            'is_in_shopping_cart'
        ]

    def validate(self, data):
        initial_ingredients = self.initial_data.get('ingredients')
        initial_tags = self.initial_data.get('tags')

        if initial_ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': 'Поле обязательно'}
            )
        if initial_tags is None:
            raise serializers.ValidationError(
                {'tags': 'Поле обязательно'}
            )

        validate_ingredients(initial_ingredients)
        validate_tags(initial_tags)

        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation['ingredients'] = IngredientReadSerializer(
            instance.recipeingredient_set.all(), many=True
        ).data
        if instance.image:
            representation['image'] = (
                f'{settings.MEDIA_DOMAIN}{instance.image.url}'
                if settings.MEDIA_DOMAIN else instance.image.url
            )
        else:
            representation['image'] = None
        return representation

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=instance,
                    ingredient_id=item['id'],
                    amount=item['amount']
                ) for item in ingredients_data
            ])

        return instance


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ['recipe']


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['recipe']


class CreateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[validate_username_format]
    )
    password = serializers.CharField(write_only=True, required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name'
        ]


class AdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class SubscriptionSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(
            queryset,
            many=True,
            context={'request': request}
        ).data
