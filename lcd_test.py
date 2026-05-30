import machine
from esp8266_i2c_lcd import I2cLcd

# 헥사보드 I2C 핀 (일반적인 ESP32 기본 I2C: SDA=21, SCL=22)
i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)

# I2C 디바이스 주소 스캔
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])

# LCD 초기화 (주소는 보통 0x27 또는 0x3F)
if devices:
    addr = devices[0]
    lcd = I2cLcd(i2c, addr, 2, 16)
    lcd.clear()
    lcd.putstr("Henna's berries")
    print("LCD 출력 완료!")
else:
    print("I2C 디바이스 못 찾음!")
    