import json
import urllib.error
import urllib.parse
import urllib.request

import pygame

import api_urls
import model
import shared_data
import thread_actor
import utils
from thread_class import ThreadClass
from util import logs

log = logs.get_logger('playlist.py')


class PlaylistService(ThreadClass):
    model = None
    shared = None

    @classmethod
    def init(self):
        self.model = model.Model.instance()
        self.shared = shared_data.SharedData.instance()

        if self.model.get_data_info('playlist_id') is not None:
            if self.model.get_playlist_info(self.model.get_data_info('playlist_id')) is not None:
                thread_actor.send_message("changeplaylist|" + str(self.model.get_data_info('playlist_id')))
        if self.model.get_data_info('volume') is not None:
            thread_actor.send_message("changevolume|" + str(self.model.get_data_info('volume')))

    @classmethod
    def get_now_playlist(self):
        is_new = False
        try:
            if self.shared.api_base == "":
                raise urllib.error.URLError("no api base")
            url = api_urls.API_URL_GETSETTING
            if self.shared.member_id == 0:
                raise urllib.error.URLError("cannot find member id")

            params = {'member_id': self.shared.member_id}
            params_encoded = urllib.parse.urlencode(params).encode('UTF-8')
            url_connect = urllib.request.urlopen(url=url, data=params_encoded)
            rtn_data = url_connect.read().decode("utf-8")
            rtn_json = json.loads(rtn_data)

            if rtn_json['result']['ret'] == "success":
                api_data = rtn_json['data']
                data_list = api_data['list']

                old_playlist_id = self.model.get_data_info('playlist_id')
                old_volume = self.model.get_data_info('volume')

                for info in data_list:
                    if info['type'] == "nowPlaylist":
                        new_playlist_id = info['value']
                    if info['type'] == "volume":
                        new_volume = info['value']

                if new_playlist_id is not None:
                    pinfo = self.model.get_playlist_info(new_playlist_id)
                    if pinfo is not None:
                        if old_playlist_id is None:
                            thread_actor.send_message("changeplaylist|" + str(new_playlist_id))
                        else:
                            if int(old_playlist_id) != new_playlist_id:
                                thread_actor.send_message("changeplaylist|" + str(new_playlist_id))
                    else:
                        thread_actor.send_message("changeplaylist|" + str(self.model.get_playlist_default()[0]['id']))
                else:
                    thread_actor.send_message("changeplaylist|" + str(self.model.get_playlist_default()[0]['id']))

                if new_volume is not None:
                    if old_volume is None:
                        thread_actor.send_message("changevolume|" + str(new_volume))
                    elif int(old_volume) != new_volume:
                        thread_actor.send_message("changevolume|" + str(new_volume))
                else:
                    thread_actor.send_message("changeplaylist|9")

            else:
                if self.model.get_data_info('playlist_id') is None or self.model.get_data_info('volume') is None:
                    log.info("setting value are None, setting player default")
                    thread_actor.send_message("changeplaylist|" + str(self.model.get_playlist_default()[0]['id']))
                    thread_actor.send_message("changevolume|9")

        except urllib.error.URLError as e:
            log.info("fail to get setting")
            print(e)
            return False
        except urllib.error.HTTPError as e:
            log.info("fail to get setting")
            print(e)
            return False
        except Exception as e:
            log.info("fail to get setting")
            print(e)
            return False
        return is_new

    def run(self):
        # init block
        self.init()

        while not self.stopped():
            try:
                self.get_now_playlist()
                pygame.time.wait(60 * 1000)

            except KeyboardInterrupt:
                break

            except Exception as e:
                print(e)
                log.info("api loop error")
