import re
from django.core.exceptions import ValidationError


def validate_username_format(value):
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            "Username должен содержать только буквы, цифры и символы @/./+/-/_"
        )
    if value.lower() == 'me':
        raise ValidationError(
            "Использовать 'me' в качестве username запрещено."
        )
    return value


def validate_ingredients(value):
    if not value:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один ингредиент.'
        )
    if isinstance(value[0], dict):
        ids = [item.get('id') for item in value]
        if len(ids) != len(set(ids)):
            raise ValidationError('Ингредиенты не должны повторяться.')

    return value


def validate_tags(value):
    if not value:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один тег.'
        )

    if len(value) != len(set(value)):
        raise ValidationError('Теги в рецепте не должны повторяться.')

    return value
