from rest_framework import serializers
from users.models import User, Sub
from api.serializers import DecodeBase64ImageField


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return not user.is_anonymous and \
            Sub.objects.filter(sub_from=user, sub_to=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = DecodeBase64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(
        method_name="get_users_recipes")
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_users_recipes(self, obj):
        from recipes.serializers import RecipeForCartSerializer

        request = self.context.get("request")
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get("recipes_limit")

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return RecipeForCartSerializer(recipes, context={"request": request},
                                       many=True).data


class CreateSubSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sub
        fields = ("sub_to", "sub_from")
        extra_kwargs = {
            "sub_to": {"write_only": True},
            "sub_from": {"write_only": True},
        }

    def to_representation(self, instance):
        user = instance.sub_to
        return SubSerializer(user, context=self.context).data
