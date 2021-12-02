import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from subprocess import call

import pygame

import api_client
import api_urls
import downloader
import env
import model
import player
import playlist
import shared_data
import thread_actor
import utils
from thread_class import ThreadClass
from util import logs

log = logs.get_logger('api.py')


class ApiService(ThreadClass):
    model = None
    shared = None

    @classmethod
    def init(self):
        self.model = model.Model.instance()
        self.shared = shared_data.SharedData.instance()
        log.info('init')

    @classmethod
    def get_default_api_server(self):
        log.info('get_default_api_server')
        try:
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
            self.shared.api_base = "http://" + url_list[randnum]

            log.info("api url base is " + self.shared.api_base)
        except urllib.error.URLError as e:
            log.info("cannot find api server")
        except urllib.error.HTTPError as e:
            log.info("cannot find api server")
        except Exception as e:
            log.info("cannot find api server")

    @classmethod
    def signin(self):
        log.info('signin')
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_SIGNIN
            params = {'id': self.shared.userid, 'password': self.shared.instance().password}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)
            log.info('call API: url=%s, params=%s', url, params)
            log.info('API response: %s', rtn_data)

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                member_id = api_data['info']['member_id']
                self.shared.session_info = api_data['info']
                self.shared.member_id = self.shared.session_info['member_id']
                api_client.member_id = member_id
                self.model.set_data_info('member_id', self.shared.session_info['member_id'])
                self.shared.contract_state = self.shared.session_info['contract_state']
                version_str = str(self.shared.session_info['version_check'])
                self.shared.session_info['version_check'] = float(self.shared.session_info['version_check'])
                # print("signin success\nmember_id = ", self.shared.member_id, "\nold version is ", self.shared.version_check, "new version is ", self.shared.session_info['version_check'])
                log.info("signin success")
                log.info("member_id is " + str(self.shared.member_id))
                log.info("old version is " + str(self.shared.version_check) + " new version is " + str(
                    self.shared.session_info['version_check']))
                if self.shared.version_check < self.shared.session_info['version_check']:
                    self.upgrade(self.shared.session_info['version_check'])
                    return True
                else:
                    url = self.shared.api_base + api_urls.API_URL_LOGIN
                    params = {'member_id': self.shared.member_id, 'version': self.shared.version_check}
                    params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
                    url_connect = urllib.request.urlopen(url=url, data=params_encoded)
                    return True
            else:
                response_msg = rtn_json['result']['msg']
                log.warn("sign in failed: response_msg=%s", response_msg)
                return False
        except urllib.error.URLError as e:
            log.warn("signin fail: URLError")
            return False
        except urllib.error.HTTPError as e:
            log.warn("signin fail: HTTPError")
            return False
        except Exception as e:
            log.warn("signin fail", exc_info=1)
            return False

    @classmethod
    def upgrade(self, version):
        log.info('upgrade')
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_UPGRADE
            params = {'member_id': self.shared.member_id, "version": version}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                route = api_data['url']
                if route != "":
                    # service stop and upgrade do
                    call('chmod -R 755 ./upgrade.sh', shell=True)
                    call('./upgrade.sh ' + route, shell=True)
                    call('./stop.sh', shell=True)
            else:
                log.info('upgrade: response msg: %s', rtn_json['result']['msg'])
                return False
        except urllib.error.URLError as e:
            log.info("upgrade fail")
            return False
        except urllib.error.HTTPError as e:
            log.info("upgrade fail")
            return False
        except Exception as e:
            log.info("upgrade fail")
            return False

    @classmethod
    def get_playlist(self):
        # is_new = False
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_PLAYLIST
            if self.shared.member_id == 0:
                raise urllib.error.URLError("cannot find member id")

            params = {'member_id': self.shared.member_id}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                new_playlist_list = api_data['list']
                if not new_playlist_list:
                    new_playlist_list = []
                log.info('get_playlist: %s', len(new_playlist_list))
                new_playlists = []

                # 가장 첫번째 플레이리스트를 별도로 저장했다가 channel이 선택되지 않은 경우의 기본값으로 활용한다.
                if new_playlist_list:
                    default_playlist = new_playlist_list[0]
                    default_playlist_id = default_playlist['playlist_id']
                    log.info('get_playlist: set default_playlist_id=%s', default_playlist_id)
                    self.model.set_data_info(model.DATA_KEY_DEFAULT_PLAYLIST_ID, default_playlist_id)

                for this_playlist_info in new_playlist_list:
                    playlist_id = this_playlist_info['playlist_id']
                    new_playlists.append(playlist_id)
                    existing_playlist_info = self.model.get_playlist_info(playlist_id)
                    if not existing_playlist_info:
                        log.info(str(this_playlist_info['playlist_id']) + ' is binded, insert data')
                        self.model.set_playlist_info(
                            playlist_id=this_playlist_info['playlist_id'],
                            title=this_playlist_info['title'],
                            mood=this_playlist_info['mood'],
                            mod_ts=this_playlist_info['mod_ts'],
                            new_count=this_playlist_info['new_count']
                        )
                        self.get_playlist_detail_by_playlist_id(playlist_id)
                    else:
                        update_playlist = False
                        if existing_playlist_info['count'] <= 0:
                            log.info('update existing playlist because count <= 0')
                            update_playlist = True
                        if existing_playlist_info['mod_ts'] != this_playlist_info['mod_ts']:
                            log.info('update existing playlist because mod_ts is changed')
                            update_playlist = True

                        if update_playlist:
                            log.info(str(this_playlist_info['playlist_id']) + ' is updated, update data')
                            self.model.set_playlist_info(
                                playlist_id=this_playlist_info['playlist_id'],
                                title=this_playlist_info['title'],
                                mood=this_playlist_info['mood'],
                                mod_ts=this_playlist_info['mod_ts'],
                                new_count=this_playlist_info['new_count']
                            )
                            self.get_playlist_detail_by_playlist_id(playlist_id)
                            if str(playlist_id) == self.model.get_data_info('playlist_id'):
                                player.Player.player_setting()

                old_playlist_list = self.model.get_playlist_info_all()

                for this_playlist_info in old_playlist_list:
                    if this_playlist_info['id'] not in new_playlists:
                        log.info(str(this_playlist_info['id']) + ' is unbinded, start delete playlist info')
                        self.model.del_playlist_info(this_playlist_info['id'])
                        self.model.remove_musics(this_playlist_info['id'])
                        playlist.PlaylistService.get_now_playlist()

            else:
                log.info(rtn_json['result']['msg'])
        except urllib.error.URLError as e:
            log.warn("fail to get playlist: URLError")
            return False
        except urllib.error.HTTPError as e:
            log.warn("fail to get playlist: HTTPError")
            return False
        except Exception as e:
            log.error("fail to get playlist", exc_info=1)
            return False
        # return is_new

    @classmethod
    def get_playlist_detail(self, playlist_id):
        log.info('get_playlist_detail: playlist_id=%s', playlist_id)
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_PLAYLIST_DETAIL

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

    @classmethod
    def get_playlist_detail_by_playlist_id(self, playlist_id):
        log.info('get_playlist_detail_by_playlist_id: playlist_id=%s', playlist_id)
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_PLAYLIST_DETAIL

            params = {'playlist_id': playlist_id}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)
            playlist_info = self.model.get_playlist_info(playlist_id)
            mod_ts = datetime.strptime(playlist_info['mod_ts'], "%Y-%m-%d %H:%M:%S")
            start = datetime.strptime(playlist_info['mod_ts'], "%Y-%m-%d %H:%M:%S")
            start_at = 0
            timestamp = str(time.mktime(utils.getNow().timetuple()))

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                music_list = api_data['list']
                self.model.remove_musics(playlist_id)
                musics = []
                for idx, music in enumerate(music_list):
                    id = str(playlist_id) + ':' + str(idx)
                    music_id = music['music_id']
                    pt = datetime.strptime(music['duration'], '%H:%M:%S')
                    real_duration = pt.second + pt.minute * 60 + pt.hour * 3600
                    title = music['title']
                    artist_name = music['artist_name']
                    route = music['route']
                    duration = music['duration']
                    end_at = start_at + real_duration
                    path = os.path.join(env.CACHE_MUSIC_DIR, str(music['music_id']) + ".dat")
                    musics.append(
                        (id, music_id, playlist_id, idx, title, artist_name, route,
                         duration, real_duration, path, start_at, end_at)
                    )
                    start_at = end_at
                self.model.put_music_list(musics)
                self.model.update_count(len(music_list), playlist_id)
                log.info('put musics: %s', len(musics))

                total_duration = start_at
                log.info("total number of songs is " + str(len(music_list)))
                log.info("total duration is " + str(total_duration))
                self.model.set_playlist_total_duration(playlist_id, total_duration)

            else:
                log.info(rtn_json['result']['msg'])

            return True
        except urllib.error.URLError as e:
            log.info("fail to get playlist detail")
            return False
        except urllib.error.HTTPError as e:
            log.info("fail to get playlist detail")
            return False
        except Exception as e:
            log.info("fail to get playlist detail")
            return False

    @classmethod
    def get_cmlist(self):
        log.info('get_cmlist')
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = self.shared.api_base + api_urls.API_URL_CMLIST
            if self.shared.member_id == 0:
                log.info("member id not correct")
                return
            weekday = utils.getNow().strftime('%a').upper()
            dt = utils.getNow().strftime("%Y-%m-%d")
            self.shared.cm_date = dt
            self.model.set_data_info('cm_date', dt)
            params = {'member_id': self.shared.member_id, 'date': dt, 'weekday': weekday}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)

            cm_list = []
            cm_data = []

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                cm_list = api_data['list']
                if not cm_list:
                    cm_list = []
                log.info("cm length is " + str(len(cm_list)))
            else:
                log.warn(rtn_json['result'])

            cm_length = len(cm_list)
            for idx, cm in enumerate(cm_list):
                pt = datetime.strptime(cm['duration'], '%H:%M:%S')
                real_duration = pt.second + pt.minute * 60 + pt.hour * 3600
                real_at = dt + " " + cm['time']
                start = datetime.strptime(real_at, "%Y-%m-%d %H:%M:%S")
                real_end_dt = start + timedelta(seconds=real_duration)
                real_end = real_end_dt.strftime("%Y-%m-%d %H:%M:%S")
                path = os.path.join(env.CACHE_CM_DIR, str(cm['cm_id']) + ".dat")
                date = dt
                id = str(idx)
                cm_id = cm['cm_id']
                type = cm['type']
                cm_info = cm['cm_info']
                time = cm['time']
                wait_num = cm['wait_num']
                route = cm['route']
                duration = cm['duration']
                real_duration = real_duration
                path = path
                real_at = real_at
                real_end = real_end
                cm_data.append(
                    (id, cm_id, date, type, cm_info, time, wait_num, route, duration, real_duration, path,
                     real_at, real_end, idx)
                )

            log.info('CM 목록 갱신 및 이전 목록 삭제: len(cm_list)=%s', cm_length)
            self.model.put_cm_list(cm_data)
            self.model.delete_cm_from_idx(cm_length)
            shared_data.SharedData.instance().reset_networkfail_counter()

            return True
        except urllib.error.HTTPError as e:
            log.warn("url error")
            shared_data.SharedData.instance().add_networkfail_counter()
            return False
        except urllib.error.URLError as e:
            log.warn("url error")
            shared_data.SharedData.instance().add_networkfail_counter()
            return False
        except Exception as e:
            log.warn("cm error", exc_info=1)
            shared_data.SharedData.instance().add_networkfail_counter()
            return False

    @classmethod
    def get_chime(self):
        chime_up_mp3 = os.path.join(env.TTS_DIR, 'chime_up.mp3')
        if not os.path.exists(chime_up_mp3) or os.path.getsize(chime_up_mp3) == 0:
            os.system(
                'wget http://cdn2.rhymeduck.com/chime_up.mp3 '
                '-P ' + env.TTS_DIR + ' '
                                      '--no-check-certificate'
            )

    @classmethod
    def get_tts(self):
        log.info('get_tts')
        try:
            url = api_urls.API_URL_TTSONCE
            if self.shared.member_id == 0:
                log.info("member id not correct")
                return

            dt = utils.getNow().strftime("%Y-%m-%d")
            self.shared.cm_date = dt

            params = {'member_id': self.shared.member_id}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)
            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                url = api_data['url']
                download_cnt = 0
                filename = 'tts' + "_" + str(self.shared.cm_date) + "_" + utils.getNow().strftime("%H:%M:%S") + ".dat"
                path = os.path.join(env.CACHE_CM_DIR, filename)
                api_client.download(url, path)

                while not os.path.exists(path):
                    if download_cnt > 10:
                        log.info("TTS download error")
                        break;
                    else:
                        download_cnt += 1
                        api_client.download(url, path)

                if os.path.exists(path):
                    duration = "00:00:10"  # dummy data. but it plays to the end
                    real_duration = 10
                    real_delay = 3

                    tts_reg = utils.getNow()
                    while os.path.exists("./model.db-journal"):
                        if (tts_reg + timedelta(seconds=10) < utils.getNow()):
                            log.info("TTS Time out")
                            break
                        else:
                            pygame.time.delay(1000)
                    if not os.path.exists("./model.db-journal"):
                        db_reg = utils.getNow()
                        real_at_dt = db_reg + timedelta(seconds=real_delay)
                        real_at = real_at_dt.strftime("%Y-%m-%d %H:%M:%S")
                        real_end_dt = real_at_dt + timedelta(seconds=real_duration)
                        real_end = real_end_dt.strftime("%Y-%m-%d %H:%M:%S")

                        if real_end_dt > utils.getNow():
                            idx = -1
                            id = str(dt) + ':' + str(idx)
                            self.model.put_tts(
                                id=id,
                                idx=idx,
                                date=dt,
                                cm_id=None,
                                type=0,
                                cm_info=None,
                                time=real_at,
                                wait_num=1,
                                route=url,
                                duration=duration,
                                real_duration=real_duration,
                                path=path,
                                real_at=real_at,
                                real_end=real_end,
                            )

                    shared_data.SharedData.instance().reset_networkfail_counter()

            else:
                log.info(rtn_json['result']['msg'])
                return True

        except urllib.error.HTTPError as e:
            log.info("url error")
            shared_data.SharedData.instance().add_networkfail_counter()
            return False
        except urllib.error.URLError as e:
            log.info("url error")
            shared_data.SharedData.instance().add_networkfail_counter()
            return False
        except Exception as e:
            log.info("Get TTS info fail")
            return False

    @classmethod
    def set_teamviewer_id(self):
        try:
            url = api_urls.API_URL_TEAMVIEWER
            tvid = subprocess.check_output("teamviewer info | grep 'TeamViewer ID:' | tail -1 | awk {'print $5'}",
                                           shell=True).decode('utf-8').split('\n')[0]
            params = {'member_id': self.shared.member_id, 'teamviewer_id': tvid}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)

            if rtn_json['result']['ret'] == "success":
                log.info(rtn_json['result']['msg'])
            else:
                log.info(rtn_json['result']['msg'])

        except urllib.error.URLError as e:
            log.info("TeamViewer id Setting fail")
            return False
        except urllib.error.HTTPError as e:
            log.info("TeamViewer id Setting fail")
            return False
        except Exception as e:
            log.info("TeamViewer id Setting fail")
            return False

    def run(self):
        # init block
        self.init()
        self.get_default_api_server()
        is_signin = self.signin()
        self.set_teamviewer_id()

        while not is_signin:
            pygame.time.wait(60 * 1000)
            self.get_default_api_server()
            is_signin = self.signin()

        shared_data.SharedData.instance().signed = True
        init = True
        log.info('sign in success and initialized')
        api_client.log_login()

        while not self.stopped():
            try:
                if not init:
                    pygame.time.wait(10 * 60 * 1000)
                    if self.stopped():
                        break

                old_date = self.shared.cm_date
                cm_ready = self.get_cmlist()
                new_date = self.shared.cm_date

                self.get_playlist()

                if init:
                    init = False
                    thread_actor.send_message("playlist_checker_start")

                if cm_ready:
                    shared_data.SharedData.instance().list_ready = True

            except KeyboardInterrupt:
                break

            except Exception as e:
                log.info("api loop error")
                log.warn('exception', exc_info=1)
