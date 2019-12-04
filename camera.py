import RPi.GPIO as GPIO
import time
import os

def changeDirection(directionValue):
    global cpwm
    global cdelta
    global czero_dutyCycle
    direction = 0
    direction = directionValue
    changeDuty = cdelta/180 * direction + czero_dutyCycle
    print('duty',changeDuty)
    cpwm.ChangeDutyCycle(changeDuty)

cP_SERVO = 11
cfPWM = 50

czero_dutyCycle = 2.5#*0.64
cmiddle_dutyCycle = 7.5#*0.64
cright_dutyCycle = 12.5#*0.64
cdelta = cright_dutyCycle - czero_dutyCycle
GPIO.setmode(GPIO.BOARD)
GPIO.setup(cP_SERVO, GPIO.OUT)
GPIO.setwarnings(False)
cpwm = GPIO.PWM(cP_SERVO, cfPWM)
cpwm.start(czero_dutyCycle)
#time.sleep(2)
changeDirection(120)
