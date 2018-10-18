from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
# Create your views here.
from .models import Area
from .serializers import AreasSerialzier, SubsAreaSerializers
from rest_framework_extensions.cache.mixins import CacheResponseMixin

class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    ''''省市区'''

    pagination_class = None

    def get_queryset(self):
        """
        提供数据集
        """
        if self.action == 'list':
            # 获取省份
            return Area.objects.filter(parent=None)
        else:
            # # 获取省份下面的一个市, 获取一个市下面的的一个区/县
            return Area.objects.all()

    def get_serializer_class(self):
        """
        提供序列化器
        """
        if self.action == 'list':
            return AreasSerialzier
        else:
            return SubsAreaSerializers




