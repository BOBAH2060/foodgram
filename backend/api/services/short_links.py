from django.http import Http404

from recipes.models import Recipe


from .constants import (
    SHORT_LINK_ALPHABET,
    SHORT_LINK_BASE,
    SHORT_LINK_MIN_LENGTH,
    ZERO_RECIPE_ID,
    SHORT_LINK_NOT_FOUND_MESSAGE,
)


class RecipeShortLinkService:
    """Service for generating and decoding recipe short links."""

    @classmethod
    def make_code(cls, recipe_id: int) -> str:
        """Generate a short code from a recipe ID."""
        if recipe_id == ZERO_RECIPE_ID:
            return SHORT_LINK_ALPHABET[ZERO_RECIPE_ID] * SHORT_LINK_MIN_LENGTH

        return cls._encode(recipe_id).zfill(SHORT_LINK_MIN_LENGTH)

    @classmethod
    def get_recipe_by_code(cls, short_code: str) -> Recipe:
        """Return a recipe by its short code or raise 404."""
        try:
            recipe_id = cls._decode(short_code.lower())
            return Recipe.objects.get(pk=recipe_id)
        except (ValueError, Recipe.DoesNotExist) as exc:
            raise Http404(SHORT_LINK_NOT_FOUND_MESSAGE) from exc

    @classmethod
    def _encode(cls, recipe_id: int) -> str:
        """Encode a recipe ID into a short string."""
        result = ''
        while recipe_id:
            recipe_id, remainder = divmod(recipe_id, SHORT_LINK_BASE)
            result = SHORT_LINK_ALPHABET[remainder] + result
        return result

    @classmethod
    def _decode(cls, code: str) -> int:
        """Decode a short string back into a recipe ID."""
        result = 0
        for char in code:
            index = SHORT_LINK_ALPHABET.find(char)
            if index < 0:
                raise ValueError(f'Invalid short code char: {char}')
            result = result * SHORT_LINK_BASE + index
        return result
