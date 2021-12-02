import os
from typing import Optional

import env

last_recover_music_index = -1


def get_recover_music() -> Optional[str]:
    global last_recover_music_index
    """
    호출할 때마다 비상음원을 순차적으로 리턴한다.
    :return: 
    """
    recover_musics = os.listdir(env.RECOVER_MUSIC_DIR)
    if recover_musics:
        recover_music_count = len(recover_musics)
        this_recover_music_index = (last_recover_music_index + 1) % recover_music_count
        last_recover_music_index = this_recover_music_index
        return recover_musics[this_recover_music_index]
    else:
        return None
