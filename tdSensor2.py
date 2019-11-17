import pickle

import serial
import subprocess
import requests
import sqlite3
import multiprocessing as mp
import socket
import time
#import duoji
import json

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
        #connected = 0
    else:
        return True
        #connected = 1

def insertData(conn,cur,data):
    #cur = conn.cursor()
    try:
        cur.execute('insert into sensor (temperature,depth,add_time,tag) values("%s","%s","%s","%s")'%(data[0],data[1],data[2],data[3]))
    except Exception as e:
        print(e)
        conn.rollback()
    else:
        conn.commit()


def sendDataToServer(res):
    param = {'data':res,'stationId':1}
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
        return dataDict



def sendData(collectRate):
    selectId = 0
    currentTime = int(time.time())
    aitem = {}
    jsls = []
    while True:
        conn = sqlite3.connect('logSensor.db')
        cur = conn.execute('select * from sqlite_master where type="table"')
        if not cur.fetchone():
            conn.execute(create_sensor_table)
        cur = conn.cursor()

        conn2 = sqlite3.connect('logId.db')
        cur2 = conn2.execute('select * from sqlite_master where type = "table"')
        if not cur2.fetchone():
            conn2.execute(create_log_table)
            value = 0
            cur2 = conn2.execute('insert into log (idValue) values(%s)' % value)  # initialize the table with the idValue 0
            conn2.commit()
        cur2 = conn2.cursor()
        cur2.execute('select idValue from log order by id desc limit 1')  # find out the last id that has been sent to the server
        rs = cur2.fetchall()
        for row in rs:
            selectId = row[0]

        if int(time.time())-currentTime>collectRate.value:
            currentTime = int(time.time())
            if testInternet():
                try:
                    cur.execute('select * from sensor where id>{}'.format(selectId)) #find out the rows that have not been sent to the server
                    remainingRows = len(cur.fetchall())
                    while remainingRows>=100:
                        cur.execute('select * from sensor where id >{} and tag = 0 limit 100'.format(selectId))
                        res = cur.fetchall()
                        for row in res:
                            aitem['temperature'] = row[1]
                            aitem['depth'] = row[2]
                            aitem['addTime'] = row[3]
                            jsls.append(aitem)
                        jsarr = json.dumps(jsls)

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
                    jsarr = json.dumps(jsls)
                    if sendDataToServer(jsarr):
                        selectId =selectId+remainingRows
                        remainingRows = remainingRows-remainingRows
                    else:
                        selectId = selectId
                        remainingRows = remainingRows

                    cur.execute('update sensor set tag = 1 where id< {}'.format(selectId))
                    conn.commit()
                    cur2.execute('insert into log (idValue) values("%s")'%selectId)
                    conn2.commit()
                except Exception as e:
                    print('error in select data from db and send it to the server',e)
                else:
                    continue
        else:
            continue
        conn.close()
        conn2.close()

def recvConfirgurations():
    dirc={}
    param = {'stationId': 1}
    url = 'http://47.110.230.61:8082/getConfig'
    try:
        r = requests.get(url, params=param, timeout=1)
        r.raise_for_status()
        ret = json.loads(r.text)
        data = ret['data']['rotateAngle']
        rotateAg = ret['data']['rotateAngle']
        rotateR =  ret['data']['rotateRate']
        collectR = ret['data']['collectRate']
        confirgurations = {'rotateAngle':rotateAg,'rotateRate':rotateR,'collectionRate':collectR}

    except Exception as e:
        print('error in receive info from Server:', e)
    else:
        return confirgurations




def readData(collectRate,currentTime):
    conn = sqlite3.connect('logSensor.db')
    cur = conn.execute('select * from sqlite_master where type="table"')
    if not cur.fetchone():
        conn.execute(create_sensor_table)
    cur = conn.cursor()

    port = 'COM5'
    ser = serial.Serial(port, baudrate=115200, timeout=1)
    tag = 0
    currentTimeI = int(time.time())
    while True:
        #print('read')
        if int(time.time() - currentTime.value > 1):
            data = getData(ser)
            temperature = data['temperature']
            depth = data['depth']
            addTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            print(addTime)
            L = [ temperature, depth, addTime, tag]
            insertData(conn, cur, L)

def main():
    print('enter main')
    global rotateAngle
    global rotateRate
    global collectRate
    confirgurationInfo = {}
    ot = time.time()
    while True:
        if time.time()-ot>300:
            confirgurationInfo = recvConfirgurations()
            rotateAngle.value = confirgurationInfo['rotateAngle']
            rotateRate.value = confirgurationInfo['rotateRate']
            collectRate.value = confirgurationInfo['collectRate']
            print(confirgurationInfo)
            ot = time.time()

if __name__=="__main__":
    rotateAngle = 0 #
    rotateRate = 1 #the seconds that use to control duoji
    #collectRate = 300 #the seconds that use to read and send the data

    collectRate = mp.Value('i',1)


    currentTime = mp.Value('i',int(time.time()))
    #currentTimeI = int(time.time())
    #selectId = 0
    #connected = 0
    #l = subprocess.getoutput('ls /dev | grep ttyUSB').split('\n')
    conn = sqlite3.connect('logSensor.db')
    cur = conn.execute('select * from sqlite_master where type="table"')
    if not cur.fetchone():
        conn.execute(create_sensor_table)
    cur = conn.cursor()

    conn2 = sqlite3.connect('logId.db')
    cur2 = conn2.execute('select * from sqlite_master where type = "table"')
    if not cur2.fetchone():
        conn2.execute(create_log_table)
        value = 0
        cur2 = conn2.execute('insert into log (idValue) values(%s)' %value) #initialize the table with the idValue 0
    cur2 = conn2.cursor()

    #portList = getAllPorts()
    #port = portList[0]
    port='COM5'
    '''for i in portList:
        ser = serial.Serial(i,baudrate=115200,timeout=1)
        msg = ser.read(16)
        p1 = msg.find('T')
        p2 = msg.find('D')
        if p2-p1>5 and msg.find('=')!=-1:
            port=i'''

    #ser = serial.Serial(port,baudrate=115200,timeout=1)

    sendProcess = mp.Process(target=sendData,args=(collectRate,))
    #sendProcess.daemon = True
    sendProcess.start()

    readProcess = mp.Process(target=readData,args=(collectRate,currentTime))
    #readProcess.daemon = True
    readProcess.start()

    '''duojiProcess = mp.process(target=duoji.setDirection,args=(rotateAngle,rotateRate))
    duojiProcess.daemon = True
    duojiProcess.start()'''

    main()