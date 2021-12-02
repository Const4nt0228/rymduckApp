from datetime import datetime

import pygame

import model
import shared_data
import thread_actor
from thread_class import ThreadClass


# if player not playing
# although there are songs to play
# then status checker restart player

class StatusChecker(ThreadClass):

    def run(self):
        while not self.stopped():
            shared = shared_data.SharedData.instance()
            if shared.signed and shared.list_ready and shared.network_fail_count <= shared.network_giveup_count:
                model_obj = model.Model.instance()
                current_playlist_id = shared.playlist_id
                playlist_info = model_obj.get_playlist_info(current_playlist_id)
                mod_ts = datetime.strptime(playlist_info['mod_ts'], "%Y-%m-%d %H:%M:%S")

                music_list = model_obj.get_active_musics_intime(current_playlist_id, 3)
                if len(music_list) > 0:
                    player_status = thread_actor.send_message("player_status")
                    if player_status == "not ready":
                        thread_actor.send_message("play")
                    elif player_status == "stopped":
                        pygame.time.delay(10 * 1000)
                        player_status = thread_actor.send_message("player_status")
                        if player_status == "stopped":
                            pygame.time.delay(5 * 1000)
                            player_status = thread_actor.send_message("player_status")
                            if player_status == "stopped":
                                ## 15 second stopped => replay
                                thread_actor.send_message("play")

                    elif player_status == "playing" and not pygame.mixer.music.get_busy():
                        pygame.time.delay(10 * 1000)
                        player_status = thread_actor.send_message("player_status")
                        if player_status == "playing" and not pygame.mixer.music.get_busy():
                            ## 10 playing status 'playing' but music is not busy => replay
                            thread_actor.send_message("play")

            pygame.time.delay(3 * 60 * 1000)
