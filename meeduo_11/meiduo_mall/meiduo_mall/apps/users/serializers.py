from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from django_redis import get_redis_connection
import re
from .models import Address
from .models import User
from . import constants
from goods.models import SKU
from celery_tasks.email.tasks import send_verify_email


class UserInfoSerializer(serializers.ModelSerializer):
    '''
    注册序列化器
    '''

    sms_code = serializers.CharField(write_only=True, label='短信验证码')
    password2 = serializers.CharField(write_only=True, label='确认密码')
    allow = serializers.CharField(label='确认协议', write_only=True)
    token = serializers.CharField(max_length=64, label='token', read_only=True)

    extra_kwargs = {
        'username': {
            'min_length': 5,
            'max_length': 20,
            'error_messages': {
                'min_length': '仅允许5-20个字符的用户名',
                'max_length': '仅允许5-20个字符的用户名',
            }
        },
        'password': {
            'write_only': True,
            'min_length': 8,
            'max_length': 20,
            'error_messages': {
                'min_length': '仅允许8-20个字符的密码',
                'max_length': '仅允许8-20个字符的密码',
            }
        }
    }

    class Meta:
        model = User

        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        创建用户
        """
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        # 对密码进行加密，否则是明文保存
        user.set_password(validated_data['password'])
        user.save()


        # 返回前保存 token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user) # 用户信息方式载荷
        token = jwt_encode_handler(payload) # 加密
        user.token = token # 添加额外属性

        return user




class UserDetailSerializer(serializers.ModelSerializer):
    '''
    用户中心序列化器
    '''
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']



class EmailSerializer(serializers.ModelSerializer):
    '''
    邮箱序列化器
    '''
    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            'email': {
                'required': True
            }
        }


    def update(self, instance, validated_data):

        email = validated_data.get('email')
        #更新邮箱
        instance.email = validated_data.get('email', None)
        instance.save()


        # 发送邮件
        # 生成验证邮箱
        verify_url = instance.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        return instance

class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)



class BrowserHistorySerializer(serializers.Serializer):
    '''
    历史浏览记录的序列化器
    '''
    sku_id = serializers.IntegerField(label='商品的id', min_value=1)


    def validate_sku_id(self, value):
        '''
        校验商品是否存在

        :param value:
        :return:
        '''
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise  serializers.ValidationError('商品已经下架！！')

        return value

    def create(self, validated_data):
        '''
        写入redis数据库
        :param validated_data:
        :return:
        '''
        sku_id = validated_data['sku_id']
        user_id = self.context['request'].user.id


        conn = get_redis_connection('history')
        pl = conn.pipeline()
        pl.lpush('history_%s'%user_id, sku_id)
        # 只保存最多5条记录
        pl.ltrim("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        pl.execute()

        return validated_data











