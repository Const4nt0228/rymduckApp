import json
import logging
import os
import random
import sys
import time
import urllib.request
import urllib.parse
from logging.handlers import TimedRotatingFileHandler
from urllib.error import URLError

import api_urls
import env
import utils

member_id = None

log = logging.getLogger('api_client.py')
log.setLevel(env.LOG_LEVEL)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(env.LOG_FORMATTER)
file_handler = TimedRotatingFileHandler(env.LOG_FILE, when='D')
file_handler.setFormatter(env.LOG_FORMATTER)
log.addHandler(console_handler)
log.addHandler(file_handler)


class Response:
    def __init__(self,
                 success: bool,
                 result: dict,
                 data: dict
                 ):
        self.success = success
        self.result = result
        self.data = data


def __call_post(
        url: str,
        data: dict
):
    success = False
    response = ''
    res_result = {}
    res_data = {}
    try:
        data_encoded = urllib.parse.urlencode(data).encode('UTF-8')
        req = urllib.request.Request(url=url, data=data_encoded)
        res = urllib.request.urlopen(req)
        rtn_data = res.read().decode("utf-8")
        response = rtn_data
        log.debug('API called: url=%s, data=%s, response=%s', url, data, rtn_data)
        rtn_json = json.loads(rtn_data)
        if rtn_json:
            res_result = rtn_json.get('result')
            res_data = rtn_json.get('data')
            if res_result:
                ret = res_result.get('ret')
                if ret == "success":
                    success = True
        if not success:
            log.warn('API call failed: url=%s, data=%s, response=%s', url, data, response)
    except URLError:
        log.warn('API call failed with URLError: url=%s, data=%s', url, data)
        success = False
    except:
        log.warn('API call failed: url=%s, data=%s', url, data, exc_info=1)
        success = False

    return Response(success=success, result=res_result, data=res_data)


def download(url, filename):
    try:
        # if not os.path.exists(filename):
        if os.path.exists(filename):
            log.debug('download: skip download. file already exist. url=%s, filename=%s', url, filename)
            return True
        log.info('download: start. url=%s, filename=%s', url, filename)
        url_request = urllib.request.Request(url)
        url_connect = urllib.request.urlopen(url_request)

        buffer_size = 4096 * 2

        timestamp = str(time.mktime(utils.getNow().timetuple()))
        filename_only = str(os.path.split(filename)[-1])
        tmp_filename = os.path.join(env.CACHE_DIR, "downloader_tmp_" + str(timestamp) + '_' + filename_only)
        with open(tmp_filename, 'wb') as f:
            while True:
                buffer = url_connect.read(buffer_size)
                if not buffer: break
                # an integer value of size of written data
                data_wrote = f.write(buffer)

        # you could probably use with-open-as manner
        url_connect.close()
        utils.encrypt_file("vodkaraspberrypi", tmp_filename, filename)
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
        # else:
        #     print("file exists")
        return True
    except:
        log.warn('download fail: url=%s, filename=%s', url, filename)
        return False


def get_default_api_server():
    log.info('get_default_api_server')
    url = api_urls.API_URL_FIND_BASE
    url_request = urllib.request.Request(url)
    url_connect = urllib.request.urlopen(url_request)

    data = url_connect.read().decode("utf-8")
    # url_list = data.split('\n')
    url_list = data.splitlines()
    for url_str in url_list:
        if url_str == "":
            url_list.remove(url_str)
    randnum = random.randrange(0, len(url_list))
    return "http://" + url_list[randnum]


def get_playlist_detail(api_base: str, playlist_id):
    log.info('get_playlist_detail: playlist_id=%s', playlist_id)
    try:
        url = api_base + api_urls.API_URL_PLAYLIST_DETAIL
        params = {'playlist_id': playlist_id}
        params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
        url_connect = urllib.request.urlopen(url=url, data=params_encoded)
        rtn_data = url_connect.read().decode("utf-8")
        rtn_json = json.loads(rtn_data)
        if rtn_json['result']['ret'] == "success":
            return rtn_json['data']['list']
    except:
        log.warn('get_playlist_detail: playlist_id={playlist_id}', exc_info=1)
        pass
    return []


def health_check() -> bool:
    global member_id
    if member_id:
        url = 'https://stbapi.rhymeduck.com/a/v1/member/recent_connect'
        data = {'member_id': member_id}
        response = __call_post(url, data)
        return response.success
    else:
        log.warn('health_check failed. member_id is None')
        return False


def get_health_check_interval() -> [int]:
    global member_id
    url = 'https://stbapi.rhymeduck.com/a/v1/member/recent_connect_period'
    data = {'member_id': member_id}
    response = __call_post(url, data)
    period = None
    if response.success and response.data:
        period = response.data
    if not period:
        period = []
    return period


def log_song(music_id):
    global member_id
    if member_id:
        url = 'http://log.rhymeduck.com/a/v1/logsong'
        data = {'member_id': member_id, 'music_id': music_id}
        response = __call_post(url, data)
        return response.success
    else:
        log.warn('log_song failed. member_id is None')
        return False


def log_channel(playlist_id):
    global member_id
    if member_id:
        url = 'http://log.rhymeduck.com/a/v1/logchannel'
        data = {'member_id': member_id, 'playlist_id': playlist_id}
        response = __call_post(url, data)
        return response.success
    else:
        log.warn('log_channel failed. member_id is None')
        return False


def log_login():
    global member_id
    if member_id:
        url = 'http://log.rhymeduck.com/a/v1/loglogin'
        data = {'member_id': member_id}
        response = __call_post(url, data)
        return response.success
    else:
        log.warn('log_login failed. member_id is None')
        return False


def log_error(error_code, error_msg):
    global member_id
    if member_id:
        url = 'http://log.rhymeduck.com/a/v1/logerror'
        data = {'member_id': member_id, 'error_code': error_code, 'error_msg': error_msg}
        response = __call_post(url, data)
        return response.success
    else:
        log.warn('log_error failed. member_id is None')
        return False
