from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')



urlpatterns = [
    # 判断用户名是否已经存在
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否注册过
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 注册
    url(r'^users/$', views.UserView.as_view()),
    # 登录
    # url(r'authorizations/$',obtain_jwt_token),
    # 重写登录方法
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),
    # 用户中心个人信息
    url(r'^user/$', views.UserDetailView.as_view()),
    # 保存邮箱
    url(r'emails/$', views.EmailView.as_view()),
    # 验证邮箱的token
    url(r'^emails/verification/$', views.VerifyEmail.as_view()),
    # 用户历史浏览记录
    url(r'browse_histories/$', views.BrowserHistoryView.as_view()),
]

urlpatterns += router.urls