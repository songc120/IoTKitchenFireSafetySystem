import RPi.GPIO as GPIO
import time

# 设置 GPIO 模式
GPIO.setmode(GPIO.BCM)

# 继电器控制的 GPIO 引脚
RELAY_PIN = 17

# 设置 GPIO17 为输出模式，初始状态为低电平（继电器断开）
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        # 启动风扇
        print("风扇开启")
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        time.sleep(5)  # 运行 5 秒

        # 关闭风扇
        print("风扇关闭")
        GPIO.output(RELAY_PIN, GPIO.LOW)
        time.sleep(5)  # 停止 5 秒

except KeyboardInterrupt:
    print("程序终止")
    GPIO.cleanup()  # 清理 GPIO 状态
