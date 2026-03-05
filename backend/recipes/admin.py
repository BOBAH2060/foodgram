from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .constants import (
    RECIPE_INGREDIENT_INLINE_EXTRA,
    RECIPE_INGREDIENT_INLINE_MIN_NUM
)
from .models import (
    User,
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Favorite,
    ShoppingCart
)


admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'avatar'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active'
    )
    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональная информация'), {
            'fields': (
                'username',
                'first_name',
                'last_name',
                'avatar',
            )
        }),
        (_('Права доступа'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'user_permissions',
            )
        }),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_staff',
                'is_active',
            ),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = RECIPE_INGREDIENT_INLINE_EXTRA
    min_num = RECIPE_INGREDIENT_INLINE_MIN_NUM
    validate_min = True
    autocomplete_fields = ['ingredient']
    readonly_fields = ['measurement_unit']

    def measurement_unit(self, obj):
        return getattr(obj.ingredient, 'measurement_unit', '-')
    measurement_unit.short_description = 'Ед. изм.'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorites_count')
    list_filter = ('tags', 'author')
    inlines = (RecipeIngredientInline,)

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'Добавлено в избранное'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
