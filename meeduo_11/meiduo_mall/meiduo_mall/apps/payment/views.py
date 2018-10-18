from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from alipay import AliPay
from django.conf import settings
from .models import Payment
from orders.models import OrderInfo
import os

class PaymentView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        '''
        发起支付
        :param request:
        :param order_id: 前端传来的订单id
        :return:
        '''
        user= request.user

        # 校验订单号
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user,
                                     pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'],
                                     status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)
        # 生成网站链接支付宝的客户端
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID, # 网站的id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2 加密方式
            debug=settings.ALIPAY_DEBUG  # 默认False， 沙箱环境
        )
        # 根据客户端调用接口，来生成交易的流水号， 3456789
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
        )
        # 拼接链接，返回给用户，让用户去登录
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return Response({'alipay_url': alipay_url})



class PaymentStatus(APIView):
    '''支付成功修改订单状态'''

    def put(self, request):
        # 获取查询字符串的参数
        data = request.query_params.dict()
        # 取出签证信息
        sign = data.pop('sign')

        # 创建网站链接支付宝的客户端
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID,  # 网站的id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2 加密方式
            debug=settings.ALIPAY_DEBUG  # 默认False， 沙箱环境
        )
        # 调用verify()验证签证及返回前端的数据是否正确
        success = alipay_client.verify(data, sign)
        if success:
            # 创建交易成功的数据，在模型类中添加当前交易的信息
            # 订单编号
            order_id = data.get('out_trade_no')
            # 支付宝支付流水号
            trade_id = data.get('trade_no')
            Payment.objects.create(
                order_id= order_id,
                trade_id =  trade_id
            )
            # 修改订单的状态
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            # 返回客户交易成功的流水号
            return Response({'trade_id': trade_id})

        else:
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)

