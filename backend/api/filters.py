import django_filters

from recipes.models import Ingredient, Recipe, Tag
from .constants import ENABLED_FILTER_VALUE, DISABLED_FILTER_VALUE


class RecipeFilter(django_filters.FilterSet):
    """FilterSet for filtering recipes by author, tags and user relations."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )

    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Filter recipes by current user's favorites."""
        if not (self.request and self.request.user.is_authenticated):
            return queryset

        filter_value = str(value)
        if filter_value == ENABLED_FILTER_VALUE:
            return queryset.filter(
                favorited_by__user=self.request.user
            ).distinct()
        if filter_value == DISABLED_FILTER_VALUE:
            return queryset.exclude(
                favorited_by__user=self.request.user
            ).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Filter recipes by current user's shopping cart."""
        if not (self.request and self.request.user.is_authenticated):
            return queryset

        filter_value = str(value)
        if filter_value == ENABLED_FILTER_VALUE:
            return queryset.filter(
                in_shopping_cart__user=self.request.user
            ).distinct()
        if filter_value == DISABLED_FILTER_VALUE:
            return queryset.exclude(
                in_shopping_cart__user=self.request.user
            ).distinct()
        return queryset


class IngredientFilter(django_filters.FilterSet):
    """FilterSet for filtering ingredients by name prefix."""

    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
