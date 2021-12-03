###### 협정세계시와 sqlite3 서버의 음원 타임라인을 이용하여 현재 재생해야할 음원 출력  

+ 모든 매장에서 동일한 타임라인의 음악을 송출해야 공연 법률에 만족함
+ 동일한 타임라인을 맞추기 위해 싱크 일치화 알고리즘 사용 

~~~
  if utils.file_is_valid(prepared_path):
     secs = int((now - self.mod_ts).total_seconds() % self.total_duration) - int(music['start_at'])
~~~
+ now : def getNow()이용해 호출한 협정세계시의 한국시간
+ mod_ts : sqlite3 DB에 저장된 playlist_info 에서의 플레이리스트 타임라인
+ total_duration : 플레이리스트 전체 길이
+ music['start_at'] : 플레이리스트 음원 시작지점

+ 위 네가지 변수를 이용하여 현재 재생해야할 시점인 secs 정의

~~~
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(1000)
        pygame.time.wait(1000)
        secs += 1
    pygame.mixer.music.load(prepared_path)
    pygame.mixer.music.play(start=secs)
~~~
+ secs 시간부터 음원 재생 시작


~~~
CREATE TABLE IF NOT EXISTS playlist_info
(id INTEGER PRIMARY KEY, title TEXT, mood TEXT, mod_ts DATETIME, new_count INTEGER, total_duration INTEGER DEFAULT 0, count INTEGER)')
~~~
+ DB에 저장된 playlist_info table
