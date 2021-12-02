import datetime
import json
import os
import socketserver
import threading

import api
import downloader
import env
import health_checker
import model
import mqtt_listener
import player
import playlist
import shared_data
import status_checker
import utils
from util import logs


def make_text_message(text):
    return bytes(text, "utf-8")


server = None
surrEvent = None

api_thread = None
downloader_thread = None
remover_thread = None
status_checker_thread = None
playlist_checker_thread = None
mqtt_listener_thread = None
mqttclient = None
player_thread = None

log = logs.get_logger('main.py')


def shutdownHandler(msg, evt):
    print("shutdown handler called. shutting down on thread id:%x" % (id(threading.currentThread())))

    server.server_close()
    server.shutdown()

    api_thread.terminate()
    api_thread.join()

    # remover_thread.terminate()
    # remover_thread.join()

    status_checker_thread.terminate()
    status_checker_thread.join()

    playlist_checker_thread.terminate()
    playlist_checker_thread.join()

    mqtt_listener_thread.terminate()
    mqtt_listener_thread.join()

    print("shutdown complete")
    evt.set()
    return


def terminate():
    print("terminate handle on thread id:%x" % (id(threading.currentThread())))
    t = threading.Thread(target=shutdownHandler, args=('SIGTERM received', surrEvent))
    t.start()


# -- shut down process

class VodkaTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip()
        # print("{} wrote:".format(self.client_address[0]))
        # print(self.data)
        # just send back the same data, but upper-cased
        msg_text = self.data.decode("utf-8")

        model_db = model.Model.instance()
        shared = shared_data.SharedData.instance()

        if self.data == make_text_message("ping"):
            self.request.sendall(make_text_message("pong"))
        elif self.data == make_text_message("play"):
            player_start()
        elif self.data == make_text_message("stop"):
            player_terminate(False)
        elif self.data == make_text_message("close"):
            player_terminate(False)
            downloader_terminate(False)
            playlist_checker_terminate(False)
            terminate()
        elif self.data == make_text_message("current_playlist_id"):
            self.request.sendall(make_text_message(str(shared.playlist_id)))
        elif self.data == make_text_message("current_cm_date"):
            self.request.sendall(make_text_message(str(api_thread.cm_date)))
        elif self.data == make_text_message("player_status"):
            if player_thread is None or not player_thread.is_alive():
                self.request.sendall(make_text_message("not ready"))
            elif player_thread.is_on:
                self.request.sendall(make_text_message("playing"))
            else:
                self.request.sendall(make_text_message("stoped"))
        elif self.data == make_text_message("apicheck"):
            log.info("playlist is : " + str(shared.playlist_id))
        elif self.data == make_text_message("current_playlist"):
            data = model_db.get_playlist_info_all()
            self.request.sendall(make_text_message(str(data)))
        # elif self.data == make_text_message("listupdated"):
        #    downloader_start()
        elif self.data == make_text_message("playlist_checker_start"):
            playlist_checker_start()
        elif self.data == make_text_message("playlist_checker_start"):
            playlist_checker_start()
        elif msg_text[:14] == "changeplaylist":
            playlist_id = int(msg_text[15:])
            log.info('VodkaTCPHandler/change playlist: id=%s', playlist_id)
            pinfo = model_db.get_playlist_info(playlist_id)
            if pinfo is not None:
                model_db.set_data_info('playlist_id', playlist_id)
                shared.playlist_id = playlist_id
                shared.playlist_info = pinfo
                player.Player.player_setting()
            else:
                log.warn('VodkaTCPHandler/change playlist: playlist_info from DB is None')
        elif msg_text[:12] == "changevolume":
            volume = msg_text[13:]
            log.info('VodkaTCPHandler/change volume: volume=%s', volume)
            model_db.set_data_info('volume', volume)
            shared.volume = volume
            player.Player.player_setting()
        elif self.data == make_text_message("playtts"):
            log.info("request play TTS")
            api_thread.get_chime()
            api_thread.get_tts()
        elif self.data == make_text_message("settvid"):
            log.info("request set TeamViewer ID")
            api_thread.set_teamviewer_id()
        elif self.data == make_text_message("reset"):
            log.info('request vodka reset')
            os.system('sudo rm -r .cache/music')
            os.system('sudo rm -r .cache/cm')
            os.system('sudo rm model.db')
            os.system('sudo reboot')


class VodkaTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    pass


def downloader_terminate(after_restart):
    print("downloader shutdown complete")
    global downloader_thread
    if downloader_thread is None:
        return
    downloader_thread.terminate()
    downloader_thread = None
    if after_restart:
        print("downloader restart")
        downloader_start()
    return


def downloader_start():
    global downloader_thread
    if downloader_thread is not None and downloader_thread.is_alive():
        downloader_terminate(True)
    else:
        downloader_thread = downloader.Downloader()
        downloader_thread.daemon = True
        downloader_thread.start()


def player_terminate(after_restart):
    global player_thread
    if player_thread is None:
        return
    print("player shutdown complete")

    player_thread.terminate()
    player_thread = None
    if after_restart:
        print("player restart")
        player_start()
    return


