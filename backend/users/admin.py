from django.contrib import admin

from .models import User, Sub


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name',
        'username', 'email',
    )
    search_fields = (
        'email',
        'username',
    )


class SubAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sub_from',
        'sub_to',
    )


admin.site.register(User, UserAdmin)
admin.site.register(Sub, SubAdmin)
