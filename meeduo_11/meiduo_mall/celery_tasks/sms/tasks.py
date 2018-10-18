from meiduo_mall.libs.yuntongxun.sms import CCP
from celery_tasks.main import celery_app

from meiduo_mall.apps.verifications import constants




@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, code):
    ccp = CCP()
    ccp.send_template_sms(mobile, code, constants.SMS_CODE_TEMPLATE_ID)



