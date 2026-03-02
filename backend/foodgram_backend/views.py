from django.shortcuts import redirect
from django.urls import reverse

from api.services.short_links import RecipeShortLinkService


def short_link_redirect(request, short_code):
    """Redirect a short code URL to the full recipe detail page."""
    recipe = RecipeShortLinkService.get_recipe_by_code(short_code)
    recipe_url = reverse('recipe-detail', kwargs={'pk': recipe.pk})
    return redirect(recipe_url)
