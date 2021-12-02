import os
from datetime import datetime, timedelta
from hashlib import md5
from os import urandom

from Crypto.Cipher import AES

from util import logs

log = logs.get_logger('utils.py')


def getNow():
    # tz = timezone(timedelta(hours=9))
    return datetime.utcnow() + timedelta(hours=9)


def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = b''  # changed '' to b''
    while len(d) < key_length + iv_length:
        # changed password to str.encode(password)
        d_i = md5(d_i + str.encode(password) + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length + iv_length]


def encrypt_file(password, in_filename, out_filename, salt_header='', key_length=32):
    with open(in_filename, 'rb') as in_file, open(out_filename, 'wb') as out_file:

        # added salt_header=''
        bs = AES.block_size
        # replaced Crypt.Random with os.urandom
        salt = urandom(bs - len(salt_header))
        key, iv = derive_key_and_iv(password, salt, key_length, bs)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # changed 'Salted__' to str.encode(salt_header)
        out_file.write(str.encode(salt_header) + salt)
        finished = False
        while not finished:
            chunk = in_file.read(1024 * bs)
            if len(chunk) == 0 or len(chunk) % bs != 0:
                padding_length = (bs - len(chunk) % bs) or bs
                # changed right side to str.encode(...)
                chunk += str.encode(
                    padding_length * chr(padding_length))
                finished = True
            out_file.write(cipher.encrypt(chunk))


def decrypt_file(password, in_filename, out_filename, salt_header='', key_length=32):
    try:
        with open(in_filename, 'rb') as in_file, open(out_filename, 'wb') as out_file:
            # added salt_header=''
            bs = AES.block_size
            # changed 'Salted__' to salt_header
            salt = in_file.read(bs)[len(salt_header):]
            key, iv = derive_key_and_iv(password, salt, key_length, bs)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            next_chunk = ''
            finished = False
            while not finished:
                chunk, next_chunk = next_chunk, cipher.decrypt(
                    in_file.read(1024 * bs))
                if len(next_chunk) == 0:
                    padding_length = chunk[-1]  # removed ord(...) as unnecessary
                    chunk = chunk[:-padding_length]
                    finished = True
                out_file.write(bytes(x for x in chunk))  # changed chunk to bytes(...)
        return True
    except:
        log.warning('decrypt_file failed: in_file=%s, out_file=%s', in_filename, out_filename)
        return False


def file_is_valid(path: str) -> bool:
    return path and os.path.exists(path) and os.path.getsize(path) > 0
