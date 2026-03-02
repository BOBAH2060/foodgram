from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

from .filters import IngredientFilter, RecipeFilter
from .mixins import AddRemoveMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AdminUserSerializer,
    CreateUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)
from .services.short_links import RecipeShortLinkService


class RecipeViewSet(AddRemoveMixin, viewsets.ModelViewSet):
    """Manage recipes with favorites, shopping cart, and short links."""

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients'
    ).order_by('-id')
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Return appropriate serializer depending on action."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        """Save a new recipe with current user as author."""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        """Return short link URL for a recipe."""
        short_code = RecipeShortLinkService.make_code(self.get_object().id)
        short_path = reverse(
            'short-link-redirect', kwargs={'short_code': short_code}
        )
        short_url = request.build_absolute_uri(short_path)
        return Response({'short-link': short_url})

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Add or remove recipe from user's favorites."""
        self.model = Favorite
        self.serializer_class = RecipeShortSerializer
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            return self.add(request.user, recipe)
        return self.remove(request.user, recipe)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Add or remove recipe from user's shopping cart."""
        self.model = ShoppingCart
        self.serializer_class = RecipeShortSerializer
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            return self.add(request.user, recipe)
        return self.remove(request.user, recipe)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Download aggregated shopping list of ingredients for user."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(total=Sum('amount'))

        lines = ['Список покупок:\n']
        lines.extend(
            f"- {item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) - "
            f"{item['total']}"
            for item in ingredients
        )

        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={request.user.username}_shopping_list.txt'
        )
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for listing and filtering ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for listing tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users and subscriptions."""

    queryset = User.objects.all()

    def get_permissions(self):
        """Return permissions depending on action and user role."""
        if self.action in ('create', 'list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.request.user.is_staff:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Return serializer class depending on action and user role."""
        if self.action == 'create':
            return CreateUserSerializer
        if self.request.user.is_staff:
            return AdminUserSerializer
        return UserSerializer

    @action(detail=False, methods=('get',))
    def me(self, request):
        """Return current user's profile."""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=('post',))
    def set_password(self, request):
        """Change password for the current user."""
        user = request.user
        if not user.check_password(request.data.get('current_password')):
            return Response(
                {'detail': 'Текущий пароль неверный'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(request.data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('post', 'get', 'delete', 'put'),
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def avatar(self, request):
        """Manage current user's avatar (get, set, or delete)."""
        user = request.user

        if request.method == 'GET':
            return Response(
                {'avatar': user.avatar.url if user.avatar else None}
            )

        avatar = request.data.get('avatar')
        if request.method in ('POST', 'PUT'):
            if not avatar:
                return Response(
                    {'detail': 'Файл не предоставлен'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserSerializer(
                user,
                data={'avatar': avatar},
                partial=True,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK,
            )

        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=('avatar',))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        """Subscribe or unsubscribe to another user."""
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        """List all authors current user is subscribed to."""
        authors = User.objects.filter(
            subscribed__user=request.user
        ).prefetch_related('recipes').order_by('id')

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page if page is not None else authors,
            many=True,
            context={'request': request},
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
