import re

from django.core.exceptions import ValidationError


def validate_username_format(username):
    """Validate allowed characters and reserved usernames."""
    if not re.match(r'^[\w.@+-]+\Z', username):
        raise ValidationError(
            "Username должен содержать только буквы, цифры и символы @/./+/-/_"
        )
    if username.lower() == 'me':
        raise ValidationError(
            "Использовать 'me' в качестве username запрещено."
        )
    return username


def validate_ingredients(ingredients_data):
    """Validate ingredient list for emptiness and duplicates."""
    if not ingredients_data:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один ингредиент.'
        )

    ingredient_ids = []
    for ingredient_item in ingredients_data:
        if isinstance(ingredient_item, dict):
            ingredient_ids.append(ingredient_item.get('id'))
        else:
            ingredient_ids.append(ingredient_item)

    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError('Ингредиенты не должны повторяться.')

    return ingredients_data


def validate_tags(tags_data):
    """Validate tag list for emptiness and duplicates."""
    if not tags_data:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один тег.'
        )

    if len(tags_data) != len(set(tags_data)):
        raise ValidationError('Теги в рецепте не должны повторяться.')

    return tags_data
