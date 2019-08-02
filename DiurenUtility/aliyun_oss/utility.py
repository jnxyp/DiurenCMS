import base64
import datetime
import hmac
import json
import time
from hashlib import sha1 as sha

import oss2
# from django.conf import settings

from durian_cms import settings

auth = oss2.Auth(settings.ALIYUN_OSS_STORAGE['ACCESS_KEY_ID'],
                 settings.ALIYUN_OSS_STORAGE['ACCESS_KEY_SECRET'])
bucket = oss2.Bucket(auth, settings.ALIYUN_OSS_STORAGE['END_POINT'],
                     settings.ALIYUN_OSS_STORAGE['BUCKET_NAME'])


def get_signed_url(object_path: str, method: str = 'GET', expires: int = 5 * 60, headers=None,
                   params=None):
    return bucket.sign_url(method.upper(), object_path, expires, headers, params)


# Author: Aliyun
# https://help.aliyun.com/document_detail/31927.html?spm=a2c4g.11186623.2.10.79944367FPfoMP#concept-qp2-g4y-5db

# Modified by jn_xyp@2019-07-19

def _get_iso_8601(expire):
    gmt = datetime.datetime.utcfromtimestamp(expire).isoformat()
    gmt += 'Z'
    return gmt


def get_token(object_path: str, expires: int = 5 * 60, callback_url: str = None):
    now = int(time.time())
    expire_syncpoint = now + expires
    expire = _get_iso_8601(expire_syncpoint)

    policy_dict = {'expiration': expire}
    condition_array = []
    array_item = ['starts-with', '$key', object_path]
    condition_array.append(array_item)
    policy_dict['conditions'] = condition_array
    policy = json.dumps(policy_dict).strip()
    policy_encode = base64.b64encode(policy.encode())
    h = hmac.new(settings.ALIYUN_OSS_STORAGE['ACCESS_KEY_SECRET'].encode(), policy_encode, sha)
    sign_result = base64.encodebytes(h.digest()).strip()

    token_dict = {'accessid': settings.ALIYUN_OSS_STORAGE['ACCESS_KEY_ID'],
                  'host': settings.ALIYUN_OSS_STORAGE['END_POINT'],
                  'policy': policy_encode.decode(),
                  'signature': sign_result.decode(),
                  'expire': expire_syncpoint,
                  'dir': object_path}

    if callback_url:
        callback_dict = {'callbackUrl': callback_url,
                         'callbackBody': 'filename=${object}&size=${size}',
                         'callbackBodyType': 'application/x-www-form-urlencoded'}
        callback_param = json.dumps(callback_dict).strip()
        base64_callback_body = base64.b64encode(callback_param.encode())
        token_dict['callback'] = base64_callback_body.decode()

    result = json.dumps(token_dict)
    return result


if __name__ == '__main__':
    print(bucket.object_exists('media/'))
