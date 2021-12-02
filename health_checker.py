import random
import time

import pygame

import api_client
import shared_data
from thread_class import ThreadClass
from util import logs

log = logs.get_logger('health_checker.py')
INTERVAL_UPDATE_PERIOD = 10 * 60 # 10 min
INTERVAL_MIN = 5 #sec

class HealthChecker(ThreadClass):
    def __init__(self):
        super().__init__()
        self.interval_update_time = 0
        self.interval_min = 5
        self.interval_max = 10

    def run(self):
        while not self.stopped():
            shared = shared_data.SharedData.instance()
            if shared.member_id:
                health_check_result = api_client.health_check()
                if not health_check_result:
                    log.warn('health check failed')
                if self.interval_update_time < time.time() - INTERVAL_UPDATE_PERIOD:
                    log.info('update health check interval: start')
                    self.interval_update_time = time.time()
                    try:
                        period = api_client.get_health_check_interval()
                        if period and len(period) >= 2:
                            log.info('update health check interval: period from API = %s', period)
                            min = period[0]
                            max = period[1]
                            if min < INTERVAL_MIN:
                                log.info('update health check interval: period.min is too small. use default value = 5(s)')
                                min = INTERVAL_MIN
                            if max < min:
                                max = min
                            self.interval_min = min
                            self.interval_max = max
                            log.info('update health check interval: update done. min=%s(s), max=%s(s)', min, max)
                    except:
                        log.error('update health check', exc_info=1)

                interval = random.randint(self.interval_min, self.interval_max) * 1000
                interval = interval + random.randint(0, 100)
                log.debug('next health check starts after: interval=%s', interval)
                pygame.time.delay(interval)
