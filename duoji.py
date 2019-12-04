import RPi.GPIO as GPIO
import time
import os
import socket
import multiprocessing as mp


def setDirection(pwm,rotateAngle,rotateRate):
    direction = 0
    zero_dutyCycle = 2.5#*0.64
    middle_dutyCycle = 7.5#*0.64
    right_dutyCycle = 12.5#*0.64
    delta = right_dutyCycle - zero_dutyCycle
    print('delta',delta)
    duty = delta/360 * direction + zero_dutyCycle
    pwm = pwm
    print('pwm in duoji method',pwm)
    pwm.ChangeDutyCycle(duty)
    time.sleep(rotateRate.value)
    while True:
        pwm = pwm
        print('pwm in duoji method',pwm)
        if direction==360:
            continue
        direction = direction+rotateAngle.value
        #print('direction',direction)
        duty = delta/360 * direction + zero_dutyCycle
        pwm.ChangeDutyCycle(duty)
        direction = direction+rotateAngle.value
        if direction>=360:
            direction=360           
        time.sleep(rotateRate.value)
 
def setDirection2(Duoji,direction):
    #Duoji=duoji()
    Duoji.changeDirection(direction)
    while True:
        print('enter 2')
        Duoji.changeDirection(direction)
        direction = direction+30
        if direction>=360:
            direction=360
            reverse = 1
        
        time.sleep(1)

def setDirection3(direction):
    global pwm
    directionValue = direction
    zero_dutyCycle = 2.5#*0.64
    middle_dutyCycle = 7.5#*0.64
    right_dutyCycle = 12.5#*0.64
    delta = right_dutyCycle - zero_dutyCycle
    while True:
        print(directionValue)
        duty = delta/360 * directionValue + zero_dutyCycle
        pwm.ChangeDutyCycle(duty)
        directionValue = directionValue+30
        if directionValue>=360:
            directionValue=360
            
        
        time.sleep(1)














