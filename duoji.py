import RPi.GPIO as GPIO
import time


def setDirection(rotateAngle,rotateRate):
    P_SERVO = 37
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
    while True:
        print('direction',direction)
        if reverse==0:
            duty = delta/360 * direction + zero_dutyCycle
            print(duty)
            print(reverse)
            pwm.ChangeDutyCycle(duty)
            direction = direction+rotateAngle.value
            if direction==360+rotateAngle.value:
                reverse = 1
        if reverse==1:
            duty = delta/360 * direction + zero_dutyCycle
            print(duty)
            print(reverse)
            pwm.ChangeDutyCycle(duty)
            direction = direction - rotateAngle.value
            if direction==0-rotateAngle.value:
                reverse = 0
                
        
        time.sleep(2)


#setDirection(30,10)







