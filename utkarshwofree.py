import requests
import json
import base64
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ================= CONFIG =================

API_URL = "https://application.utkarshapp.com/index.php/data_model"

COMMON_KEY = b"%!^F&^$)&^$&*$^&"   # 16 bytes
COMMON_IV  = b"#*v$JvywJvyJDyvJ"   # 16 bytes

key_chars = "%!F*&^$)_*%3f&B+"
iv_chars  = "#*$DJvyw2w%!_-$@"

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

def encrypt(data, use_common_key=False, key=None, iv=None):
    cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)

    if not cipher_key or not cipher_iv or len(cipher_key) != 16 or len(cipher_iv) != 16:
        raise Exception("Invalid AES key/IV length")

    cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
    padded = pad(json.dumps(data, separators=(",", ":")).encode(), AES.block_size)
    return b64encode(cipher.encrypt(padded)).decode() + ":"


def decrypt(data, use_common_key=False, key=None, iv=None):
    try:
        if not data or ":" not in data:
            return None

        cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)

        if not cipher_key or not cipher_iv or len(cipher_key) != 16 or len(cipher_iv) != 16:
            return None

        cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
        encrypted = b64decode(data.split(":")[0])
        decrypted = cipher.decrypt(encrypted)

        return unpad(decrypted, AES.block_size).decode()

    except ValueError:
        # Padding error
        return None
    except Exception:
        return None


def post_request(path, data=None, use_common_key=False, key=None, iv=None):
    encrypted_data = encrypt(data, use_common_key, key, iv) if data else data
    r = requests.post(API_URL + path, headers=HEADERS, data=encrypted_data)

    decrypted = decrypt(r.text, use_common_key, key, iv)
    if not decrypted:
        raise Exception("Decryption failed (invalid padding or response)")

    return json.loads(decrypted)


# ---------- STREAM ENCRYPT / DECRYPT ----------

STREAM_KEY = b'%!$!%_$&!%F)&^!^'
STREAM_IV  = b'#*y*#2yJ*#$wJv*v'

def encrypt_stream(text):
    cipher = AES.new(STREAM_KEY, AES.MODE_CBC, STREAM_IV)
    return b64encode(cipher.encrypt(pad(text.encode(), AES.block_size))).decode()

def decrypt_stream(enc):
    try:
        cipher = AES.new(STREAM_KEY, AES.MODE_CBC, STREAM_IV)
        decrypted = cipher.decrypt(b64decode(enc))
        return unpad(decrypted, AES.block_size).decode(errors="ignore")
    except Exception:
        return None

def decrypt_and_load_json(enc):
    data = decrypt_stream(enc)
    if not data:
        raise Exception("Stream decryption failed")
    return json.loads(data)

# ================= MAIN FUNCTION =================

def run_script(email, password, batch_id):
    """
    Telegram-safe function
    Returns list of generated .txt files
    """

    session = requests.Session()
    generated_files = []

    # ---------- CSRF ----------
    r = session.get("https://online.utkarsh.com/")
    csrf = r.cookies.get("csrf_name")
    if not csrf:
        raise Exception("CSRF token not found")

    # ---------- LOGIN ----------
    login_payload = {
        "csrf_name": csrf,
        "mobile": email,
        "password": password,
        "url": "0",
        "submit": "LogIn",
        "device_token": "null"
    }

    login_headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }

    login_resp = session.post(
        "https://online.utkarsh.com/web/Auth/login",
        data=login_payload,
        headers=login_headers
    ).json()

    login_data = decrypt_and_load_json(login_resp.get("response"))
    jwt = login_data["data"]["jwt"]
    HEADERS["jwt"] = jwt

    # ---------- PROFILE ----------
    profile = post_request("/users/get_my_profile", use_common_key=True)
    user_id = profile["data"]["id"]
    HEADERS["userid"] = user_id

    # ---------- USER KEY ----------
    key = "".join(key_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()
    iv  = "".join(iv_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()

    if len(key) != 16 or len(iv) != 16:
        raise Exception("Generated AES key/IV invalid")

    # ---------- COURSE DATA ----------
    tiles_url = "https://online.utkarsh.com/web/Course/tiles_data"

    payload = {
        "course_id": batch_id,
        "layer": 1,
        "page": 1,
        "parent_id": 0,
        "type": "course_combo"
    }

    enc = encrypt_stream(json.dumps(payload))
    r = session.post(
        tiles_url,
        data={"tile_input": enc, "csrf_name": csrf}
    ).json()

    data = decrypt_and_load_json(r.get("response"))

    # ---------- SAVE OUTPUT ----------
    for course in data.get("data", []):
        fname = f"{course['id']}_{course['title'].replace('/','_')}.txt"
        generated_files.append(fname)

        with open(fname, "w", encoding="utf-8") as f:
            f.write(course["title"] + "\n")

    return generated_files


# DO NOT AUTO RUN
if __name__ == "__main__":
    pass
