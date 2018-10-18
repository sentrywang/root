from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
from .serializers import OrderSettlementSerializer, CartInfoSerialzier
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView

class CartView(APIView):
    '''创建订单'''

    # 登陆后才能下单
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 从redis取出被勾选的商品
        # 从购物车中获取用户勾选要结算的商品信息
        user = request.user
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

        # 获取被勾选的商品
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])


        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
        # 返回

        # 运费
        freight = Decimal('10.00')
        # 输出商品
        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})

        return Response(serializer.data)




class OrderCartCreate(CreateAPIView):
    '''保存订单'''

    permission_classes = [IsAuthenticated]
    serializer_class = CartInfoSerialzier










