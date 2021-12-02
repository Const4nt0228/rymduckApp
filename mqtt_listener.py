import os

import pygame

import model
import mqtt.client as mqtt
import shared_data
import thread_actor
import utils
from thread_class import ThreadClass
from util import logs

default_path = "./.cache"
music_path = default_path + "/music"
cm_path = default_path + "/cm"

log = logs.get_logger('mqtt_listener.py')


class MyMQTTClass(mqtt.Client):
    parent = None
    model = None

    def init(self):
        self.model = model.Model.instance()

    def on_connect(self, mqttc, obj, flags, rc):
        pygame.time.wait(1 * 1000)
        if str(shared_data.SharedData.instance().member_id) != "0":
            log.info("mqtt thread get member_id from api")
            self.subscribe("vodka_python/user_" + str(shared_data.SharedData.instance().member_id), 1)
            self.subscribe("vodka_python/all/", 1)
        elif str(self.model.get_data_info('member_id')) != "0":
            log.info("mqtt thread get member_id from model.db")
            self.subscribe("vodka_python/user_" + str(self.model.get_data_info('member_id')), 1)
            self.subscribe("vodka_python/all/", 1)
        else:
            log.info("mqtt error")

    def on_message(self, mqttc, obj, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        msg_text = msg.payload.decode("utf-8")
        # print(msg_text)
        data_list = msg_text.split("|")
        if data_list[0] == "changeplaylist":
            thread_actor.send_message("changeplaylist|" + str(data_list[1]))
        if data_list[0] == "changevolume":
            thread_actor.send_message("changevolume|" + str(data_list[1]))
        if data_list[0] == "playtts":
            thread_actor.send_message("playtts")
        if data_list[0] == "settvid":
            thread_actor.send_message("settvid")
        if data_list[0] == "settvpw":
            os.system("sudo rm -f /opt/teamviewer/config/global.conf")
            os.system("sudo teamviewer passwd devtreez1012")
        if data_list[0] == "reset":
            thread_actor.send_message("reset")

    def on_publish(self, mqttc, obj, mid):
        # print("mid: "+str(mid))
        None

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        # print("Subscribed: "+str(mid)+" "+str(granted_qos))
        None

    # def on_log(self, mqttc, obj, level, string):
    # print(string)

    def set_parent(self, Mqtt_listener):
        parent = Mqtt_listener


class Mqtt_listener(ThreadClass):
    #    model = None

    # print("vodka_python/user_" + str(shared_data.SharedData.instance().member_id))
    def run(self):
        mqttc = MyMQTTClass(protocol=mqtt.MQTTv31)

        #       logger = logging.getLogger(__name__)
        #       mqttc.enable_logger(logger)

        mqttc.init()

        mqttc.set_parent(self)
        host = "40.74.131.223"
        port = 1883

        while not self.stopped():
            try:
                mqttc.connect(host, port)
                log.info('Success to connect to MQTT server. Start Listening.')
                mqttc.loop_forever()
            except:
                log.error('Failed to connect to MQTT server: host=%s, port=%s}', host, port)
                pygame.time.delay(30000)

        # while (not self.stopped()):
        #     try:
        #
        #         mqttc.loop()
        #     except KeyboardInterrupt:
        #         break
        #     except Exception as e:
        #         print(e)
