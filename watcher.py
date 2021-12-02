import socket
import threading

from util import logs

HOST, PORT = "localhost", 9999

from subprocess import call
import time
import utils

# watcher
# watcher send ping message
# if ping send fail, restart whole thread

log = logs.get_logger('watcher.py')


class Watcher:
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

    @classmethod
    def scheduler(self):
        while (True):
            time.sleep(3)

            received = self.send_message("ping")
            if received == "pong":
                continue
            else:
                log.info("vodka main restart")
                call(['./restart_vodka.sh'], shell=True)


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 9999
    try:

        surrEvent = threading.Event()
        watcher = Watcher()
        watcher_thread = threading.Thread(target=watcher.scheduler)
        watcher_thread.daemon = True
        watcher_thread.start()

        log.info("watcher thread started")
        surrEvent.wait()

    except KeyboardInterrupt as e:
        print(e)
