import os
import shutil

import api_client
import env


def setup_recover_musics(api_base: str) -> bool:
    recover_channel_id = env.RECOVER_CHANNEL_ID
    if not recover_channel_id:
        message = 'setup_recover_musics: recover_channel_id is invalid: ' + recover_channel_id
        print(message)
        raise Exception(message)
    init_time = env.INIT_TIME
    print('setup_recover_musics: starts. recover_channel_id=', recover_channel_id, 'init_time=', init_time)
    shutil.rmtree(env.RECOVER_MUSIC_DIR)
    os.mkdir(env.RECOVER_MUSIC_DIR)
    recover_playlist = api_client.get_playlist_detail(api_base, recover_channel_id)
    recover_music_max_count = -1
    if env.RECOVER_MUSIC_MAX_COUNT:
        try:
            recover_music_max_count = int(env.RECOVER_MUSIC_MAX_COUNT)
        except:
            pass
    if recover_music_max_count > 0:
        recover_playlist = recover_playlist[:recover_music_max_count]
    if recover_playlist:
        print('setup_recover_musics: playlist count=', len(recover_playlist))
        for music in recover_playlist:
            music_id = music['music_id']
            music_filename = str(music_id) + '.dat'
            music_url = music['route']
            music_path = os.path.join(env.RECOVER_MUSIC_DIR, music_filename)
            api_client.download(music_url, music_path)
        return True
    else:
        print('setup_recover_musics: playlist is empty. channel_id=', recover_channel_id)
    return False


print('Initialize recover musics')
api_base = api_client.get_default_api_server()
success = setup_recover_musics(api_base)
if not success:
    raise Exception('[ERROR] Failed to setup recover music')
