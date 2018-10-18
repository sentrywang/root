from rest_framework import serializers
from django_redis import get_redis_connection



class SMSCodeSerializer(serializers.Serializer):
    '''图片验证码校验序列化器'''

    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4, label='图片验证码')



    def validate(self, attrs):
        # 图片验证码是否正确
        # 取出图片验证码

        # 前端查询字符串传来的要校验的数据
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 取出redis中的数据进行校验
        conn = get_redis_connection('verify_codes')
        real_img_code = conn.get('img_%s'% image_code_id)


        # 防止前端对同一张图片验证码进行多次校验
        conn.delete('img_%s'% image_code_id)

        #判断是否有效
        if not real_img_code:
            raise serializers.ValidationError('图片验证码过期！！')

        # 判断验证码是否正确
        if text.lower() != real_img_code.decode().lower():
            raise serializers.ValidationError('图片验证码错误')

        # 手机号判断
        # 短信验证码的频率
        mobile = self.context['view'].kwargs['mobile']
        # 判断是否发送过短信验证码
        if conn.get('send_sms_code_%s'%mobile):
            raise serializers.ValidationError('请求次数过于频繁')

        return attrs









