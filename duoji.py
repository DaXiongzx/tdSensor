import RPi.GPIO as GPIO
import time
import os

def setDirection(rotateAngle,rotateRate):
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
#        print('direction',direction)
#        print('rotateRate',rotateRate.value)
        if reverse==0:
            duty = delta/360 * direction + zero_dutyCycle
#            print(duty)
#            print(reverse)
            pwm.ChangeDutyCycle(duty)
            os.system('gpio pwm {} {}'.format(P_SERVO,round((right_dutyCycle-zero_dutyCycle)/360*direction+zero_dutyCycle)*9600/100))
            direction = direction+rotateAngle.value
            if direction>=360:
#                time.sleep(rotateRate.value)
                #pwm.ChangeDutyCycle(right_dutyCycle)
                direction=360
                reverse = 1
        if reverse==1:
            duty = delta/360 * direction + zero_dutyCycle
#            print(duty)
#            print(reverse)
            pwm.ChangeDutyCycle(duty)
            os.system('gpio pwm {} {}'.format(P_SERVO,round((right_dutyCycle-zero_dutyCycle)/360*direction+zero_dutyCycle)*9600/100))
            direction = direction - rotateAngle.value
            if direction<=0:
#                time.sleep(rotateRate.value)
#                pwm.ChangeDutyCycle(zero_dutyCycle)
                direction=0
                reverse = 0
                
        
        time.sleep(rotateRate.value)



def setDirection2(rotateAngle,rotateRate):
    P_SERVO = 7
    fPWM = 50
    zero_dutyCycle = 2.5
    middle_dutyCycle = 7.5
    right_dutyCycle = 12.5
    delta = right_dutyCycle - zero_dutyCycle
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(P_SERVO, GPIO.OUT)
    GPIO.setwarnings(False)
    pwm = GPIO.PWM(P_SERVO, fPWM)
    pwm.start(zero_dutyCycle)
    direction = 0
    reverse = 0
    os.system('gpio pwm {} {}'.format(P_SERVO,round(zero_dutyCycle * 9600 / 100)))
    while True:
        print('direction',direction)
        if reverse==0:
            duty = delta/360 * direction + zero_dutyCycle
            print(duty)
            print(reverse)
            pwm.ChangeDutyCycle(duty)
#            os.system('gpio pwm {} {}'.format(P_SERVO,round(duty)*9600/100))
            direction = direction+rotateAngle
            if direction==360+rotateAngle:
                reverse = 1
        if reverse==1:
            duty = delta/360 * direction + zero_dutyCycle
            print(duty)
            print(reverse)
            pwm.ChangeDutyCycle(duty)
#            os.system('gpio pwm {} {}'.format(P_SERVO,round(duty)*9600/100))
            direction = direction - rotateAngle
            if direction==0-rotateAngle:
                reverse = 0
                
        
        time.sleep(2)


#setDirection2(30,10)







