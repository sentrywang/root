from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from django_redis import get_redis_connection
from . import serializers
from goods.models import SKU
from goods.serializers import SKUSerializer
from .serializers import UserInfoSerializer,UserDetailSerializer,EmailSerializer, BrowserHistorySerializer
from .models import User
from . import constants
from carts.utils import merage_cart_sku
# Create your views here.

class UsernameCountView(APIView):
    """
    用户名数量
    """
    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserView(CreateAPIView):

    serializer_class = UserInfoSerializer


class UserDetailView(RetrieveAPIView):
    '''
    用户中心个人信息
    '''
    # 登陆成功才能修改个人信息
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer


    def get_object(self):

        # 返回当前登录的用户的对象
        return self.request.user


class EmailView(UpdateAPIView):
    '''
    保存邮箱
    '''

    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    # 返回当前用户的信息，包含邮箱
    def get_object(self):
        return self.request.user


class VerifyEmail(UpdateAPIView):
    '''
    校验激活邮箱的url

    '''
    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        # print(token)
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # token解密
        user = User().check_verify_email_url(token)
        if not user:
            return Response({'message': 'token失效'})
        else:
            user.email_active = True
            user.save()
            return Response({'message': 'OK'})



class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    # POST /addresses/
    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class BrowserHistoryView(CreateAPIView):
    '''
    保存历史浏览记录
    '''
    # 查看历史浏览记录要登录
    permission_classes = [IsAuthenticated]
    serializer_class = BrowserHistorySerializer

    # def post(self, request):
    #     '''
    #     保存
    #     :param request:
    #     :return:
    #     '''
    #     ser = self.get_serializer()
    #     ser.is_valid(raise_exception=True)
    #     ser.save()
    #     return self.create()


    def get(self, request):
        '''
        获取历史浏览记录
        :param request:
        :return:
        '''
        # 获取当前用户的id
        user_id = request.user.id

        # 获取redis数据
        conn=  get_redis_connection('history')
        # 取出redis数据
        history = conn.lrange('history_%s'%user_id, 0, -1)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保存顺序一致
        for sku_id in history:
            # sku_id 是byte字节类型
            # byte 是由redis 和ｐｙｔｈｏｎ　链接的中间插件来转化的
            # id 是integer
            sku = SKU.objects.get(id=sku_id.decode())
            skus.append(sku)

        s = SKUSerializer(skus, many=True)

        # 返回序列化后的数据
        return Response(s.data)


from rest_framework_jwt.views import ObtainJSONWebToken

class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """
    def post(self, request, *args, **kwargs):
        # 调用父类的方法，获取drf jwt扩展默认的认证用户处理结果
        response = super().post(request, *args, **kwargs)

        # 仿照drf jwt扩展对于用户登录的认证方式，判断用户是否认证登录成功
        # 如果用户登录认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 校验当前登录用户，成功获取用户信息
            user = serializer.validated_data.get('user')
            # 合并当前用户cookie中的购物车信息到的redis中
            response = merage_cart_sku(request, user, response)

        return response



