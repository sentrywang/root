from django.conf.urls import url
from . import views

urlpatterns = [
    # 保存购物车信息
    url(r'cart/$', views.CartView.as_view()),
    # 全选
    url(r'cart/selection/$', views.CartSelectedAllView.as_view()),
]