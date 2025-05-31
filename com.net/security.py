from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import base64

SECRET_KEY = hashlib.sha256(b'key_dung_de_lam_khoa_32_bits').digest()
BLOCK_SIZE = 16

def pad(data):
    padding_len = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + chr(padding_len) * padding_len

def unpad(data):
    padding_len = ord(data[-1])
    return data[:-padding_len]

def encrypt_message(plain_text):
    iv = get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    padded = pad(plain_text).encode('utf-8')
    ciphertext = cipher.encrypt(padded)
    return base64.b64encode(iv + ciphertext).decode('utf-8')

def decrypt_message(encoded_data):
    try:
        raw = base64.b64decode(encoded_data)
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        padded_plain = cipher.decrypt(ciphertext).decode('utf-8')
        return unpad(padded_plain)
    except Exception as e:
        print("Decrypt error:", e)
        return None
