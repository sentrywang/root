from django.conf.urls import url

from . import views

urlpatterns = [
    # 生成验证码图片
    url(r'image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),
    # 发送短信验证码
    url(r'sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodesView.as_view()),
]