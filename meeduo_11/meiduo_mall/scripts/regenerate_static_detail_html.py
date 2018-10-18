#!/usr/bin/env python

import sys
# 找到脚本的上级目录
sys.path.insert(0, '../')

import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

 # 让django进行初始化设置
import django
django.setup()

from goods.models import SKU
from django.template import loader
from goods.utils import get_categories
from django.conf import settings


'''
商品详情页面的静态化脚本
'''
def generate_static_detail_html(sku_id):
    '''
    异步生成静态化页面
    sku_id : 当前商品的ｉｄ
    '''

    # 商品分类信息的静态化
    categories = get_categories()

    # 当前商品信息
    sku = SKU.objects.get(id=sku_id)

    # 获取商品面包屑导航栏的信息
    goods = sku.goods
    goods.channel = goods.category1.goodschannel_set.all()[0]

    # 构建当前商品的规格键
    # sku_key = [规格1参数id， 规格2参数id， 规格3参数id, ...]
    # 获取当前商品的规格值
    sku_specs = sku.skuspecification_set.order_by('spec_id')
    sku_key = []
    for spec in sku_specs:
        sku_key.append(spec.option.id)


    # 获取当前商品的所有SKU
    skus = goods.sku_set.all()

    # 构建不同规格参数（选项）的sku字典
    # spec_sku_map = {
    #     (规格1参数id, 规格2参数id, 规格3参数id, ...): sku_id,
    #     (规格1参数id, 规格2参数id, 规格3参数id, ...): sku_id,
    #     ...
    # }
    spec_sku_map = {}
    for s in skus:
        # 获取sku的规格参数
        s_specs = s.skuspecification_set.order_by('spec_id')
        # 用于形成规格参数-sku字典的键
        key = []
        for spec in s_specs:
            key.append(spec.option.id)
        # 向规格参数-sku字典添加记录
        spec_sku_map[tuple(key)] = s.id

    specs = goods.goodsspecification_set.order_by('id')
    # 若当前sku的规格信息不完整，则不再继续
    if len(sku_key) < len(specs):
        return

    # 获取当前商品的具体的规格信息，　
    for index, spec in enumerate(specs):
        # 复制当前sku的规格键
        key = sku_key[:]
        # 该规格的选项
        options = spec.specificationoption_set.all()
        for option in options:
            # 在规格参数sku字典中查找符合当前规格的sku
            key[index] = option.id
            option.sku_id = spec_sku_map.get(tuple(key))

        spec.options = options



    # 页面渲染
    context = {
        'categories': categories,
        'goods': goods,
        'specs': specs,
        'sku': sku
    }

    # 通过模板渲染


    template = loader.get_template('detail.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/'+str(sku_id)+'.html')
    with open(file_path, 'w') as f:
        f.write(html_text)

if __name__ == '__main__':
    # 取出所有的商品
    skus = SKU.objects.all()
    for sku in skus:
        print(sku.id)
        generate_static_detail_html(sku.id)
