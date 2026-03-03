from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from api.services.short_links import RecipeShortLinkService


def short_link_redirect(request, short_code):
    """Redirect a short code URL to the full recipe detail page."""
    recipe = RecipeShortLinkService.get_recipe_by_code(short_code)
    relative_url = reverse('recipe-detail', kwargs={'pk': recipe.pk})
    domain = getattr(settings, 'MEDIA_DOMAIN', None) or request.get_host()
    absolute_url = f'{domain}{relative_url}'

    return redirect(absolute_url)
