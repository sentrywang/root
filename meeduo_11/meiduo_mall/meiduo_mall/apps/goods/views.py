from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from .serializers import SKUSerializer, SKUSearchSerializer
from .models import SKU
from drf_haystack.viewsets import HaystackViewSet
# Create your views here.

class SKUListView(ListAPIView):
    """
    sku列表数据
    """
    # 使用的序列化器
    serializer_class = SKUSerializer
    # 过滤后端
    filter_backends = (OrderingFilter,)
    # 过滤的字段
    ordering_fields = ('create_time', 'price', 'sales')

    # get_object()
    # get_serialzier_class
    # get_serializer()

    def get_queryset(self):
        '''
        重写方法获取指定的数据
        :return:
        '''
        # 商品的类别id
        # 是从视图来的 self.context['view'].kwrage['categories']
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id, is_launched=True )



class SKUSearchViewSet(HaystackViewSet):
    '''
    获得商品的索引
    '''
    # index_models 是指明哪些模型类创建了索引的模型类
    index_models = [SKU]

    # 把搜索后的商品信息返回
    serializer_class = SKUSearchSerializer


























