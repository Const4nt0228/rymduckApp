# Rhymeduck Settop[Linux] 개발문서

# vodka_light
#####  *python music player on linux platform*    
----  

## Features
- 플랫폼 : Linux
- Plug & Play 기반의 셋톱박스로 음악서비스 제공
- 유선(Lan선) / 무선 공유기를 통한 네트워크 통신 가능
- 셋톱박스 제어를 위한 반응형 웹 페이지 운영 (stb.rhymeduck.com, scplay.kr)
- 페이지를 통한 볼륨 조절, 채널 변경, 현재 재생 중인 음악 확인, TTS 기능

 | 구분 | 사양 |
 | ------ | ------ |
 | 보드 | Raspberry PI 3 model B Rev 1.2 |
 | OS | Raspbian GNU/Linux 8 (jessie) 32bit |
 | CPU| ARMv7 Processor rev 4 (v71) |
 |RAM| 1GB |
 
--- 
### init&#46;sh 분석
    
```
set -e
sudo sh /home/pi/vodka_python/script/user_setting.sh
sudo sh /home/pi/vodka_python/script/wifi_setting.sh
python3 /home/pi/vodka_python/init.py

sudo teamviewer passwd devtreez1012

sudo raspi-config nonint do_expand_rootfs

mv -f init.sh /home/pi/vodka_python/init.sh

echo 'All done. Reboot'
sleep 15
sudo reboot
```

+ 사용전 초기 정보를 셋팅하는 sh 파일
+ user_setting.sh 를 통해 ID와 PW 입력 후 config.json파일에 저장
+ wifi_setting.sh 를 통해 네트워크 접속 정보 wpa_supplicant.conf 저장

---
### watcher&#46;py 분석

```
    def scheduler(self):
        while (True):
            time.sleep(3)

            received = self.send_message("ping")
            if received == "pong":
                continue
            else:
                log.info("vodka main restart")
                call(['./restart_vodka.sh'], shell=True)
```

```
    def send_message(msg):
        # Create a socket (SOCK_STREAM means a TCP socket)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Connect to server and send data
                sock.connect((HOST, PORT))
                sock.sendall(bytes(msg + "\n", "utf-8"))

                # Receive data from the server and shut down
                received = str(sock.recv(1024), "utf-8")
                return received
        except Exception as e:
            print(e)
            return "false"
```   

+ thread를 이용해 구동
+ socket을 통한 handshaking 하는 프로그램으로 프로그램이 정상 작동하는지 모니터링하는 모듈
+ localhost, 9999 PORT에 메세지 'ping' 을 보내고 응답 메세지'pong' 을 수신받지 못할 경우 restart_vodka.sh를 call

---
main&#46;py 분석
```
            if "downloader_tmp_" in file:
                file_path = os.path.join(env.CACHE_DIR, file)
                log.info('delete downloader temp file: %s', file_path)
                os.remove(file_path)
```
+ downloader_tmp 임시파일 삭제
```
json_data = open("./config.json").read()
json_data = open("./version.json").read()
```
+ json 파일 저장데이터를 통해 use, device information 불러옴

```
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
```
+ TCP 통신방식으로 VodkaTCPServer와 연결, thread로 동작
+  VodkaTCPHandler 동작수행함





##### 매장음악에서 동시성이 왜 필요한지

### 끊임없는 음원 재생을 위한 동시성

![sc](https://github.com/Const4nt0228/rymduckApp/blob/main/img/%EB%8F%99%EC%8B%9C%EC%84%B1.drawio.png?raw=true)


---
### process pseudo code
#### class Player(Thread Class) -> self.stopped
```
    def run()
        init()
        player_setting()
            init() //db에서 List get
                   //vol Setting
                   
    while (not stopped)
        active_cm = cm_list[]
        active_music = ms_list[]
        
        if(5회 이상 실패시)
            recover 작업 (player_setting()으로 다시 받아옴)
            recover_music (비상용 음원 재생)

        elif active_cm
            // music 재생중에는 cm으로 변경이 가능 
    
        elif
            cm도중에는 music으로 변경이 불가능
            


```
----
#### def init()
+ pygame.mixer : Sound 객체 로드, 제어

#### def prepare music()
pseudo code
```
for env.CACHE_DIR의 모든 파일 읽어들이면서
    if file.endswith ('mp3')
        remove -> env.CACHE_DIR.file ()
    if file.endswith('ogg') //no royalty codec file
        remove -> env.CACHE_DIR.file ()
    // 캐시 디렉토리에있는 음원파일 삭제
    
    ?? current_music 에 캐시 디렉토리에서 이름이 현재 시간으로 되어있는 mp3파일 저장
    
    success = descrypt(current_music) //파일 복호화
    // 복호화는 AES(고급암호화표준사용)
    // SALT 방식을 이용화해서 암호화되었음
    
    success = convert .mp3 to .ogg
```


---
### def run(self)

```
act_index값 증가
my_index = act_index

init() // sound객체 로드 제어
player_setting() //플레이어 환경 세팅

while(not stopped)
    if(stopped -> is_on=False) //is_on 은 플레이어 동작 여부 bool
    cm_list, music_list 불러옴
    
    if true
        active_cm 에 cm_list 첫번째 (재생해야할 첫번째)
        active_music 에 music_list 첫번째 (재생해야할 첫번째)
    else
        active_cm, music 에 None 값 대입
        
    if failure_count > 5
        failure_count 초기화, self.play_recover_music() 리커버 수행
        
        play_recover_music 동작 시
        recovering = True //비상용 음원이 실행중인지 bool
        recover_music을 대신 틀어줌,
        player_setting() 재시도하여서 정상화를 다시시도함
        
        //failure 작동시 비상용 음원 재생하면서 정상화 시도하기 위해 동시성을 사용하나?
        
        elif active_cm
            요청에 따라 cm재생, 이미 재생중이면 그냥 그대로 재생
        elif active_music 
            요청에 따라 music 재생
            cm재생중일때 인터럽트로 music 재생은 못함, 
        둘다 경로에 음악이없다면(다운로드를 못받은 경우 해당) -> failure count
        -> //failure count가 5개인 이유는 5곡씩 미리 다운받기 때문에??
```
