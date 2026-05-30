# Smartfarm Device

헥사보드(ESP32) 기반 스마트팜 IoT 디바이스.
DHT11 온습도 센서 데이터를 시리얼로 Mac에 전송 후 Supabase에 저장하고,
NeoPixel LED 원격 제어를 지원.

## 아키텍처

헥사보드(MicroPython) → USB 시리얼 → Mac Flask 서버 → Supabase → Next.js 웹앱

## 구성

- `main.py` — 헥사보드 펌웨어 (DHT11 읽기 + LED + LCD 제어)
- `server.py` — Mac에서 실행하는 Flask 서버
- `lcd_test.py`, `esp8266_i2c_lcd.py`, `lcd_api.py` — LCD 라이브러리

## 사용 하드웨어

- 헥사보드 (ESP32-D0WD-V3)
- DHT11 (PIN2 = GPIO33)
- NeoPixel LED 스트립 (PIN3 = GPIO4)
- 1602 LCD (I2C, 0x27)

## 설정

`.env` 파일 생성:
\`\`\`
SUPABASE_URL=...
SUPABASE_API_KEY=...
DEVICE_ID=...
\`\`\`

## 실행

\`\`\`bash
pip install -r requirements.txt
python3 server.py
\`\`\`