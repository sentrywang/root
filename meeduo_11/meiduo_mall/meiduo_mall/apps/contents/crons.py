from django.template import loader
from django.conf import settings
import os
from collections import OrderedDict
from .models import ContentCategory
from goods.models import GoodsChannel

def generate_static_index_html():
    # 取出要静态化的数据
    # 广告数据
    contegories = {}
    content_categories = ContentCategory.objects.all()
    for cont in content_categories:
        contegories[cont.key] = cont.content_set.filter(status = True).order_by('sequence')
    # 分类数据
    # OrderedDict把字典按照key的序列号进行排序
    # {
    #   1： ’xxx’,
    #   2:  'asd'
    # }
    categories = OrderedDict()
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        group_id = channel.group_id  # 当前组
        # 如果当前组没有子类别，就添加
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        #有子类别
        cat1 = channel.category  # 当前频道的类别

        # 追加当前频道
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url # 以及类别的ｕｒｌ
        })
        # 构建当前类别的子类别
        # 获取二级类别
        for cat2 in cat1.goodscategory_set.all():
            cat2.sub_cats = []
            # 获取商品的三级类别信息，　ｓｐｕ
            for cat3 in cat2.goodscategory_set.all():
                cat2.sub_cats.append(cat3)
            categories[group_id]['sub_cats'].append(cat2)

    # 渲染数据，到模板
    context = {
        'contents': contegories, # 广告数据
        'categories': categories   # 商品类别
    }
    # 得到模板
    temp_html = loader.get_template('index.html')
    html_text = temp_html.render(context)
    # 把渲染好的页面，写道单独的文件中
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)

