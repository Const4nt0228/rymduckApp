import json
import logging
import os


# Dir and files
def makeDir(path):
    if not os.path.exists(path):
        os.mkdir(path)


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, 'log')
DB_FILE = os.path.join(ROOT_DIR, "model.db")
LOG_FILE = os.path.join(LOG_DIR, 'application.log')
CACHE_DIR = os.path.join(ROOT_DIR, '.cache')
CACHE_MUSIC_DIR = os.path.join(CACHE_DIR, 'music')
CACHE_CM_DIR = os.path.join(CACHE_DIR, 'cm')
RECOVER_MUSIC_DIR = os.path.join(ROOT_DIR, '.recover')
TTS_DIR = os.path.join(ROOT_DIR, '.tts')
makeDir(LOG_DIR)
makeDir(CACHE_DIR)
makeDir(CACHE_MUSIC_DIR)
makeDir(CACHE_CM_DIR)
makeDir(RECOVER_MUSIC_DIR)
makeDir(TTS_DIR)

LOG_FORMATTER = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

# Config
config_json = open(os.path.join(ROOT_DIR, "config.json")).read()
config = json.loads(config_json)
USER_ID = config['userid']
PASSWORD = config['password']
RECOVER_CHANNEL_ID = config.get('recover_channel_id')
RECOVER_MUSIC_MAX_COUNT = config.get('recover_music_max_count')
INIT_TIME = config.get('init_time')
STAGE = 'production'
try:
    STAGE = config['stage']
except:
    pass
def is_dev() -> bool:
    return STAGE == "dev"

# Logging
LOG_LEVEL = logging.INFO
if is_dev():
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL)
