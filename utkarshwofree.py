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

STREAM_KEY = b"%!$!%_$&!%F)&^!^"
STREAM_IV  = b"#*y*#2yJ*#$wJv*v"

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

# ================= AES HELPERS =================

def _valid_key_iv(key, iv):
    return key and iv and len(key) == 16 and len(iv) == 16


def encrypt(data, use_common_key=False, key=None, iv=None):
    cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)

    if not _valid_key_iv(cipher_key, cipher_iv):
        raise Exception("Invalid AES key or IV")

    cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
    raw = json.dumps(data, separators=(",", ":")).encode()
    return b64encode(cipher.encrypt(pad(raw, AES.block_size))).decode() + ":"


def decrypt(data, use_common_key=False, key=None, iv=None):
    try:
        if not data or ":" not in data:
            return None

        cipher_key, cipher_iv = (COMMON_KEY, COMMON_IV) if use_common_key else (key, iv)
        if not _valid_key_iv(cipher_key, cipher_iv):
            return None

        cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
        encrypted = b64decode(data.split(":")[0])
        decrypted = cipher.decrypt(encrypted)

        return unpad(decrypted, AES.block_size).decode()

    except Exception:
        return None


def post_request(path, data=None, use_common_key=False, key=None, iv=None):
    payload = encrypt(data, use_common_key, key, iv) if data else data
    r = requests.post(API_URL + path, headers=HEADERS, data=payload)

    decrypted = decrypt(r.text, use_common_key, key, iv)
    if not decrypted:
        raise Exception("Invalid encrypted response from server")

    return json.loads(decrypted)

# ================= STREAM CRYPTO =================

def encrypt_stream(text):
    cipher = AES.new(STREAM_KEY, AES.MODE_CBC, STREAM_IV)
    return b64encode(cipher.encrypt(pad(text.encode(), AES.block_size))).decode()


def decrypt_stream(enc):
    try:
        if not enc or not isinstance(enc, str):
            return None

        raw = b64decode(enc)
        cipher = AES.new(STREAM_KEY, AES.MODE_CBC, STREAM_IV)
        decrypted = cipher.decrypt(raw)

        try:
            return unpad(decrypted, AES.block_size).decode("utf-8")
        except ValueError:
            return None

    except Exception:
        return None


def decrypt_and_load_json(enc):
    data = decrypt_stream(enc)
    if not data:
        raise Exception("Invalid or unencrypted server response")

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        raise Exception("Decrypted data is not valid JSON")

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
        raise Exception("Failed to get CSRF token")

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

    if "response" not in login_resp:
        raise Exception("Login failed (no response)")

    login_data = decrypt_and_load_json(login_resp["response"])

    if not isinstance(login_data, dict):
        raise Exception("Login failed (invalid response)")

    if "data" not in login_data or "jwt" not in login_data["data"]:
        raise Exception("Login failed (wrong credentials)")

    jwt = login_data["data"]["jwt"]
    HEADERS["jwt"] = jwt

    # ---------- PROFILE ----------
    profile = post_request("/users/get_my_profile", use_common_key=True)

    if not isinstance(profile, dict) or "data" not in profile:
        raise Exception("Failed to fetch profile")

    user_id = profile["data"]["id"]
    HEADERS["userid"] = user_id

    # ---------- USER KEY ----------
    key = "".join(key_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()
    iv  = "".join(iv_chars[int(i)] for i in (user_id + "1524567456436545")[:16]).encode()

    if not _valid_key_iv(key, iv):
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

    if "response" not in r:
        raise Exception("Invalid course response")

    course_data = decrypt_and_load_json(r["response"])

    if not isinstance(course_data, dict) or "data" not in course_data:
        raise Exception("No course data found")

    # ---------- SAVE OUTPUT ----------
    for course in course_data["data"]:
        title = course.get("title", "unknown")
        cid = course.get("id", "0")

        fname = f"{cid}_{title.replace('/','_').replace(':','_')}.txt"
        generated_files.append(fname)

        with open(fname, "w", encoding="utf-8") as f:
            f.write(title + "\n")

    return generated_files


# IMPORTANT: DO NOT AUTO RUN
if __name__ == "__main__":
    pass
