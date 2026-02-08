from rest_framework import serializers
from .models import DatabaseConfig

class DatabaseConfigSerializer(serializers.ModelSerializer):
    """数据库配置序列化器"""
    
    # 将db_type映射为type以符合前端期望
    type = serializers.CharField(source='db_type')
    
    # 修改时间字段名称
    created_time = serializers.DateTimeField(source='created_at', read_only=True)
    updated_time = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = DatabaseConfig
        fields = [
            'id', 'name', 'project', 'type', 'host', 'port', 
            'username', 'password', 'database', 'charset',
            'connection_params', 'psm', 'verify_ssl', 
            'description', 'is_active', 'created_by',
            'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_by', 'created_time', 'updated_time']
        
    def to_representation(self, instance):
        """重写数据表示方法"""
        data = super().to_representation(instance)
        
        # 出于安全考虑，隐藏密码信息
        if 'password' in data:
            data['password'] = '******'
            
        # 确保connection_params是一个字典
        if data.get('connection_params') is None:
            data['connection_params'] = {}
            
        return data
        
    def create(self, validated_data):
        """创建时处理db_type字段和created_by字段"""
        # 从source字段中获取db_type的值
        if 'db_type' in validated_data:
            # 已经是db_type，不需要处理
            pass
        elif 'type' in validated_data:
            # type字段需要映射到db_type
            db_type = validated_data.pop('type')
            validated_data['db_type'] = db_type
            
        # 设置创建人
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        """更新时处理db_type字段"""
        # 处理type到db_type的映射
        if 'db_type' in validated_data:
            # 已经是db_type，不需要处理
            pass
        elif 'type' in validated_data:
            # type字段需要映射到db_type
            db_type = validated_data.pop('type')
            validated_data['db_type'] = db_type
            
        return super().update(instance, validated_data) 