import os
import time
from datetime import datetime

import pygame

import api_client
import env
import model
import shared_data
import utils
from thread_class import ThreadClass
from util import logs

log = logs.get_logger('player.py')


class Player(ThreadClass):
    act_index = 0
    is_on = False
    model = None
    current = {"type": "", "id": 0}

    model = None
    shared = None

    current_cm_date = None
    current_playlist_id = 0
    current_volume = 0

    playlist_info = {}
    mod_ts = None
    total_duration = 0

    list_check_count = 0

    last_recover_music_index = -1
    recovering = False  # 현재 비상음원 재생 중인지 여부

    @classmethod
    def init(self):
        self.model = model.Model.instance()
        self.shared = shared_data.SharedData.instance()
        self.recovering = False
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

    @classmethod
    def prepare_music(cls, path):
        for file in os.listdir(env.CACHE_DIR):
            if file.endswith('mp3'):
                os.remove(os.path.join(env.CACHE_DIR, file))
            if file.endswith('ogg'):
                os.remove(os.path.join(env.CACHE_DIR, file))

        timestamp = str(time.mktime(utils.getNow().timetuple()))
        current_music = os.path.join(env.CACHE_DIR, "current_" + str(timestamp) + ".mp3")
        success = utils.decrypt_file("vodkaraspberrypi", path, current_music)
        if success:
            try:
                import pydub
                current_music_occ = '.'.join(current_music.split('.')[:-1]) + '.ogg'
                log.debug('prepared_path_ogg: %s', current_music_occ)
                pydub.AudioSegment.from_mp3(current_music).export(current_music_occ, format='ogg')
                current_music = current_music_occ
            except:
                log.debug('Can not convert mp3 to ogg', exc_info=1)
            log.debug('prepare_music: result=%s', current_music)
            return current_music
        else:
            log.info('prepare_music: decrypt failed. remove broken file: %s', path)
            os.remove(path)
            return ""

    @classmethod
    def prepare_tts(self):
        chime_up_mp3 = os.path.join(env.TTS_DIR, 'chime_up.mp3')
        if not os.path.exists(chime_up_mp3) or os.path.getsize(chime_up_mp3) == 0:
            os.system(
                'wget http://cdn2.rhymeduck.com/chime_up.mp3 '
                '-P ' + env.TTS_DIR + ' '
                '--no-check-certificate'
            )
        try:
            import pydub
            chime_up_ogg = '.'.join(chime_up_mp3.split('.')[:-1]) + '.ogg'
            log.debug('prepared_tts_ogg: %s', chime_up_ogg)
            pydub.AudioSegment.from_mp3(chime_up_mp3).export(chime_up_ogg, format='ogg')
            chime_up_mp3 = chime_up_ogg
        except:
            log.debug('Can not convert mp3 to ogg', exc_info=1)
        pygame.mixer.music.load(chime_up_mp3)
        pygame.mixer.music.play(0)
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.time.wait(500)

    @classmethod
    def stop_music(self):
        if (self.is_on):
            self.is_on = False
            self.act_index = self.act_index + 1
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(1000)
                pygame.time.wait(1000)
                pygame.mixer.music.stop()

    @classmethod
    def terminate_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(1000)
            pygame.time.wait(1000)
            pygame.mixer.music.stop()
        self.current = {"type": "", "id": 0}

    @classmethod
    def terminate(self):
        log.info("player stop!!!")
        self.terminate_music()
        if self._stop_event:
            self._stop_event.set()

    @classmethod
    def player_setting(self):
        if self.shared is None and self.model is None:
            log.info('player_setting: init')
            self.init()
        else:
            if self.shared.cm_date == "":
                self.current_cm_date = self.model.get_data_info('cm_date')
            else:
                self.current_cm_date = self.shared.cm_date

            # set playlist_id
            self.current_playlist_id = self.shared.playlist_id
            if not self.current_playlist_id:
                self.current_playlist_id = self.model.get_data_info('playlist_id')
                if self.current_playlist_id:
                    log.info('player_setting: set current_playlist_id from DB = %s', self.current_playlist_id)
            if self.current_playlist_id and not self.model.get_playlist_info(self.current_playlist_id):
                log.info('player_setting: playlist is not exist in DB: %s', self.current_playlist_id)
                self.current_playlist_id = None
            if not self.current_playlist_id:
                self.current_playlist_id = self.model.get_data_info(model.DATA_KEY_DEFAULT_PLAYLIST_ID)
                if self.current_playlist_id:
                    log.info('player_setting: set current_playlist_id from default_playlist_id = %s', self.current_playlist_id)

            # set volume
            self.current_volume = self.shared.volume
            if not self.current_volume:
                log.info('player_setting: set current_volume as default value')
                self.current_volume = 9

            self.playlist_info = self.model.get_playlist_info(self.current_playlist_id)
            if self.playlist_info:
                self.mod_ts = datetime.strptime(self.playlist_info['mod_ts'], "%Y-%m-%d %H:%M:%S")
                self.total_duration = self.playlist_info['total_duration']
            else:
                pass

            if self.current_volume == "0":
                nomalize = 0
            else:
                nomalize = 70 + int(self.current_volume) * 3
            os.system('sudo amixer cset numid=1 ' + str(nomalize) + '%')

            # Update shared data
            self.shared.current_playlist_id = self.current_playlist_id
            self.shared.current_cm_date = self.current_cm_date

            log.info(
                'player_setting done: '
                'current_cm_date=%s, '
                'current_playlist_id=%s, '
                'current_volume=%s, '
                'playlist_info=%s, '
                'mod_ts=%s, '
                'total_duration=%s, '
                'normalize=%s',
                self.current_cm_date,
                self.current_playlist_id,
                self.current_volume,
                self.playlist_info,
                self.mod_ts,
                self.total_duration,
                nomalize
            )
            if self.shared.member_id:
                api_client.log_channel(self.current_playlist_id)

    def get_recover_music(self) -> str:
        """
        호출할 때마다 비상음원을 순차적으로 리턴한다.
        :return:
        """
        recover_musics = os.listdir(env.RECOVER_MUSIC_DIR)
        if recover_musics:
            recover_music_count = len(recover_musics)
            this_recover_music_index = (self.last_recover_music_index + 1) % recover_music_count
            self.last_recover_music_index = this_recover_music_index
            this_file = recover_musics[this_recover_music_index]
            this_path = os.path.join(env.RECOVER_MUSIC_DIR, this_file)
            return this_path
        else:
            return None

    def play_recover_music(self):
        music_path = self.get_recover_music()
        self.recovering = True
        if music_path:
            log.info('Play recover music: %s', music_path)
            prepared_path = self.prepare_music(music_path)
            if utils.file_is_valid(prepared_path):
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(1000)
                    pygame.time.wait(1000)
                pygame.mixer.music.load(prepared_path)
                pygame.mixer.music.play(start=0)
            else:
                log.error('recover music path is invalid: path=%s', music_path)
        else:
            log.error('Recover music is not found')

    def run(self):
        log.info("run: starts")
        self.act_index = self.act_index + 1
        my_index = self.act_index
        self.init()
        self.player_setting()
        cm_failure = 0
        music_failure = 0
        failure_count = 0

        while not self.stopped():
            try:
                pygame.time.wait(1000)
                if self.stopped():
                    self.is_on = False
                    break
                cm_list = self.model.get_active_cms_intime(self.current_cm_date, 3)
                music_list = self.model.get_active_musics_intime(self.current_playlist_id, 3)
                if cm_list:
                    active_cm = cm_list[0]
                else:
                    active_cm = None
                if music_list:
                    active_music = music_list[0]
                else:
                    active_music = None

                if failure_count > 5:
                    failure_count = 0
                    self.play_recover_music()

                elif self.recovering:
                    if pygame.mixer.music.get_busy():
                        # Keep playing recover music
                        continue
                    else:
                        self.player_setting()  # player setting 재시도하여 정상화 시도
                        self.recovering = False

                elif active_cm:
                    self.is_on = True
                    cm = active_cm

                    if self.current['type'] == "cm" and self.current['id'] == cm['id']:
                        # Keep playing cm
                        continue
                    else:
                        log.info('Play cm: start play. cm=%s', cm)

                        #cm[] 문자열가지고 시간으로 만들어줌
                        cm_real_time = datetime.strptime(cm['real_at'], "%Y-%m-%d %H:%M:%S")
                        path = cm['path'] or ''

                        # 서버에서 음원을 못받아왔다는거, failure_count 올리고 5초과시 복구작업
                        if not os.path.exists(path) or os.path.getsize(path) == 0:
                            log.debug('File is None or empty: path=%s', path)
                            failure_count += 1
                            pygame.time.wait(1000)
                            continue
                        prepared_path = self.prepare_music(path)


                        if utils.file_is_valid(prepared_path):
                            now = utils.getNow()
                            secs = int((now - cm_real_time).total_seconds())
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.fadeout(1000)
                                pygame.time.wait(1000)
                                secs += 1
                            if '/tts_' in path:
                                self.prepare_tts()
                                secs = 0
                            pygame.mixer.music.load(prepared_path)
                            pygame.mixer.music.play(start=secs)
                            self.current['type'] = "cm"
                            self.current['id'] = cm['id']
                            log.info('Play cm success: %s', cm["id"])
                            api_client.log_song(cm['cm_id'])
                            failure_count = 0
                        else:
                            log.warn("CM's prepared_path is not valid: %s", prepared_path)
                            failure_count += 1
                            pygame.time.wait(1000)
                            continue

                elif active_music:
                    self.is_on = True
                    music = active_music
                    now = utils.getNow()
                    if self.current['type'] == "music" and self.current['id'] == music['id']:
                        continue
                    elif pygame.mixer.music.get_busy() and self.current['type'] == "cm":
                        log.info("CM is playing. Wait playing music until CM is done")
                        continue
                    else:
                        log.info('Play music: start play. music=%s', music)
                        if self.total_duration == 0:
                            log.warn("playlist_len>0, total_duration=0)")
                            continue
                        if not os.path.exists(music['path']) or os.path.getsize(music['path']) == 0:
                            failure_count += 1
                            pygame.time.wait(1000)
                            continue
                        prepared_path = self.prepare_music(music['path'])


                        if utils.file_is_valid(prepared_path):
                            secs = int((now - self.mod_ts).total_seconds() % self.total_duration) - int(
                                music['start_at'])

                            # 추후 문제시 total_dauration, mod_ts 확인

                            # now(현재시) - mod_ts(음악타임라인)


                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.fadeout(1000)
                                pygame.time.wait(1000)
                                secs += 1
                            pygame.mixer.music.load(prepared_path)
                            pygame.mixer.music.play(start=secs)
                            self.current['type'] = "music"
                            self.current['id'] = music['id']
                            log.info(
                                'Play music success: music=%s, secs=%s, mod_ts=%s, total_duration=%s',
                                music["id"],
                                secs,
                                self.mod_ts,
                                self.total_duration
                            )
                            api_client.log_song(music['music_id'])
                            failure_count = 0
                        else:
                            failure_count += 1
                            pygame.time.wait(1000)
                            continue
                else:
                    self.current['type'] = ""
                    self.current['id'] = 0
                    self.player_setting()
                    # main.player_terminate(True)

            except KeyboardInterrupt:
                break

            except Exception as e:
                self.current['type'] = ""
                self.current['id'] = 0
                log.warn('exception', exc_info=1)
