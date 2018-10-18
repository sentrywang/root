from django.conf.urls import url
from . import views

urlpatterns = [
    # qq登录获取登录url
    url(r'qq/authorization/$', views.QQAuthView.as_view()),
    # 获取QQ登录的用户
    url(r'qq/user/$', views.QQAuthUserView.as_view())
]
