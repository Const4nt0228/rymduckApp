kill -9 `ps aux | grep Vodka_main | awk '{print $2}'`
python3 main.py Vodka_main &

