from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    date_joined = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'created_at', 'updated_at']
        read_only_fields = ['date_joined', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text=_('用户密码'),
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=False, allow_blank=True, help_text=_('邮箱地址（可选）'))
    phone = serializers.CharField(required=False, allow_blank=True, help_text=_('手机号（可选）'))
    avatar = serializers.URLField(required=False, allow_blank=True, help_text=_('头像URL（可选）'))
    
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone', 'avatar']
        
    def validate_phone(self, value):
        """验证电话号码"""
        if not value or value.strip() == '':
            return None
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError(_('请输入有效的11位手机号码'))
        return value
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        if 'phone' in validated_data and not validated_data['phone']:
            validated_data['phone'] = None
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True  # 确保新用户默认是激活状态
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser', 'password']
        extra_kwargs = {
            'username': {'required': True},  # PUT方法需要
            'email': {'required': False},
            'phone': {'required': False},
            'avatar': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
            'password': {'write_only': True, 'required': False}
        }
        
    def validate_phone(self, value):
        """验证电话号码"""
        if not value or value.strip() == '':
            return None
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError(_('请输入有效的11位手机号码'))
        return value
        
    def update(self, instance, validated_data):
        user = self.context['request'].user

        # 处理密码更新
        password = validated_data.pop('password', None)
        if password:
            if user.is_staff:
                instance.set_password(password)
            else:
                raise serializers.ValidationError({'password': _('普通用户不能修改密码。')})
        
        # 处理管理员状态更新 - 同步更新 is_staff 和 is_superuser
        is_staff = validated_data.pop('is_staff', None)
        is_superuser = validated_data.pop('is_superuser', None)
        
        # 确保 is_staff 和 is_superuser 保持同步
        if is_staff is not None or is_superuser is not None:
            if not user.is_staff:
                raise serializers.ValidationError({'is_staff': _('您没有权限修改管理员状态。')})
            
            # 如果只提供了其中一个字段，同步另一个字段
            if is_staff is not None and is_superuser is None:
                is_superuser = is_staff
            elif is_superuser is not None and is_staff is None:
                is_staff = is_superuser
            elif is_staff != is_superuser:
                # 如果两个字段都提供了但值不同，强制同步
                raise serializers.ValidationError({
                    'is_staff': _('is_staff 和 is_superuser 必须保持一致。'),
                    'is_superuser': _('is_staff 和 is_superuser 必须保持一致。')
                })
            
            # 同步更新两个字段
            instance.is_staff = is_staff
            instance.is_superuser = is_superuser

        if 'phone' in validated_data and not validated_data['phone']:
            validated_data['phone'] = None
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LoginUserSerializer(serializers.ModelSerializer):
    """登录用户序列化器 - 只返回必要字段"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser']

class UserSimpleSerializer(serializers.ModelSerializer):
    """简化的用户序列化器，用于关联查询展示"""
    class Meta:
        model = User
        fields = ['id', 'username']