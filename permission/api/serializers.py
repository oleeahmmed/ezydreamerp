from rest_framework import serializers
from django.contrib.auth.models import User, Permission, Group

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, required=True, write_only=True)

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class UserPermissionSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'groups', 'permissions']

    def get_permissions(self, obj):
        # Combine direct and group permissions
        direct_permissions = obj.user_permissions.all()
        group_permissions = Permission.objects.filter(group__user=obj).distinct()

        # Use sets for efficient union
        all_permission_pks = set(direct_permissions.values_list('pk', flat=True))
        all_permission_pks.update(group_permissions.values_list('pk', flat=True))

        all_permissions = Permission.objects.filter(pk__in=all_permission_pks).order_by('content_type__app_label', 'codename')

        return PermissionSerializer(all_permissions, many=True).data