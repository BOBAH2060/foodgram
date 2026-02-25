from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AdminUserSerializer,
    CreateUserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)
from .mixins import AddRemoveMixin
from .services.short_links import encode


class RecipeViewSet(AddRemoveMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    ]

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients'
        )

        params = self.request.query_params

        if author := params.get('author'):
            queryset = queryset.filter(author_id=author)

        if tags := params.getlist('tags'):
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        if (
            params.get('is_favorited') == '1'
            and self.request.user.is_authenticated
        ):
            queryset = queryset.filter(favorited_by__user=self.request.user)

        if (
            params.get('is_in_shopping_cart') == '1'
            and self.request.user.is_authenticated
        ):
            queryset = queryset.filter(
                in_shopping_cart__user=self.request.user
            )
        queryset = queryset.order_by('-id')

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        base_url = request.build_absolute_uri('/').rstrip('/')
        short_code = encode(self.get_object().id)
        short_url = f'{base_url}/s/{short_code}'
        return Response({'short-link': short_url})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        self.model = Favorite
        self.serializer_class = RecipeShortSerializer
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            return self.add(request.user, recipe)
        return self.remove(request.user, recipe)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        self.model = ShoppingCart
        self.serializer_class = RecipeShortSerializer
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            return self.add(request.user, recipe)
        return self.remove(request.user, recipe)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total=Sum('amount'))

        content = ['Список покупок:\n']
        content.extend(
            f"- {item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — {item['total']}"
            for item in ingredients
        )

        response = HttpResponse(
            '\n'.join(content), content_type='text/plain'
        )
        response['Content-Disposition'] = (
            f'attachment; filename={request.user.username}_shopping_list.txt'
        )
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if name := self.request.query_params.get('name'):
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ShoppingCartViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShoppingCart.objects.filter(
            user=self.request.user
        ).select_related('recipe')


class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('recipe')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ('create', 'list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.request.user.is_staff:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        if self.request.user.is_staff:
            return AdminUserSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        user = request.user
        if not user.check_password(request.data.get('current_password')):
            return Response(
                {'detail': 'Текущий пароль неверный'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(request.data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post', 'get', 'delete', 'put'],
        url_path='me/avatar'
    )
    def avatar(self, request):
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
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserSerializer(
                user,
                data={'avatar': avatar},
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {'avatar': serializer.data['avatar']},
                status=status.HTTP_200_OK
            )

        if request.method == 'DELETE':
            if not user.avatar.name.startswith('data:image'):
                user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            obj, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscribed__user=request.user
        ).prefetch_related('recipes')

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page or authors,
            many=True,
            context={'request': request}
        )
        if page:
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(
            user=self.request.user
        ).select_related('author').prefetch_related('author__recipes')
