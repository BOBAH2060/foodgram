from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def encode(num: int) -> str:
    if num == 0:
        return "000"

    result = ""
    while num:
        num, rem = divmod(num, 36)
        result = ALPHABET[rem] + result

    return result.zfill(3)


def decode(code: str) -> int:
    result = 0
    for char in code:
        result = result * 36 + ALPHABET.index(char)
    return result


def redirect_short_link(request, short_code):
    try:
        recipe_id = decode(short_code)
        recipe = Recipe.objects.get(id=recipe_id)
        base_url = request.build_absolute_uri('/').rstrip('/')
        return redirect(f'{base_url}/api/recipes/{recipe.id}/')
    except (Recipe.DoesNotExist, ValueError):
        raise Http404('Короткая ссылка не найдена')
