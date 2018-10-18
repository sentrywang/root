import base64
import pickle
from django_redis import get_redis_connection


def  merage_cart_sku(request, user, response):
    '''
    购物车合并


    # 链接 redis然后合并
    # 合并商品的数量以及被勾选的状态
    # 清除cookie商品的信息
    #删除ｃｏｏｋｉｅ中关于购物车的记录

    '''
    # 取出cookie中商品的数量以及被选择的状态
    cookie_cart = request.COOKIES.get('cart')
    """
    sku_id:{
        count:10,
        selected:True,
    }

    """
    # 没有添加过购物车
    if not cookie_cart:
        return response

    # 反解码
    # 解析cookie购物车数据
    cookie_cart = pickle.loads(base64.b64decode(cookie_cart.encode()))

    # 存放商品的信息
    cart = {}

    redis_cart_selected_add = []
    # 记录redis勾选状态中应该删除的sku_id
    redis_cart_selected_remove = []

    for sku_id, selected_cart in cookie_cart.items():
        # 区商品的数量
        cart[sku_id] = selected_cart['count']
        # 取状态
        '''
        sku_id :  true
        '''
        # 取出cookie中商品的状态
        if selected_cart['selected']:
            redis_cart_selected_add.append(sku_id)
        else:
            # 移除当前商品的被勾选状态
            redis_cart_selected_remove.append(sku_id)

    if cart:
        redis_conn = get_redis_connection('cart')
        pl = redis_conn.pipeline()
        # 添加商品的数量
        pl.hmset('cart_%s' % user.id, cart)
        if redis_cart_selected_add:
            pl.sadd('cart_selected_%s' % user.id, *redis_cart_selected_add)
        if redis_cart_selected_remove:
            pl.srem('cart_selected_%s' % user.id, *redis_cart_selected_remove)
        pl.execute()

        response.delete_cookie('cart')


    # 返回, 在登录页面使用
    return response



























