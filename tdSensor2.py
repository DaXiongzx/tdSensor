import RPi.GPIO as GPIO
import os
import serial
import subprocess
import requests
import sqlite3
import multiprocessing as mp
import socket
import time
#import duoji
#from duoji import duoji
import json
#import camera

create_sensor_table = '''create table sensor(
                            id integer primary key autoincrement,
                            temperature integer not null,
                            depth integer not null,
                            add_time text not null,
                            tag real not null)'''
create_log_table = ''' create table log(
                        id integer primary key autoincrement,
                        idValue integer not null)'''

def get_host_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(('8.8.8.8',80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip

def getAllPorts():
    l = subprocess.getoutput('ls /dev | grep ttyUSB').split('\n')
    l = ['/dev/'+i for i in l]
    return l

def testInternet():
    try:
        r = requests.get('http://www.baidu.com',timeout=1)
        r.raise_for_status()
    except Exception as e:
        print('error in testInternet',e)
        return False
    else:
        return True

def insertData(conn,cur,data):
    try:
        cur.execute('insert into sensor (temperature,depth,add_time,tag) values("%s","%s","%s","%s")'%(data[0],data[1],data[2],data[3]))
    except Exception as e:
        print(e)
        conn.rollback()
    else:
        conn.commit()


def sendDataToServer(res):
    if len(res)<5:
#        print('no value')
        return False
#    print('length:',len(res))
    stationId = 2
    try:
        with open('/home/pi/Desktop/stationId.txt') as f:
            stationId = f.read().strip()
    except Exception as e:
        print('error in sendDataToServer when read staionId',e)
#    print('this is in method',res)
    param = {'data':res,'stationId':stationId}
    url = 'http://47.110.230.61:8082/receiveData'
    try:
        r = requests.post(url,params=param,timeout=1)
        ret = json.loads(r.text)
        r.raise_for_status()
    except Exception as e:
        print('error in sendData to Serverssss:',e)
        return False
    else:
        if ret['code']==0:
            return True
        else:
            return False


def getData(ser):
    temperature = ''
    depth = ''
    dataDict = {}
    while True:
        try:
            if ser.read(1).decode() == 'T':
                ser.read(1)
                while True:
                    t = ser.read(1).decode()
                    if t != 'D':
                        temperature = temperature + t
                    else:
                        break
                ser.read(1)
                while True:
                    d = ser.read(1).decode()
                    if d != '\r':
                        depth = depth + d
                    else:
                        ser.read(1)
                        break
                dataDict = {'temperature': temperature, 'depth': depth}
        except Exception as e:
            print('error in read data from sensor and set the temperature=100',e)
            dataDict = {'temperature': '100', 'depth': '100'}
        ser.flush()
        return dataDict



def sendData(sendRate):
    selectId = 0
    currentTime = int(time.time())
    aitem = {}
    jsls = []
    sendRate.value = 60
    while True:
        if int(time.time())-currentTime>sendRate.value:
            currentTime = int(time.time()) 
            try:
                with open('/home/pi/Desktop/sendRate.txt') as f:
                    sendRate.value = int(f.read().strip())
#                    print('send rate',sendRate.value)
            except Exception as e:
                sendRate.value = 60
                print('error in set sendRate and set sendRate = 60',e)                      
            if testInternet():
                try:
                    conn = sqlite3.connect('/home/pi/tdSensor/tdSensor/logSensor.db')
                    cur = conn.execute('select * from sqlite_master where type="table"')
                    if not cur.fetchone():
                        conn.execute(create_sensor_table)
                    cur = conn.cursor()
                except Exception as e:
                    print('connect conn error',e)
                
                try:
                    conn2 = sqlite3.connect('/home/pi/tdSensor/tdSensor/logId.db')
                    cur2 = conn2.execute('select * from sqlite_master where type = "table"')
                    if not cur2.fetchone():
                        conn2.execute(create_log_table)
                        value = 0
                        cur2 = conn2.execute('insert into log (idValue) values("%s")' % value)  # initialize the table with the idValue 0
                        conn2.commit()
                    cur2 = conn2.cursor()
                except Exception as e:
                    print('error in connect conn2',e)
                
                try:
                    cur2.execute('select idValue from log order by id desc limit 1')  # find out the last id that has been sent to the server
                    rs = cur2.fetchall()
                    for row in rs:
                        selectId = row[0]
#                    print('selectId',selectId)
                except Exception as e:
                    print('error in read selectId',e)
                    
                try:
                    cur.execute('select * from sensor where id>{}'.format(selectId)) #find out the rows that have not been sent to the server
                    remainingRows = len(cur.fetchall())
#                    print('remaing rows',remainingRows)
                    while remainingRows>=100:
#                        print('send1')
                        cur.execute('select * from sensor where id >{} and tag = 0 limit 100'.format(selectId))
                        res = cur.fetchall()
                        for row in res:
                            aitem['temperature'] = row[1]
                            aitem['depth'] = row[2]
                            aitem['addTime'] = row[3]
                            
                            jsls.append(aitem)
                            aitem = {}
                        jsarr = json.dumps(jsls)
                        jsls = []
                        

                        if sendDataToServer(jsarr):  #send data to the server
                            selectId = selectId+100
                            remainingRows = remainingRows-100
                        else:
                            selectId = selectId
                            remainingRows = remainingRows

                    cur.execute('select * from sensor where id>{} and tag = 0 '.format(selectId))
                    res = cur.fetchall()
                    for row in res:
                        aitem['temperature'] = row[1]
                        aitem['depth'] = row[2]
                        aitem['addTime'] = row[3]
                        jsls.append(aitem)
                        aitem = {}
                    jsarr = json.dumps(jsls)                    
                    jsls = []
                    
                    if sendDataToServer(jsarr):
                        selectId =selectId+remainingRows
                        remainingRows = remainingRows-remainingRows
                    else:
                        selectId = selectId
                        remainingRows = remainingRows
                    try:
                        cur.execute('update sensor set tag = 1 where id< {}'.format(selectId))
                    except Exception as e:
                        print(e)
                        conn.rollback()
                    else:
                        conn.commit()
                        
                    try:
                        cur2.execute('insert into log (idValue) values("%s")'%selectId)
                    except Exception as e:
                        print(e)
                        conn2.rollback()
                    else:
                        conn2.commit()
    
                    conn.close()
                    conn2.close()
                except Exception as e:
                    print('error in select data from db and send it to the server',e)
                else:
                    continue
        else:
            continue

def recvConfirgurations():
    confirgurations = {}
    dirc={}
    stationId = 2
    try:
        with open('/home/pi/Desktop/stationId.txt') as f:
            stationId = f.read().strip()
    except Exception as e:
        print('error in read stationId')
    
    param = {'stationId': stationId}
    url = 'http://47.110.230.61:8082/getConfig'
    try:
        r = requests.post(url, params=param, timeout=1)
        r.raise_for_status()
        ret = json.loads(r.text)
#        print('ret',ret)
        data = ret['data']['rotateAngle']
        rotateAg = ret['data']['rotateAngle']
        rotateR =  ret['data']['rotateRate']
        collectR = ret['data']['collectRate']
        confirgurations = {'rotateAngle':rotateAg,'rotateRate':rotateR,'collectRate':collectR}
        
    except Exception as e:
        confirgurations = {'rotateAngle': 0, 'rotateRate': 1, 'collectRate': 30}
        print('error in receive info from Server:', e)
    else:
        
        return confirgurations




def readData(collectRate):
    ser = ''
    try:
        conn = sqlite3.connect('/home/pi/tdSensor/tdSensor/logSensor.db')
        cur = conn.execute('select * from sqlite_master where type="table"')
        if not cur.fetchone():
            conn.execute(create_sensor_table)
        cur = conn.cursor()
    except Exception as e:
        print('error in connect conn when readData',e)
    try:
        portList = getAllPorts()
        port=''
        for i in portList:
            ser = serial.Serial(i,baudrate=115200,timeout=1)
            msg = ser.read(16).decode()
            p1 = msg.find('T')
            p2 = msg.find('D')
            if p2-p1>5 and msg.find('=')!=-1:
                port=i
    except Exception as e:
        print('error in get ports',e)        
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=1)
    except Exception as e:
        print('error in get ser',e)
    tag = 0
    currentTimeI = int(time.time())
    while True:
        if int(time.time()) - currentTimeI > collectRate.value:
            currentTimeI = time.time()
            data = getData(ser)
            while len(data['temperature'])==0 or len(data['depth'])==0:
                data = getData(ser)
            temperature = data['temperature']
            depth = data['depth']
            addTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            
            L = [ temperature, depth, addTime, tag]
#            print('this is the data insert to db',L)
            insertData(conn, cur, L)
            
            
def sendRaspberryUpdateTime():
    stationId = 2
    updateTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    try:
        with open('/home/pi/Desktop/stationId.txt') as f:
            stationId = f.read().strip()
    except Exception as e:
        print('error in receive Id in updateTime',e)
    param = {'stationId': stationId,'time':updateTime}
    url = 'http://47.110.230.61:8082/raspberryUpdateTime'
    try:
        r = requests.post(url, params=param, timeout=1)
        r.raise_for_status()
    except Exception as e:
        print('error in send updateInfo to Server:', e)

def receiveInfoFromTxt():
    try:
        with open ('/home/pi/Desktop/Confirguration.txt') as f:
            jsInfo = f.read()
            InfoDict = json.loads(jsInfo)
    except Exception as e:
        InfoDict = {'collectRate': 30, 'rotateAngle': 0, 'rotateRate': 1}
        print('error in receive ConfigInfo from txt',e)
    else:
        return InfoDict

def writeInfoToTxt(InfoDict):
    try:
        with open('/home/pi/Desktop/Confirguration.txt','w') as f:
            jsInfo = json.dumps(InfoDict)
            f.write(jsInfo)
    except Exception as e:
        print('error in write configInfo to txt',e)

def takePicture(rotateRate):
    ot = time.time()
    while True:
        if time.time()-ot>rotateRate.value:
            ot = time.time()
            time.sleep(2)
            now = time.strftime("%m-%d-%H:%M:%S",time.localtime())
            #print("this is {}".format(now))
            try:
                os.system('fswebcam -d/dev/video0 -r 320*240 /home/pi/Desktop/Picture/{}.jpg'.format(now))
            except Exception as e:
                print('error in take picture',e)
        

def setDirection(rotateAngle,rotateRate):
    direction = 0
    zero_dutyCycle = 2.5#*0.64
    middle_dutyCycle = 7.5#*0.64
    right_dutyCycle = 12.5#*0.64
    delta = right_dutyCycle - zero_dutyCycle
    duty = delta/360 * direction + zero_dutyCycle
    P_SERVO = 7
    fPWM = 50
    #pwm.stop()
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(P_SERVO, GPIO.OUT)
    pwm = GPIO.PWM(P_SERVO, fPWM)
    pwm.start(zero_dutyCycle)
    
    print('pwm in method',pwm)
    #pwm.ChangeDutyCycle(duty)
    time.sleep(rotateRate.value)
    while True:
        if direction==360:
            continue
        direction = direction+rotateAngle.value
        print('direction',direction)
        duty = delta/360 * direction + zero_dutyCycle
        pwm.ChangeDutyCycle(duty)
        #direction = direction+rotateAngle.value
        if direction>=360:
            direction=360           
        time.sleep(rotateRate.value)

def udpListener(rotateAngle,rotateRate):
    duojiProcess=None
    zero_dutyCycle = 2.5#*0.64
    middle_dutyCycle = 7.5#*0.64
    right_dutyCycle = 12.5#*0.64
    delta = right_dutyCycle - zero_dutyCycle
    P_SERVO = 7
    fPWM = 50
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(P_SERVO, GPIO.OUT)
    pwm = GPIO.PWM(P_SERVO, fPWM)
    print('initial pwm',pwm)
    pwm.start(middle_dutyCycle)
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind(('0.0.0.0',9999))
    print('bind on 9999')
    while True:
        direction,addr = s.recvfrom(1024)
        changeDirectionstr = direction.decode()
        print('command to duoji',changeDirectionstr)
        
        if changeDirectionstr.find('?stopUdp')==0:
            pwm.stop()
            GPIO.cleanup()
            if duojiProcess and duojiProcess.is_alive():
                
                duojiProcess.terminate()
            duojiProcess = mp.Process(target=setDirection,args=(rotateAngle,rotateRate))
            duojiProcess.start()
        else:
            if duojiProcess and duojiProcess.is_alive():
                duojiProcess.terminate()
            if changeDirectionstr.find('?d')==0:
                print('changeFlag')
                udpFlag.value = 1
                directionValue = float(changeDirectionstr[2:])
                duty = delta/360 * directionValue + zero_dutyCycle
                pwm.ChangeDutyCycle(duty)
            else:
                #udpFlag.value=0
                print('else')



def changeCamera():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind(('0.0.0.0',8888))
    print('bind on 8888')
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
    #changeDirection(120)
    while True:
        print(udpFlag.value)
        chdirection,addr = s.recvfrom(1024)
        changeDirectionstr = chdirection.decode()
        #print('changeDirectionstr',changeDirectionstr)
        if changeDirectionstr.find('?')==0:
            directionValue = float(changeDirectionstr[2:])
            #print('directionValue',directionValue)
            changeDuty = cdelta/180 * directionValue + czero_dutyCycle
            #print('duty',changeDuty)
            cpwm.ChangeDutyCycle(changeDuty)
            #changeDirection(directionValue)

def main():
    duojiProcess=None
#    print('enter main')
    global rotateAngle
    global rotateRate
    global collectRate
    confirgurationInfo = {}
    ot = time.time()
    while True:
        if time.time()-ot>10:
            ot = time.time()
            if testInternet():
                try:
                    ipaddress = get_host_ip()
                except Exception as e:
                    ipaddress='127.0.0.1'
                try:
                    with open('/home/pi/Desktop/stationId.txt') as f:
                        stationId = f.read().strip()
                except Exception as e:
                    print('error in read stationid',e)
                    stationId = 2
                param = {'stationId': stationId,'ip':ipaddress}
                url = 'http://47.110.230.61:8082/updateIp'
                try:
                    r = requests.post(url,params=param,timeout=1) 
                except Exception as e:
                    print('error in send ip to Server',e)
                confirgurationInfo = recvConfirgurations()
#                print('confirguration',confirgurationInfo)
                writeInfoToTxt(confirgurationInfo)
                confirgurationInfo = receiveInfoFromTxt()
                try:
                    rotateAngle.value = confirgurationInfo['rotateAngle']
                    rotateRate.value = confirgurationInfo['rotateRate']
                    collectRate.value = float(confirgurationInfo['collectRate'])
                except Exception as e:
                    rotateAngle.value=60
                    rotateRate.value=10
                    collectRate.value=60
                sendRaspberryUpdateTime()

            

if __name__=="__main__":
    
    
    
    directionValue = mp.Value('f',0)
    udpFlag = mp.Value('i',0)
    collectRate = mp.Value('f',30)
    rotateAngle = mp.Value('f',0)
    rotateRate = mp.Value('f',1)
    sendRate = mp.Value('f',60)
    try:
        confirgurationInfo = receiveInfoFromTxt()
#        print('info',confirgurationInfo)   
        rotateAngle.value = confirgurationInfo['rotateAngle']
        rotateRate.value = confirgurationInfo['rotateRate']
        collectRate.value = float(confirgurationInfo['collectRate'])
        sendRaspberryUpdateTime()
    except Exception as e:
        rotateAngle.value = 0
        rotateRate.value = 1
        collectRate.value = 30
        print('error in receive conInfo in main',e)

    
    sendProcess = mp.Process(target=sendData,args=(sendRate,))
    sendProcess.daemon = True
    sendProcess.start()

    readProcess = mp.Process(target=readData,args=(collectRate,))
    readProcess.daemon = True
    readProcess.start()
    
    #Duoji = duoji()
    
    #duojiProcess = mp.Process(target=duoji.setDirection,args=(Duoji,rotateAngle,rotateRate,udpFlag))
    #duojiProcess.daemon = True
    #duojiProcess.start()
    
    takePictureProcess = mp.Process(target=takePicture,args=(rotateRate,))
    takePictureProcess.daemon = True
    takePictureProcess.start()
    
    udpProcess = mp.Process(target=udpListener,args=(rotateAngle,rotateRate))
    udpProcess.daemon = True
    udpProcess.start()
    
    chCameraProcess = mp.Process(target=changeCamera,args=())
    chCameraProcess.daemon = True
    chCameraProcess.start()

    main()
