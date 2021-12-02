import os
import time
import urllib.request

import pygame

import api_client
import env
import model
import shared_data
import thread_actor
import utils
from thread_class import ThreadClass
from util import logs

default_path = "./.cache"

log = logs.get_logger('downloader.py')


class Downloader(ThreadClass):
    model = None

    def run(self):
        log.info("downloader created")
        self.model = model.Model.instance()
        shared = shared_data.SharedData.instance()

        initial_down = False
        send_play = False
        while (not self.stopped()):
            try:
                current_playlist_id = shared.current_playlist_id
                current_cm_date = shared.current_cm_date
                active_music_files = []
                active_cm_files = []

                # 재생 예정인 음악 20개 다운로드하기
                if current_playlist_id:
                    active_musics = self.model.get_active_musics_limit(current_playlist_id, 20)
                    for music in active_musics:
                        id = music['id']
                        path = music['path']
                        route = music['route']
                        file = os.path.split(path)[-1]
                        active_music_files.append(file)
                        api_client.download(route, path)

                # 오늘 재생 예정인 CM 모두 다운로드하기
                if current_cm_date:
                    active_cms = self.model.get_active_cms(current_cm_date)
                    for cm in active_cms:
                        id = cm['id']
                        path = cm['path']
                        route = cm['route']
                        file = os.path.split(path)[-1]
                        active_cm_files.append(file)
                        api_client.download(route, path)

                initial_down = True
                player_status = thread_actor.send_message("player_status")
                if player_status == "not ready" or player_status == "stopped":
                    # if initial_down and not send_play:
                    send_play = True
                    thread_actor.send_message("play")
                    # break

                # clear inactive music & cm files
                if active_music_files:  # 네트워크 지연 등으로 활성화된 음악 정보를 늦게 가져올 수 있기 때문에, 활성화된 음악 목록이 있는 경우에만 불필요한 파일을 지운다.
                    for music_file in os.listdir(env.CACHE_MUSIC_DIR):
                        if not music_file in active_music_files:
                            music_path = os.path.join(env.CACHE_MUSIC_DIR, music_file)
                            log.info('delete inactive music file: %s', music_path)
                            os.remove(music_path)

                if active_cm_files: # 네트워크 지연 등으로 활성화된 음악 정보를 늦게 가져올 수 있기 때문에, 활성화된 음악 목록이 있는 경우에만 불필요한 파일을 지운다.
                    for cm_file in os.listdir(env.CACHE_CM_DIR):
                        if not cm_file in active_cm_files:
                            cm_path = os.path.join(env.CACHE_CM_DIR, cm_file)
                            log.info('delete inactive cm file: %s', cm_path)
                            os.remove(cm_path)

                pygame.time.delay(1000)

            except KeyboardInterrupt:
                break
            except Exception as e:
                log.warn('exception', exc_info=1)
                pygame.time.delay(1000 * 10)
