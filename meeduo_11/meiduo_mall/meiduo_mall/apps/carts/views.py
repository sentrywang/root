from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from .serializer import CartSerialzier,CartSKUSerialzier,CartDeleteSerializer,CartSelectedSerializer
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
import pickle
import base64
from . import constants
from goods.models import SKU
# Create your views here.


class CartView(APIView):
    '''
    购物车
    '''

    # serializer_class = CartSerialzier

    def perform_authentication(self, request):
        '''
        全部校验token来登录
        '''
        pass

    def post(self, request):
        """
        添加购物车
        """
        serializer = CartSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 尝试对请求的用户进行验证
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录，在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 记录购物车商品数量
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            # 记录购物车的勾选项
            # 勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，在cookie中保存
            # {
            #     1001: { "count": 10, "selected": true},
            #     ...
            # }
            # 使用pickle序列化购物车数据，pickle操作的是bytes类型
            cart = request.COOKIES.get('cart')
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart.encode()))
            else:
                cart = {}

            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get('count'))

            cart[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()

            response = Response(serializer.data, status=status.HTTP_201_CREATED)

            # 设置购物车的cookie
            # 需要设置有效期，否则是临时cookie
            response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)
            return response

    def get(self, request):
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            conn = get_redis_connection('cart')
            pl = conn.pipeline()
            # 商品的数量
            redis_cart = conn.hgetall('cart_%s' % user.id)
            # 商品的勾选状态
            # (sku_Id, true)
            redis_cart_selected =conn.smembers('cart_selected_%s' % user.id)

            cart = {}
            # 组装数据
            '''
            sku_id: {
                count:10,
                selected:True
            }
            '''
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count':int(count),
                    #  选择状态
                    'selected': sku_id in redis_cart_selected
                }
        else:
            # 未登录就写入cookie
            cart = request.COOKIES.get('cart')
            if cart:
                # 判断之前是否添加过购物车，
                # 添加过购物车把商品数量增加
                cart = pickle.loads(base64.b64decode(cart.encode()))
            # 若没有就是新添加的cookie
            else:
                cart = {}

        # 遍历处理购物车数据
        #根据商品的ｉｄ取出信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            # 获取当前商品的数量
            sku.count = cart[int(sku.id)]['count']
            # 获取当前商品的勾选状态
            sku.selected = cart[int(sku.id)]['selected']

        #输出
        ser = CartSKUSerialzier(skus, many=True)
        return Response(ser.data)


    def put(self, request):
        '''修改购物车商品'''

        ser = CartSerialzier(data=request.data)
        ser.is_valid(raise_exception=True)
        sku_id = ser.validated_data.get('sku_id')
        count = ser.validated_data.get('count')
        selected = ser.validated_data.get('selected')


        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            user = None
        # 登录
        if user and user.is_authenticated:
            conn = get_redis_connection('cart')
            pl = conn.pipeline()
            # 修改数量
            pl.hset('cart_%s'%user.id, sku_id, count)
            # 是被选择
            if selected:
                # 增加
                pl.sadd("cart_selected_%s"%user.id, sku_id)
            else:
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(ser.data)

        # 未登
        else:
            # 未登录就写入cookie
            cart = request.COOKIES.get('cart')
            if cart:
                # 判断之前是否添加过购物车，
                # 添加过购物车把商品数量增加
                cart = pickle.loads(base64.b64decode(cart.encode()))

            # 若没有就是新添加的cookie
            else:
                cart = {}
            # 获取购物车商品
            sku = cart.get(sku_id)
            if sku:
                # 获取商品的数量， 对数量进行增加
                count += int(sku.get('count'))

            # 给购物车重新赋值
            # 不管是否有购物车记录都是重新赋值的
            cart[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 转化为byte
            data_byte = pickle.dumps(cart)
            #  转为base64的byte的str
            bs64_data = base64.b64encode(data_byte)
            #
            cookie_data = bs64_data.decode()

            # 写入cookie里
            # 设置购物车的cookie
            # 需要设置有效期，否则是临时cookie
            response = Response(ser.data, status=status.HTTP_201_CREATED)

            response.set_cookie('cart', cookie_data, max_age=constants.CART_COOKIE_EXPIRES)

            return response


    def delete(self,request):

        # 校验商品数量
        ser = CartDeleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sku_id = ser.validated_data['sku_id']

        # 判断是否登录
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None


        # 登录
        if user is not None and user.is_authenticated:
            # 用户已登录，在redis中保存
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            cart = request.COOKIES.get('cart')

            if cart:
                cart = pickle.loads(base64.b64decode(cart.encode()))

                response = Response(ser.data, status=status.HTTP_204_NO_CONTENT)
                if sku_id in cart:
                    # 删除sku_id
                    del cart[sku_id]

                    # 把字典转化为str
                    cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                    # 从新生成cookie
                    # 设置购物车的cookie
                    # 需要设置有效期，否则是临时cookie
                    response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)

                return response




class CartSelectedAllView(APIView):
    '''
    全选视图
    '''
    def perform_authentication(self, request):
        '''
        全部校验token来登录
        '''
        pass

    def put(self, request):
        serializer = CartSelectedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        # 判断是否登录
        try:
            user = request.user
        except Exception:
            # 验证失败，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 用户已登录，在redis中保存
            redis_conn = get_redis_connection('cart')
            cart = redis_conn.hgetall('cart_%s' % user.id)
            # 取出所有的商品的ｓｋｕ-Id
            sku_id_list = cart.keys()

            if selected:
                # 全选
                # sku_id_list [1,2,3,4] *sku_id_List [1,2,3,4]======> 1,2,3,4
                redis_conn.sadd('cart_selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_conn.srem('cart_selected_%s' % user.id, *sku_id_list)
            return Response({'message': 'OK'})
        # 没有登录，　修改已有购物车商品的额状态信息　，　修改后重新生成cookie
        else:
            cart = request.COOKIES.get('cart')

            response = Response({'message': 'OK'})

            if cart is not None:
                # 取出已有的商品的购物车cookie，进行反解码，　ｄｉｃｔ
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    # 给商品的全选状态重新赋值
                    cart[sku_id]['selected'] = selected
                #再次生成ｃｏｏｋｉｅ
                cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                # 设置购物车的cookie
                # 需要设置有效期，否则是临时cookie
                response.set_cookie('cart', cookie_cart, max_age=constants.CART_COOKIE_EXPIRES)

            return response










