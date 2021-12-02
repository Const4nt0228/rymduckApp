kill -9 `ps aux | grep Vodka_watcher | awk '{print $2}'`
kill -9 `ps aux | grep Vodka_main | awk '{print $2}'`
