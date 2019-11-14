import RPi.GPIO as GPIO
import time



P_SERVO = 7
fPWM = 50
zero_dutyCycle = 2.5
middle_dutyCycle = 7.5
right_dutyCycle = 12.5
delta = right_dutyCycle - zero_dutyCycle
GPIO.setmode(GPIO.BOARD)
GPIO.setup(P_SERVO, GPIO.OUT)
pwm = GPIO.PWM(P_SERVO, fPWM)
pwm.start(zero_dutyCycle)

def setDirection(addirection,sleeptime):
    direction = 0
    reverse = 0
    while True:
        if reverse==0:
            duty = delta/180 * direction + zero_dutyCycle
            pwm.ChangeDutyCycle(duty)
            direction = direction+addirection
            if direction==360:
                reverse = 1
        if reverse==1:
            duty = delta/180 * direction + zero_dutyCycle
            pwm.ChangeDutyCycle(duty)
            direction = direction - addirection
            if direction==0:
                reverse = 0




