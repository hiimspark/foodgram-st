from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.serializers import SetPasswordSerializer

from .serializers import UserSerializer, UserRegistrationSerializer
from .serializers import AvatarSerializer
from .serializers import CreateSubSerializer, SubSerializer
from users.models import User, Sub
from utils.pagination import FoodgramPagination


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = FoodgramPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(['post'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data['new_password'])
            self.request.user.save()
            return Response(
                'Пароль успешно изменен',
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(['put', 'delete'],
            detail=False,
            url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {
                        'avatar': ['Обязательное поле.']
                    }, status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = AvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            if user.avatar:
                user.avatar.delete()

            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if not user.avatar:
                return Response(
                    {
                        'detail': ['Аватар отсутствует.']
                    }, status=status.HTTP_400_BAD_REQUEST,
                )

            user.avatar.delete()
            user.save()
            return Response(
                {
                    'detail': ['Аватар успешно удален.']
                }, status=status.HTTP_204_NO_CONTENT,
            )

    @action(['post', 'delete'],
            detail=True,
            url_path='subscribe',
            url_name='subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk):
        if request.method == "POST":
            sub_to = User.objects.filter(pk=pk)
            if not sub_to.exists():
                return Response(
                    "Нельзя подписаться на несуществующего пользователя!",
                    status=status.HTTP_404_NOT_FOUND,
                )

            if (int(pk) == request.user.id):
                return Response(
                    "Нельзя подписаться на самого себя!",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sub = Sub.objects.filter(
                sub_from=request.user.id, sub_to=pk
            )
            if sub.exists():
                return Response(
                    "Вы уже подписаны на этого пользователя!",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = CreateSubSerializer(
                data={
                    "sub_from": request.user.id,
                    "sub_to": pk,
                },
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            sub_to = User.objects.filter(pk=pk)
            if not sub_to.exists():
                return Response(
                    "Нельзя отписаться от несуществующего пользователя!",
                    status=status.HTTP_404_NOT_FOUND,
                )

            sub = Sub.objects.filter(
                sub_from=request.user.id, sub_to=pk
            )

            if not sub.exists():
                return Response(
                    "Нельзя удалить несуществующую подписку!",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sub.delete()

            return Response(
                f"Вы отписались от пользователя {User.objects.get(pk=pk)}",
                status=status.HTTP_204_NO_CONTENT
            )

    @action(['get'],
            detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscribed_users = User.objects.filter(
            sub_to__sub_from=request.user).order_by('username')
        pages = self.paginate_queryset(subscribed_users)
        serializer = SubSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
