import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from base64 import b64decode, b64encode
import base64

# ================= CONFIG =================

API_URL = "https://application.utkarshapp.com/index.php/data_model"
COMMON_KEY = b"%!^F&^$)&^$&*$^&"
COMMON_IV = b"#*v$JvywJvyJDyvJ"
key_chars = "%!F*&^$)_*%3f&B+"
iv_chars = "#*$DJvyw2w%!_-$@"

HEADERS = {
    "Authorization": "Bearer 152#svf346t45ybrer34yredk76t",
    "Content-Type": "text/plain; charset=UTF-8",
    "devicetype": "1",
    "host": "application.utkarshapp.com",
    "lang": "1",
    "user-agent": "okhttp/4.9.0",
    "userid": "0",
    "version": "152"
}

# ================= CRYPTO =================

def encrypt(data, use_common_key, key, iv):
    cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)
    cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
    padded = pad(json.dumps(data, separators=(",", ":")).encode(), AES.block_size)
    return b64encode(cipher.encrypt(padded)).decode() + ":"

def decrypt(data, use_common_key, key, iv):
    cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)
    cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
    encrypted = b64decode(data.split(":")[0])
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode()

def post_request(path, data=None, use_common_key=False, key=None, iv=None):
    enc = encrypt(data, use_common_key, key, iv) if data else data
    r = requests.post(API_URL + path, headers=HEADERS, data=enc)
    return json.loads(decrypt(r.text, use_common_key, key, iv))

def decrypt_stream(enc):
    key = b'%!$!%_$&!%F)&^!^'
    iv = b'#*y*#2yJ*#$wJv*v'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(b64decode(enc))
    return unpad(decrypted, AES.block_size).decode(errors="ignore")

def decrypt_and_load_json(enc):
    return json.loads(decrypt_stream(enc))

def encrypt_stream(txt):
    key = b'%!$!%_$&!%F)&^!^'
    iv = b'#*y*#2yJ*#$wJv*v'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return b64encode(cipher.encrypt(pad(txt.encode(), AES.block_size))).decode()

# ================= MAIN LOGIC =================

def run_script(email, password, batch_id):
    """
    Runs extractor and returns list of generated txt files
    """

    session = requests.Session()
    generated_files = []

    # ---------- CSRF ----------
    csrf = session.get("https://online.utkarsh.com/").cookies.get("csrf_name")
    if not csrf:
        raise Exception("CSRF token not found")

    # ---------- LOGIN ----------
    login_url = "https://online.utkarsh.com/web/Auth/login"
    payload = {
        "csrf_name": csrf,
        "mobile": email,
        "password": password,
        "url": "0",
        "submit": "LogIn",
        "device_token": "null"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }

    resp = session.post(login_url, data=payload, headers=headers).json()
    data = decrypt_and_load_json(resp["response"])

    HEADERS["jwt"] = data["data"]["jwt"]

    # ---------- PROFILE ----------
    profile = post_request("/users/get_my_profile", use_common_key=True)
    user_id = profile["data"]["id"]
    HEADERS["userid"] = user_id

    key = "".join(key_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()
    iv = "".join(iv_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()

    # ---------- COURSE ----------
    tiles_url = "https://online.utkarsh.com/web/Course/tiles_data"

    payload = {
        "course_id": batch_id,
        "layer": 1,
        "page": 1,
        "parent_id": 0,
        "type": "course_combo"
    }

    enc = encrypt_stream(json.dumps(payload))
    r = session.post(tiles_url, data={"tile_input": enc, "csrf_name": csrf}).json()
    data = decrypt_and_load_json(r["response"])

    for course in data["data"]:
        filename = f"{course['id']}_{course['title'].replace('/','_')}.txt"
        generated_files.append(filename)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(course["title"] + "\n")

    return generated_files


# IMPORTANT: DO NOT AUTO-RUN
if __name__ == "__main__":
    pass
