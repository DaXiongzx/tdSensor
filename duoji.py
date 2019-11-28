import RPi.GPIO as GPIO
import time
import os

def setDirection(rotateAngle,rotateRate,udpFlag):
    global direction
    P_SERVO = 7
    fPWM = 50
    zero_dutyCycle = 2.5#*0.64
    middle_dutyCycle = 7.5#*0.64
    right_dutyCycle = 12.5#*0.64
    delta = right_dutyCycle - zero_dutyCycle
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(P_SERVO, GPIO.OUT)
    GPIO.setwarnings(False)
    pwm = GPIO.PWM(P_SERVO, fPWM)
    pwm.start(zero_dutyCycle)
    direction = 0
    reverse = 0
    while True:
        if udpFlag.value==0:
            duty = delta/360 * direction + zero_dutyCycle   
            pwm.ChangeDutyCycle(duty)
            os.system('gpio pwm {} {}'.format(P_SERVO,round((right_dutyCycle-zero_dutyCycle)/360*direction+zero_dutyCycle)*9600/100))
            direction = direction+rotateAngle.value
            if direction>=360:
                direction=360                    
            time.sleep(rotateRate.value)



def changeDirection(directionValue):
    global direction
    direction = directionValue
    changeDuty = delta/360 * directionValue + zero_dutyCycle
    pwm.ChangeDutyCycle(changeDuty)
#           

P_SERVO = 7
fPWM = 50
direction = 0
zero_dutyCycle = 2.5#*0.64
middle_dutyCycle = 7.5#*0.64
right_dutyCycle = 12.5#*0.64
delta = right_dutyCycle - zero_dutyCycle
GPIO.setmode(GPIO.BOARD)
GPIO.setup(P_SERVO, GPIO.OUT)
GPIO.setwarnings(False)
pwm = GPIO.PWM(P_SERVO, fPWM)
pwm.start(zero_dutyCycle)
#setDirection2(30,10)







