from django.conf.urls import url
from . import views
urlpatterns = [
    # 发起支付
    url(r'^orders/(?P<order_id>\d+)/payment/$', views.PaymentView.as_view()),
    # 修改订单状态
    url(r'^payment/status/$', views.PaymentStatus.as_view()),
]