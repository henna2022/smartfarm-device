# ─────────────────────────────────────────
#  스마트팜 Python 서버 — Mac 버전
#  DHT11 + LED 제어
# ─────────────────────────────────────────

import serial
import sqlite3
import threading
import time
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Supabase 설정 ──────────────────────────
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL     = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
DEVICE_ID        = os.getenv("DEVICE_ID")

PORT     = "/dev/cu.usbserial-1140"
BAUDRATE = 115200
DB_FILE  = "smartfarm.db"

app = Flask(__name__)
CORS(app)

latest = {"temp": 0.0, "hum": 0.0, "ledOn": False, "fanOn": False, "updated": ""}
ser_lock = threading.Lock()
ser_obj = None  # 시리얼 객체 전역 보관


def post_to_supabase(temp, hum):
    try:
        res = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_readings",
            headers={
                "apikey": SUPABASE_API_KEY,
                "Authorization": f"Bearer {SUPABASE_API_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={"device_id": DEVICE_ID, "temp": temp, "hum": hum},
            timeout=5,
        )
        if res.status_code == 201:
            print("  [Supabase] 전송 완료")
        else:
            print(f"  [Supabase] 오류 {res.status_code}: {res.text}")
    except Exception as e:
        print(f"  [Supabase] 예외: {e}")


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temp      REAL,
            hum       REAL
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] 테이블 준비 완료")


def parse_line(line):
    try:
        data = {}
        for chunk in line.strip().split("|"):
            key, val = chunk.split(",")
            data[key.strip()] = val.strip()
        return data
    except Exception:
        return None


def serial_thread():
    global ser_obj
    print(f"[Serial] {PORT} 연결 시도 중...")
    try:
        ser_obj = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        print("[Serial] 연결 성공!\n")
    except Exception as e:
        print(f"[오류] 포트 연결 실패: {e}")
        return

    conn = sqlite3.connect(DB_FILE)
    while True:
        try:
            with ser_lock:
                raw = ser_obj.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            # LED 상태 확인 응답
            if raw.startswith("LED_STATE,"):
                state = raw.split(",")[1]
                latest["ledOn"] = (state == "ON")
                print(f"[LED] 상태 = {state}")
                continue

            # 센서 데이터
            data = parse_line(raw)
            if not data or "TEMP" not in data or "HUM" not in data:
                continue

            try:
                temp = float(data["TEMP"])
                hum  = float(data["HUM"])
            except ValueError:
                continue

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            latest["temp"]    = round(temp, 1)
            latest["hum"]     = round(hum, 1)
            latest["updated"] = ts

            conn.execute(
                "INSERT INTO sensor_log (timestamp, temp, hum) VALUES (?,?,?)",
                (ts, latest["temp"], latest["hum"])
            )
            conn.commit()
            print(f"[{ts}]  온도: {latest['temp']}°C  |  습도: {latest['hum']}%")
            post_to_supabase(latest["temp"], latest["hum"])

        except Exception as e:
            print(f"[오류] {e}")
            time.sleep(1)


def send_command(cmd):
    """헥사보드로 명령 전송 (LED:ON / LED:OFF 등)"""
    if ser_obj is None:
        return False
    try:
        with ser_lock:
            ser_obj.write((cmd + "\n").encode())
        return True
    except Exception as e:
        print(f"[Send 오류] {e}")
        return False


# ── REST API ──────────────────────────
@app.route("/api/latest")
def api_latest():
    return jsonify(latest)


@app.route("/api/blynk/read")
def api_read():
    """Next.js의 readSensors 호환 응답"""
    return jsonify({
        "temp": latest["temp"],
        "hum": latest["hum"],
        "soil": None,
        "ledOn": latest["ledOn"],
        "fanOn": latest["fanOn"],
        "ok": True,
    })


@app.route("/api/blynk/write", methods=["POST"])
def api_write():
    """Next.js의 writeActuator 호환"""
    body = request.get_json() or {}
    pin = body.get("pin")
    value = body.get("value")

    if pin == "led":
        cmd = "LED:ON" if value else "LED:OFF"
        ok = send_command(cmd)
        if ok:
            latest["ledOn"] = bool(value)
            return jsonify({"ok": True})
        return jsonify({"error": "전송 실패"}), 500

    if pin == "fan":
        # 추후 모터 제어 추가 예정
        latest["fanOn"] = bool(value)
        return jsonify({"ok": True})

    return jsonify({"error": "알 수 없는 pin"}), 400


@app.route("/api/history")
def api_history():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT timestamp, temp, hum FROM sensor_log ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    data = [{"timestamp": r[0], "temp": r[1], "hum": r[2]} for r in rows]
    return jsonify(data[::-1])


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=serial_thread, daemon=True)
    t.start()
    print("[Flask] 서버 시작: http://localhost:5001\n")
    app.run(port=5001, debug=False)