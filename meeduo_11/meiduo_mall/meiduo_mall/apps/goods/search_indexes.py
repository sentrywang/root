from haystack import indexes
from .models import SKU

class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    '''
    创建商品的索引模型类
    '''
    #  document=True指定text是索引的关键词
    # use_template 是在模板中指定索引的关键词的字段
    text =  indexes.CharField(document=True, use_template=True)

    def get_model(self):
        '''
        指明建立索引的模型类表
        :return:
        '''
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集"""
        return self.get_model().objects.filter(is_launched=True)












