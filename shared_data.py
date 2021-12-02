import thread_actor


class SharedData:
    __instance = None

    # data
    network_giveup_count = 6
    network_fail_count = 0

    extras = {}

    signed = False
    list_ready = False

    userid = ""
    password = ""

    api_base = ""
    session_info = {}
    member_id = 0
    contract_state = 0
    version_check = 0.0
    playlist_info = {}
    cm_date = ""
    playlist_id = None
    volume = 9

    current_cm_date = ""
    current_playlist_id = ""

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance

        return cls.__instance

    @classmethod
    def add_networkfail_counter(self):
        self.network_fail_count = self.network_fail_count + 1

        if self.network_fail_count > self.network_giveup_count:
            thread_actor.send_message("stop")

    @classmethod
    def reset_networkfail_counter(self):
        if self.network_fail_count <= self.network_giveup_count:
            self.network_fail_count = 0
        else:
            self.network_fail_count = 0
            thread_actor.send_message("play")
