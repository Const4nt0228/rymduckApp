# vodka_light
python music player on linux platform
## 0. code & img 관리
### 1) code 관리
code 관리는 github로 관리하는 것을 원칙으로 한다.
### 2) img 관리
#### img 생성
수정된 코드에 대해서 img를 생성하는 방법은 리눅스의 dd를 이용한다. <br>
(단, 장치및 디렉토리의 이름은 변동될 수 있음)

    sudo su                           // 관리자 계정으로 변환 
    fdisk -l /dev/mmcblk0             // SD카드 파티션정보 확인 
    lsusb                             // USB 장치 확인 
    mount -t vfat /dev/sda1 /mnt      // USB 장치 mount
    dd if=/dev/mmcblk0 of=/mnt/vodka_light.img bs=512 count=000000 // img 생성 시작

count에는 end sector(0.5MB)를 입력하며, 입력한 크기가 곧 img 크기가 된다.
이미지는 mount한 USB에 저장된다.

#### img 굽기
Etcher를 이용하여 img를 굽는다. <br>
Etcher는 다중프로그램 실행이 가능하며, USB 허브등을 이용해 동시에 굽는 작업도 가능하다

    1. Etcher 실행 
    2. img 선택 
    3. 드라이브 선택
    4. flash 버튼을 통해 굽기 시작
    
배포에 대한 자세한 설명은 '공유폴더 - 개발문서 - 메뉴얼'를 참고해주십시오.

## 1. init setting
    sudo apt-get -y install rdate 
    sudo apt-get -y update sudo apt-get -y install python3-dev python3-numpy python3-pip 
    libsdl-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsmpeg-dev 
    libportmidi-dev libavformat-dev libswscale-dev libjpeg-dev libfreetype6-dev 
    sudo pip3 install pygame

    add to /etc/rc.local  "sudo -u pi bash -c /home/pi/vodka_python/launch.sh &" 
    add (contab -e) "0 6 * * * sudo -u pi bash -c /home/pi/vodka_python/launch.sh &"

for mac

    sudo apt-get -y install rdate
    brew install sdl sdl_image sdl_mixer sdl_ttf portmidi
    brew reinstall sdl_mixer --with-libvorbis
    
----------------------------------------------

## 부록
### 초기 이미지파일에 계정세팅하는 방법
1) pi 입력 후 엔터

2) 1db1player 비밀번호 입력 후 엔터

3) cd vodka_py...[tab] 엔터 눌러 이동

4) ./stop.sh

5) cd ..

6) ./init.sh

7) user id를 물어보면 cms상의 user_id를 입력
   pw를 물어보면 해당 user_id 의 pw를 입력

8) ssid 입력란: wifi ssid를 입력
   pw 입력란: wifi pw를 입력

---Complete---
* init 시 init.sh가 vodka_python 폴더 하위로 이동하므로 reset하고 싶을 경우 해당 folder로 이동하여 수행한다.

### 업데이트 방법
1) version.json을 해당 버전에 맞게 수정

2) vodka_python dir 내부에 있는 파일(.py & .sh)만 모아 반디집 프로그램을 이용하여 tgz타입으로 압축

3) 압축파일을 업로드 (단, 업로드시 오피스키퍼로 인해 파일이 손상될 위험이 있음)

4) KT & Azure DB를 수정 (version, member table)

### Mqtt 서버 세팅하기

1) apt-get install mosquitto 명령어를 이용해 설치

2) 설치와 동시에 자동 실행이나, 실행이 되지 않을시 mosquitto -d

3) mosquitto_pub -t vodka_python/user_(user_id) -m "changeplaylist|(playlist_id)" 로 test

### Version Log

#### ver.11.43
    1) Player 로그인시 최근 로그인 기록이 남게끔 API 통신

#### ver.11.5
    1) MQTT 도입
       - 채널, 볼륨 setting값 변경 (get_setting pooling 속도 3초에서 40초로 변경)
    2) 볼륨 알고리즘 수정
       - 사용자가 설정한 볼륨이 처음부터 나오는 것이 아닌 기본 볼륨(95%)로 송출되다가 설정 볼륨으로 되던 방식을
         처음부터 설정 볼륨이 나오게끔 수정

### ver.11.7
    1) TTS 기능 추가
    2) TeamViewer(원격 프로그램) 기능 추가
    3) MQTT 기능 추가
       - TTS 송출
       - data reset (model.db, .cache 디렉토리 삭제 후 재부팅)
       - Teamviewer id를 DB 저장하는 API 호출, TeamviewerPW 재설정
    4) 볼륨 알고리즘 추가 수정
       - 볼륨이 설정되지 않는 경우(get_setting에 값이 없는 경우)에 대한 미흡한 예외처리
