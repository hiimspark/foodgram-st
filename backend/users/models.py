from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from utils.constants import (EMAIL_LEN, USER_NAMES_LEN,
                             AVATAR_UPLOAD_PATH, USERNAME_VALIDATOR_REGEX,
                             USERNAME_VALIDATOR_MESSAGE,)


class User(AbstractUser):
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    USERNAME_FIELD = 'email'
    username_regex = RegexValidator(
        regex=USERNAME_VALIDATOR_REGEX,
        message=USERNAME_VALIDATOR_MESSAGE
    )

    username = models.CharField(
        'Уникальный юзернейм',
        validators=[username_regex],
        max_length=USER_NAMES_LEN,
        unique=True,
    )
    email = models.EmailField('Адрес электронной почты', unique=True,
                              max_length=EMAIL_LEN)
    first_name = models.CharField('Имя', max_length=USER_NAMES_LEN)
    last_name = models.CharField('Фамилия', max_length=USER_NAMES_LEN)
    password = models.CharField('Пароль')
    avatar = models.ImageField(
        'Аватар',
        upload_to=AVATAR_UPLOAD_PATH,
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
        ordering = ('sub_to',)
        constraints = [
            models.UniqueConstraint(
                fields=['sub_from', 'sub_to'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(sub_from=models.F('sub_to')),
                name='prevent_self_subscription'
            ),
        ]

    def __str__(self):
        return f'Пользователь {self.sub_from} подписан на {self.sub_to}'
