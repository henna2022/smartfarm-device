import dht
import machine
import neopixel
import utime
import sys
import select
from esp8266_i2c_lcd import I2cLcd

# ── 센서 & LED 설정 ─────────────────────
sensor = dht.DHT11(machine.Pin(33))  # PIN2 = GPIO33

LED_COUNT = 30
led_strip = neopixel.NeoPixel(machine.Pin(4), LED_COUNT)  # PIN3 = GPIO4

# ── LCD 초기화 ─────────────────────────
i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("Henna's berries")

led_on = False

def set_led(on):
    global led_on
    led_on = on
    color = (80, 80, 60) if on else (0, 0, 0)
    for i in range(LED_COUNT):
        led_strip[i] = color
    led_strip.write()

def update_lcd(temp, hum):
    """2번째 줄에 온습도 표시"""
    lcd.move_to(0, 1)
    line = "T:{}C  H:{}%".format(int(temp), int(hum))
    # 16자에 맞춰 빈 칸 채우기
    while len(line) < 16:
        line = line + " "
    lcd.putstr(line)

# ── 시리얼 입력 비동기 처리 ──────────────
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

last_sensor_time = 0

while True:
    # Mac 명령 처리
    if poll.poll(0):
        line = sys.stdin.readline().strip()
        if line == "LED:ON":
            set_led(True)
            print("LED_STATE,ON")
        elif line == "LED:OFF":
            set_led(False)
            print("LED_STATE,OFF")

    # 센서 + LCD 갱신
    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_sensor_time) >= 2000:
        last_sensor_time = now
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            print("TEMP," + str(temp) + "|HUM," + str(hum))
            update_lcd(temp, hum)
        except Exception as e:
            print("ERR:", e)

    utime.sleep_ms(50)