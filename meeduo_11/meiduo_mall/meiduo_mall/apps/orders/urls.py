from django.conf.urls import url
from . import views
urlpatterns = [
    # 创建订单
    url(r'^orders/settlement/$', views.CartView.as_view()),
    # 保存订单
    url(r'^orders/$', views.OrderCartCreate.as_view()),
]