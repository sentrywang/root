from rest_framework import serializers

from goods.models import  SKU

class CartSerialzier(serializers.Serializer):
    '''
    购物车序列化器
    '''

    sku_id = serializers.IntegerField(label='sku id ', min_value=1)
    count = serializers.IntegerField(label='数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    def validate(self, data):
        try:
            # 查询是否商品存在
            sku = SKU.objects.get(id=data['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        # 校验商品的库存， 库存不足抛出异常
        if data['count'] > sku.stock:
            raise serializers.ValidationError('商品库存不足')

        return data


class CartSKUSerialzier(serializers.ModelSerializer):
    '''
    购物车商品信息序列化器
    '''
    count = serializers.IntegerField(label='数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'count', 'selected', 'default_image_url']


class CartDeleteSerializer(serializers.Serializer):
    """
    删除购物车数据序列化器
    """
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value

class CartSelectedSerializer(serializers.Serializer):
    '''全选序列化器'''

    selected = serializers.BooleanField(label='是否勾选', default=True)





