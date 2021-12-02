import sqlite3
import threading
from datetime import datetime

import env
import utils
from util import logs

log = logs.get_logger('model.py')

DATA_KEY_DEFAULT_PLAYLIST_ID = 'default_playlist_id'


def synchronized(method):
    """ Work with instance method only !!! """

    def new_method(self, *arg, **kws):
        with self.lock:
            return method(self, *arg, **kws)

    return new_method


class Model:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        log.info('create instance')
        return cls.__instance

    filename = env.DB_FILE
    lock = threading.RLock()

    @classmethod
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __init__(self):
        log.debug('call __init__')
        conn = sqlite3.connect(self.filename)
        c = conn.cursor()
        c.execute(
            'CREATE TABLE IF NOT EXISTS data_info(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, val TEXT)')
        c.execute(
            'CREATE TABLE IF NOT EXISTS playlist_info(id INTEGER PRIMARY KEY, title TEXT, mood TEXT, mod_ts DATETIME, new_count INTEGER, total_duration INTEGER DEFAULT 0, count INTEGER)')
        c.execute(
            'CREATE TABLE IF NOT EXISTS playlist_music2(id TEXT PRIMARY KEY, music_id INTEGER, playlist_id INTEGER, title TEXT, artist_name TEXT, route TEXT, duration TEXT, real_duration INTEGER, path TEXT, start_at DATETIME, end_at DATETIME, cached INTEGER DEFAULT 0, idx INTEGER)')
        c.execute(
            'CREATE TABLE IF NOT EXISTS cm_list2(id TEXT PRIMARY KEY, cm_id INTEGER, `date` DATE, type INTEGER, cm_info TEXT, `time` TEXT, wait_num INTEGER, route TEXT, duration TEXT, real_duration INTEGER, path TEXT, real_at DATETIME, real_end DATETIME, cached INTEGER DEFAULT 0, notuse INTEGER DEFAULT 0, idx INTEGER)')
        conn.commit()
        c.close()
        conn.close()

    @classmethod
    @synchronized
    def get_data_info(self, key):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            c.execute("SELECT * FROM data_info WHERE name = ?", [key])
            data = c.fetchone()
            c.close()
        except:
            log.error('get_data_info: key=%s', key, exc_info=1)
        finally:
            if conn:
                conn.close()
        if data is None:
            return None
        else:
            return data['val']

    @classmethod
    @synchronized
    def set_data_info(self, key, val):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()

            c.execute("SELECT * FROM data_info WHERE name = ?", [key])
            data = c.fetchone()
            if data is None:
                c.execute("INSERT INTO data_info(name, val) VALUES(?, ?)",
                          [key, val])
            else:
                c.execute("UPDATE data_info SET val = ? WHERE name = ?",
                          [val, key])
            conn.commit()
            c.close()
        except:
            log.error('set_data_info: key=%s, val=%s', key, val, exc_info=1)
        finally:
            if conn:
                conn.close()

        return True

    @classmethod
    @synchronized
    def get_playlist_info_all(self):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info")
            data = c.fetchall()
            ##
            c.close()
        except:
            log.error('get_playlist_info_all', exc_info=1)
        finally:
            if conn:
                conn.close()

        if data is None:
            data = []
        return data

    @classmethod
    @synchronized
    def get_playlist_default(self):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info order by title")
            data = c.fetchall()
            ##
            c.close()
        except:
            log.error('get_playlist_default', exc_info=1)
        finally:
            if conn:
                conn.close()

        if data is None:
            data = []
        return data

    @classmethod
    @synchronized
    def get_playlist_info(self, playlist_id):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info WHERE id = ?", [playlist_id])
            data = c.fetchone()
            ##
            c.close()
        except:
            log.error('get_playlist_info: playlist_id=%s', playlist_id, exc_info=1)
        finally:
            if conn:
                conn.close()

        return data

    @classmethod
    @synchronized
    def set_playlist_info(self, playlist_id, title, mood, mod_ts, new_count):
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info WHERE id = ?", [playlist_id])
            data = c.fetchone()
            if data is None:
                # log.info("playlist info insert")
                c.execute("INSERT INTO playlist_info(id, title, mood, mod_ts, new_count) VALUES(?, ?, ?, ?, ?)",
                          [playlist_id, title, mood, mod_ts, new_count])
            else:
                # print("playlist info update")
                c.execute("UPDATE playlist_info SET title = ?, mood = ?, mod_ts = ?, new_count = ? WHERE id = ?",
                          [title, mood, mod_ts, new_count, playlist_id])
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('set_playlist_info: playlist_id=%s', playlist_id, exc_info=1)
        finally:
            if conn:
                conn.close()
        return result

    @classmethod
    @synchronized
    def del_playlist_info(self, playlist_id):
        data = None
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("DELETE FROM playlist_info WHERE id = ?", [playlist_id])
            data = True
            ##
            conn.commit()
            c.close()
        except:
            log.error('del_playlist_info: %s', playlist_id, exc_info=1)
            data = False
        finally:
            if conn:
                conn.close()
        return data

    @synchronized
    def set_playlist_total_duration(self, playlist_id, total_duration):
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info WHERE id = ?", [playlist_id])
            data = c.fetchone()
            if data is not None:
                c.execute("UPDATE playlist_info SET total_duration = ? WHERE id = ?",
                          [total_duration, playlist_id])
                conn.commit()
                result = True
            ##
            c.close()
        except:
            log.error('set_playlist_total_duration: playlist_id=%s, total_duration=%s',
                      playlist_id,
                      total_duration,
                      exc_info=1)
        finally:
            if conn:
                conn.close()

        return result

    @classmethod
    @synchronized
    def put_music_list(self, musics):
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            sql = '''
            INSERT OR REPLACE INTO playlist_music2 (id, music_id, playlist_id, idx, title, artist_name, route, duration, real_duration, path, start_at, end_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            '''
            c.executemany(sql, musics)
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('put_music_list: musics=%s', musics, exc_info=1)
        finally:
            if conn:
                conn.close()
        return result

    @classmethod
    @synchronized
    def put_cm(self, date, cm_id, type, cm_info, time, wait_num, route, duration, real_duration, path, real_at,
               real_end):
        data = []
        last_id = 0
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM cm_list2 WHERE cm_id = ? AND `date` = ? AND time = ?", [cm_id, date, time])
            data = c.fetchone()
            if data is None:
                c.execute(
                    "INSERT INTO cm_list2(cm_id, `date`, type, cm_info, `time`, wait_num, route, duration, real_duration, path, real_at, real_end) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [cm_id, date, type, cm_info, time, wait_num, route, duration, real_duration, path, real_at,
                     real_end])
                last_id = c.lastrowid
            else:
                c.execute(
                    "UPDATE cm_list2 SET cm_id = ?, `date` = ?, type = ?, cm_info = ?, `time` = ?, wait_num = ?, route = ?, duration = ?, real_duration = ?, path = ?, real_at = ?, real_end = ?, notuse = '0' WHERE id = ?",
                    [cm_id, date, type, cm_info, time, wait_num, route, duration, real_duration, path, real_at,
                     real_end,
                     data['id']])
                last_id = data['id']
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('put_cm: date=%s, cm_id=%s', date, cm_id, exc_info=1)
        finally:
            if conn:
                conn.close()
        return last_id

    @classmethod
    @synchronized
    def put_cm_list(self, data):
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            sql = '''
                INSERT OR REPLACE INTO cm_list2 (id, cm_id, `date`, type, cm_info, `time`, wait_num, route, duration, real_duration, path, real_at, real_end, idx)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                '''
            c.executemany(sql, data)
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('put_cm_list: data=%s', data, exc_info=1)
        finally:
            if conn:
                conn.close()
        return result

    def delete_cm_from_idx(self, idx_from):
        """
        CM 목록을 갱신할 때, 과거 목록이 현재 목록보다 길어서 남는 레코드를 제거하기 위해 사용한다.
        :param idx_from:
        :return:
        """
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            sql = '''
                DELETE FROM cm_list2
                WHERE idx >= ?;
                '''
            c.execute(sql, [idx_from])
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('delete_cm_from_idx: idx_from=%s', idx_from, exc_info=1)
        finally:
            if conn:
                conn.close()
        return result

    @classmethod
    @synchronized
    def put_tts(self, id, date, cm_id, type, cm_info, time, wait_num, route, duration, real_duration, path, real_at,
                real_end, idx):
        data = []
        last_id = 0
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute(
                "INSERT OR REPLACE INTO cm_list2(id, cm_id, `date`, type, cm_info, `time`, wait_num, route, duration, real_duration, path, real_at, real_end, cached, idx) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [id, cm_id, date, type, cm_info, time, wait_num, route, duration, real_duration, path, real_at,
                 real_end,
                 "1", idx])
            last_id = c.lastrowid
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('put_tts: id=%s, date=%s, cm_id=%s',
                      id, date, cm_id,
                      exc_info=1)
        finally:
            if conn:
                conn.close()
        return last_id

    @classmethod
    @synchronized
    def get_active_cms(self, date):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            now = utils.getNow().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT * FROM cm_list2 WHERE `date` = ? AND real_end > ? ORDER BY real_at", [date, now])
            data = c.fetchall()
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('get_active_cms: date=%s', date, exc_info=1)
        finally:
            if conn:
                conn.close()

        if data is None:
            data = []
        return data

    @classmethod
    @synchronized
    def get_active_musics_intime(self, playlist_id, cnt):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info WHERE id = ?", [playlist_id])
            playlist = c.fetchone()
            if playlist:
                mod_ts = datetime.strptime(playlist['mod_ts'], "%Y-%m-%d %H:%M:%S")
                total_duration = 0
                total_duration_str = playlist['total_duration']
                if total_duration_str != "":
                    total_duration = int(total_duration_str)
                if total_duration == 0:
                    return []
                now = utils.getNow()
                now_ts = int((now - mod_ts).total_seconds() % total_duration)
                c.execute(
                    "SELECT * FROM playlist_music2 WHERE playlist_id = ? AND start_at <= ? AND end_at > ? ORDER BY start_at Limit ?",
                    [playlist_id, now_ts, now_ts, cnt])
                data = c.fetchall()
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('get_active_musics_intime: playlist_id=%s, cnt=%s',
                      playlist_id, cnt,
                      exc_info=1)
        finally:
            if conn:
                conn.close()

        if data is None:
            data = []
        return data

    @classmethod
    @synchronized
    def get_active_musics_limit(self, playlist_id, cnt):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("SELECT * FROM playlist_info WHERE id = ?", [playlist_id])
            playlist = c.fetchone()
            if not playlist:
                log.debug('get_active_musics_limit: playlist is None')
                return []
            mod_ts = datetime.strptime(playlist['mod_ts'], "%Y-%m-%d %H:%M:%S")
            total_duration = 0
            total_duration_str = playlist['total_duration']
            if total_duration_str != "":
                total_duration = int(total_duration_str)
            if total_duration == 0:
                return []
            now = utils.getNow()
            now_ts = int((now - mod_ts).total_seconds() % total_duration)
            c.execute(
                "SELECT * FROM playlist_music2 WHERE playlist_id = ? AND end_at > ? ORDER BY start_at Limit ? ",
                [playlist_id, now_ts, cnt])
            data1 = c.fetchall()
            data = data1
            if len(data1) < cnt:
                dif_cnt = cnt - len(data1)
                c.execute(
                    "SELECT * FROM playlist_music2 WHERE playlist_id = ? AND end_at <= ? ORDER BY start_at Limit ? ",
                    [playlist_id, now_ts, dif_cnt])
                data2 = c.fetchall()
                data = data + data2
            ##
            c.close()
            result = True
        except:
            log.error('get_active_musics_limit: playlist_id=%s, cnt=%s',
                      playlist_id, cnt,
                      exc_info=1)
        finally:
            if conn:
                conn.close()
        return data

    @classmethod
    @synchronized
    def get_active_cms_intime(self, date, cnt):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            now = utils.getNow().strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "SELECT * FROM cm_list2 WHERE `date` = ? AND real_at <= ? AND real_end > ? ORDER BY idx Limit ?",
                [date, now, now, cnt])
            data = c.fetchall()
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('get_active_cms_intime: date=%s, cnt=%s', date, cnt, exc_info=1)
        finally:
            if conn:
                conn.close()

        if data is None:
            data = []
        return data

    @classmethod
    @synchronized
    def remove_musics(self, playlist_id):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("DELETE FROM playlist_music2 WHERE playlist_id = ?", [playlist_id])
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('remove_musics: %s', playlist_id, exc_info=1)
        finally:
            if conn:
                conn.close()

        return result

    @classmethod
    @synchronized
    def update_count(self, count, id):
        data = []
        result = False
        try:
            conn = sqlite3.connect(self.filename)
            conn.row_factory = self.dict_factory
            c = conn.cursor()
            ##
            c.execute("UPDATE playlist_info SET count = ? WHERE id = ?", [count, id])
            ##
            conn.commit()
            c.close()
            result = True
        except:
            log.error('update_count: count=%s, id=%s', count, id, exc_info=1)
        finally:
            if conn:
                conn.close()

        return result
