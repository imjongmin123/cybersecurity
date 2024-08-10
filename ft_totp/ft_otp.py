import os
import argparse
import hmac
import hashlib
import base64
import time
import struct
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


# Hexadecimal 키 유효성 검사
def check_hex_key(key):
    try:
        if len(key) < 64 or len(key) > 128:
            return False
        value = int(key, 16)
        return True
    except ValueError:
        return False

# 공개키를 사용하여 키 암호화
def encryption_key(key, public_key):
    try:
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_key = cipher_rsa.encrypt(key.encode())
        with open('ft_otp.key', 'wb') as file:
            file.write(encrypted_key)
    except Exception as e:
        print(f"Error encrypting key: {e}")
        raise

# 개인키를 사용하여 키 복호화
def decryption_key(private_key, encrypted_key):
    try:
        cipher_rsa = PKCS1_OAEP.new(private_key)
        decrypted_key = cipher_rsa.decrypt(encrypted_key)
    except FileNotFoundError:
        print("Error: Encrypted key file not found.")
        raise
    except Exception as e:
        print(f"Error decrypting key: {e}")
        raise
    return decrypted_key

# RSA 키 쌍 생성
def generate_key_pair():
    try:
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()

        with open("private.pem", "wb") as priv_file:
            priv_file.write(private_key)
        with open("public.pem", "wb") as pub_file:
            pub_file.write(public_key)
        print("Key was successfully saved in ft_otp.key.")
    except Exception as e:
        print(f"Error generating key pair: {e}")
        raise

# RSA 키 쌍 로드
def load_key_pair():
    try:
        if not os.path.exists("private.pem") or not os.path.exists("public.pem"):
            print("Not exist key. Gerenating key...")
            generate_key_pair()
        with open("private.pem", "rb") as priv_file:
            private_key = RSA.import_key(priv_file.read())
        with open("public.pem", "rb") as pub_file:
            public_key = RSA.import_key(pub_file.read())
        print("Key was successfully loaded")
    except Exception as e:
        print(f"Error loading key pair: {e}")
        raise

    return private_key, public_key

# 키 암호화
def encryption_password(key):
    try:
        generate_key_pair()
        with open("public.pem", "rb") as pub_file:
            public_key = RSA.import_key(pub_file.read())
        encryption_key(key, public_key)
    except Exception as e:
        print(f"Error encrypting password: {e}")
        raise

def add_padding(base32_key):
    missing_padding = len(base32_key) % 8
    if missing_padding != 0:
        base32_key += '=' * (8 - missing_padding)
    return base32_key

# HOTP 생성
def hotp(key, counter, digits=6):
    try:
        key = base64.b32decode(add_padding(key)) # 패딩처리
        counter_bytes = struct.pack('>Q', counter)

        # HMAC-SHA1 20byte
        hmac_result = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # DT(dynamic truncation)
        offset = hmac_result[-1] & 0x0F 
        binary = ((hmac_result[offset] & 0x7F) << 24 | 
                (hmac_result[offset + 1] & 0xFF) << 16 |
                (hmac_result[offset + 2] & 0xFF) << 8 |
                (hmac_result[offset + 3] & 0xFF))
        otp = binary % (10 ** digits)
        return str(otp).zfill(digits)
    except Exception as e:
        print(f"Error generating HOTP: {e}")
        raise


# TOTP 생성
def totp(key, time_step=30, digits=6):
    try:
        current_time = int(time.time() // time_step)

        if current_time >= 2**64:
            raise ValueError("Time value exceeds 64-bit range")
        return hotp(key, current_time, digits)
    except Exception as e:
        print(f"Error generating TOTP: {e}")
        raise

# OTP 생성
def generate_otp(decrypted_key):
    try:
        base32_key = base64.b32encode(decrypted_key).decode().strip('=')
        otp = totp(base32_key)
        print(f"opt :  {otp}")
    except Exception as e:
        print(f"Error generating OTP: {e}")
        raise

# 메인 함수
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', type=str)
    parser.add_argument('-k', type=str)
    args = parser.parse_args()

    try:
        if args.g and args.k:
            print("Error: plz input only 1 argument")
            return 1
        if args.g:
            try:
                with open(args.g, 'r') as file:
                    hex_key = file.read().strip()
                if not check_hex_key(hex_key):
                    print("error: key must be 64 hexadecimal characters.")
                    return 1
                encryption_password(hex_key)
            except FileNotFoundError:
                print(f"Error: 파일 {args.g}을(를) 찾을 수 없습니다.")
                return 1
            except Exception as e:
                print(f"Error reading file {args.g}: {e}")
                return 1
        elif args.k:
            try:
                with open(args.k, 'rb') as file:
                    encrypted_key = file.read()
                private_key, public_key = load_key_pair()
                decrypted_key = decryption_key(private_key, encrypted_key)
                generate_otp(decrypted_key)
            except FileNotFoundError:
                print(f"Error: 파일 {args.g}을(를) 찾을 수 없습니다.")
                return 1
            except Exception as e:
                print(f"Error reading file {args.g}: {e}")
                return 1
        else:
            print("plz input argument")
            return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1

if __name__ == '__main__':
    main()