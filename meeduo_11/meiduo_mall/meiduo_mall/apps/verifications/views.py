from django.shortcuts import render
from django.http import HttpResponse
from django_redis import get_redis_connection
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
# from meiduo_mall.libs.yuntongxun.sms import CCP
from rest_framework.response import Response

from meiduo_mall.libs.captcha.captcha import captcha
from . import constants
import random
from .serializers import SMSCodeSerializer
from celery_tasks.sms import tasks

# Create your views here.


class ImageCodeView(APIView):
    """
    生成图片验证码
    """

    def get(self, request, image_code_id):
        # 生成验证码
        text, image = captcha.generate_captcha()
        # 存储在redis中
        conn = get_redis_connection('verify_codes')
        # 写入数据库，设置过期时间
        conn.setex('img_%s'%image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        # 返回的图片
        return  HttpResponse(image, content_type="images/jpg")


# 短信验证码
# ApiVIew
# GenericApView
class SMSCodesView(GenericAPIView):
    '''短信验证码'''
    '''
    检查图片验证码
    检查是否在60s内有发送记录
    生成短信验证码
    保存短信验证码与发送记录
    发送短信
    '''

    serializer_class = SMSCodeSerializer

    def get(self, request, mobile):

        # 获取前端传来的数据
        data = request.query_params
        # 校验, 使用序列化机器校验
        ser = self.get_serializer(data=data)
        ser.is_valid(raise_exception=True)

        # 发送短信验证码

        sms_code = random.randint(0, 999999)
        sms_code = '%06d'%sms_code

        # 云通讯发送验证码
        # ccp = CCP()
        # ccp.send_template_sms(mobile, sms_code, constants.SMS_CODE_TEMPLATE_ID)
        tasks.send_sms_code.delay(mobile, sms_code)

        conn = get_redis_connection('verify_codes')
        # conn.setex('sms_%s'%mobile, constants.SMS_CODE_EXPIRE, sms_code)
        # # 保存发送的记录， 便于校验是否频繁发送
        # conn.setex('send_sms_code_%s'%mobile, constants.SEND_SEMS_CODE_RATE,1)

        # 减少对redis的写入次数
        pl = conn.pipeline()
        pl.setex('sms_%s'%mobile, constants.SMS_CODE_EXPIRE, sms_code)
        # # 保存发送的记录， 便于校验是否频繁发送
        pl.setex('send_sms_code_%s'%mobile, constants.SEND_SEMS_CODE_RATE,1)
        # 执行管道里的操作
        pl.execute()


        # 返回 ok
        return Response({'message': 'ok'})









