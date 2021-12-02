sudo rdate -s time.bora.net
cd /home/pi/vodka_python

mkdir ./.cache
chmod -R 777 ./.cache
mkdir ./.cache/cm
chmod -R 777 ./.cache/cm
mkdir ./.cache/music
chmod -R 777 ./.cache/music

if [ -f "./setup.sh" ]
then
  sudo chmod 755 setup.sh
  ./setup.sh
fi

find /home/pi/vodka_python/.cache -name "downloader_tmp_*" -delete

kill -9 `ps aux | grep Vodka_watcher | awk '{print $2}'`
kill -9 `ps aux | grep Vodka_main | awk '{print $2}'`
python3 main.py Vodka_main &
python3 watcher.py Vodka_watcher &