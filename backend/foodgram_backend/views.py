from django.shortcuts import redirect
from django.conf import settings

from api.services.short_links import RecipeShortLinkService


def short_link_redirect(request, short_code):
    """Redirect a short code URL to the full recipe detail page."""
    recipe = RecipeShortLinkService.get_recipe_by_code(short_code)
    domain = settings.MEDIA_DOMAIN.rstrip('/')
    frontend_url = f'{domain}/recipes/{recipe.pk}/'

    return redirect(frontend_url)
