from django.urls import include, path
from rest_framework_nested import routers

from .views import (
    RecipeViewSet, ShoppingCartViewSet, FavoriteViewSet,
    IngredientViewSet, TagViewSet, UserViewSet, SubscriptionViewSet
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(
    r'shopping_cart', ShoppingCartViewSet, basename='shopping_cart'
)
router.register(
    r'subscriptions', SubscriptionViewSet, basename='subscription'
)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