def player_start():
    global player_thread
    if player_thread is not None and player_thread.is_alive():
        player_terminate(True)
    else:
        player_thread = player.Player()
        player_thread.daemon = True
        player_thread.start()


def playlist_checker_terminate(after_restart):
    global playlist_checker_thread
    if playlist_checker_thread is None:
        return
    print("playlist_checker shutdown complete")

    playlist_checker_thread.terminate()
    playlist_checker_thread = None
    if after_restart:
        print("playlist_checker restart")
        playlist_checker_start()
    return


def playlist_checker_start():
    global playlist_checker_thread
    if playlist_checker_thread is not None and playlist_checker_thread.is_alive():
        playlist_checker_terminate(True)
    else:
        playlist_checker_thread = playlist.PlaylistService()
        playlist_checker_thread.daemon = True
        playlist_checker_thread.start()


def on_connect(mqttc, obj, flags, rc):
    # print("rc: " + str(rc))
    None


def on_message(mosq, obj, msg):
    # This callback will be called for messages that we receive that do not
    # match any patterns defined in topic specific callbacks, i.e. in this case
    # those messages that do not have topics $SYS/broker/messages/# nor
    # $SYS/broker/bytes/#
    log.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


if __name__ == "__main__":
    log.info('Application Starts')
    log.info('env.ROOT_DIR: %s', env.ROOT_DIR)
    log.info('env.LOG_DIR: %s', env.LOG_DIR)
    log.info('env.DB_FILE: %s', env.DB_FILE)
    log.info('env.CACHE_DIR: %s', env.CACHE_DIR)
    log.info('env.CACHE_MUSIC_DIR: %s', env.CACHE_MUSIC_DIR)
    log.info('env.CACHE_CM_DIR: %s', env.CACHE_CM_DIR)
    log.info('env.RECOVER_MUSIC_DIR: %s', env.RECOVER_MUSIC_DIR)
    log.info('env.LOG_FILE: %s', env.LOG_FILE)
    log.info('env.LOG_LEVEL: %s', env.LOG_LEVEL)
    log.info('env.USER_ID: %s', env.USER_ID)
    log.info('env.RECOVER_CHANNEL_ID: %s', env.RECOVER_CHANNEL_ID)
    log.info('env.INIT_TIME: %s', env.INIT_TIME)
    if env.INIT_TIME:
        try:
            init_time = int(env.INIT_TIME)
            init_time = datetime.datetime.fromtimestamp(init_time)
            init_time = init_time.strftime("%Y-%m-%d %H:%M")
            log.info('env.INIT_TIME: %s', init_time)
        except:
            pass
    log.info('env.STAGE: %s', env.STAGE)

    # clear temp download files
    try:
        for file in os.listdir(env.CACHE_DIR):
            if "downloader_tmp_" in file:
                file_path = os.path.join(env.CACHE_DIR, file)
                log.info('delete downloader temp file: %s', file_path)
                os.remove(file_path)
    except:
        log.warn('Clear failed', exc_info=1)

    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 9999
    try:
        try:
            json_data = open("./config.json").read()

            config_json = json.loads(json_data)

            # log.info(str(config_json))
            shared_data.SharedData.instance().userid = config_json['userid']
            shared_data.SharedData.instance().password = config_json['password']
        except:
            log.info("fail to load config")
            quit(0)

        try:
            json_data = open("./version.json").read()

            version_json = json.loads(json_data)

            # log.info(str(version_json))
            shared_data.SharedData.instance().version_check = version_json['version']
        except:
            log.info("fail to load version info")
            quit(0)

        # Server
        surrEvent = threading.Event()
        socketserver.TCPServer.allow_reuse_address = True
        server = VodkaTCPServer((HOST, PORT), VodkaTCPHandler)
        server.ip, server.port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        log.info("server thread started")

        api_thread = api.ApiService()
        api_thread.daemon = True
        api_thread.start()
        log.info("api thread started")

        downloader_thread = downloader.Downloader()
        downloader_thread.daemon = True
        downloader_thread.start()
        log.info("downloader thread started")

        #########################################################
        # 2019-11-08 sqlite3 독점 문제로 주석처리
        # remover_thread = remover.Remover()
        # remover_thread.daemon = True
        # remover_thread.start()
        # log.info("remover thread started")
        #########################################################

        status_checker_thread = status_checker.StatusChecker()
        status_checker_thread.daemon = True
        status_checker_thread.start()
        log.info("status checker thread started")

        mqtt_listener_thread = mqtt_listener.Mqtt_listener()
        mqtt_listener_thread.daemon = True
        mqtt_listener_thread.start()
        log.info("mqtt listener thread started")

        health_checker_thread = health_checker.HealthChecker()
        health_checker_thread.daemon = True
        health_checker_thread.start()
        log.info("health_checker_thread started")

        # mqttclient.subscribe("vodka_python/user_" + str(shared_data.SharedData.instance().userid) + "/#", 0)
        surrEvent.wait()

    except KeyboardInterrupt as e:
        print(e)
        server.server_close()
        server.shutdown()

    except Exception as e:
        print(e)
