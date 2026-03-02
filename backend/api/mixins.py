from rest_framework import status
from rest_framework.response import Response


class AddRemoveMixin:
    """Mixin for adding and removing recipe relations."""

    model = None
    serializer_class = None

    def add(self, user, recipe):
        """Add a recipe relation for the given user."""
        obj, created = self.model.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'errors': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.serializer_class(
            recipe, context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove(self, user, recipe):
        """Remove a recipe relation for the given user."""
        deleted, _ = self.model.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепта нет'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
