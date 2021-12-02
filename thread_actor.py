import socket

from util import logs

HOST, PORT = "localhost", 9999


# in Thread
# this send_message to main thread

log = logs.get_logger('thread_actor.py')

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
        log.warn('send_message: %s', msg, exc_info=1)
        return 'fail'
