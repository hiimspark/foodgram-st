from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    USERNAME_FIELD = 'email'

    username_regex = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message='Уникальный юзернейм может содержать только '
        'буквы, цифры и @/./+/-/_'
    )

    username = models.CharField(
        'Уникальный юзернейм',
        validators=[username_regex],
        max_length=150,
        unique=True,
    )

    email = models.EmailField('Адрес электронной почты', unique=True,
                              max_length=254)

    first_name = models.CharField('Имя', max_length=150)

    last_name = models.CharField('Фамилия', max_length=150)

    password = models.CharField('Пароль')

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        default=None,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Sub(models.Model):

    sub_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sub_to",
        verbose_name="Пользователь, на кого подписались",
    )

    sub_from = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sub_from",
        verbose_name="Пользователь, который подписался",
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['sub_to']

    def __str__(self):
        return f'Пользователь {self.sub_from} подписан на {self.sub_to}'
