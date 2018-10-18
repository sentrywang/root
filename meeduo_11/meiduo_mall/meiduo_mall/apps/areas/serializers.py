from rest_framework import serializers
from .models import Area

# 获取省份的序列化器
class AreasSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name']

# 获取市及市下面区的序列化器
class SubsAreaSerializers(serializers.ModelSerializer):
    subs = AreasSerialzier(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']


