from rest_framework import status
from rest_framework.response import Response


class AddRemoveMixin:
    """Mixin for adding and removing recipe relations."""

    def add_to_user_relation(
            self, user, recipe, model, serializer_class=None, request=None
    ):
        """Add a recipe relation for the given user."""
        obj, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'errors': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = serializer_class(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_user_relation(self, user, recipe, model):
        """Remove a recipe relation for the given user."""
        deleted, _ = model.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепта нет'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
