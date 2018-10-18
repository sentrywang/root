from celery import Celery


# 为celery使用django配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'


# 实例化
celery_app = Celery('meiduo_mall')


#　配置文件
celery_app.config_from_object('celery_tasks.config')

# 接受任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.html'])



