import serial
import subprocess
import requests
import sqlite3
import multiprocessing as mp
import socket
import time
import duoji

create_sensor_table = '''create table sensor(
                            id integer not null,
                            temperature integer not null,
                            depth integer not null,
                            time real not null,
                            tag real not null)'''
create_log_table=''' create log(
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
        cur.execute('insert into sensor values(%s)' %data)
    except Exception as e:
        print(e)
        conn.rollback()
    else:
        conn.commit()
#def updateData(conn,cur):


def sendDataToServer(res):
    rasIp = get_host_ip()
    param = {'data' :res,'rasIp':rasIp}
    url=None
    try:
        r = requests.get(url,params=param,timeout=1)
        r.raise_for_status()
    except Exception as e:
        print('error in sendData to Server:',e)
        return False
    else:
        return True

def readData(ser):
    byteList = ser.read(16)
    return byteList.decode()

def getData(ser):
    data = {}
    strList = readData(ser)
    tPosition = strList.find('T')
    dPosition = strList.find('D')
    temperature = strList[tPosition+1:dPosition]
    depth = strList[dPosition+1:]
    data = {'temperature' : temperature,'depth':depth}
    return data



def sendData(cur,cur2):
    global currentTime
    global selectId
    global actime
    #currentTime = int(time.time())
    selectId = cur2.execute('select idValue from log order by id desc limit 1')[0] #find out the last id that has been sent to the server
    while True:
        if int(time.time())-currentTime>actime:
            if testInternet():
                try:
                    rows = cur.execute('select * from sensor where id>{}'.format(selectId)) #find out the rows that have not been sent to the server
                    rowsNumber = len(rows)
                    remainingRows = len(rows)
                    while remainingRows>=100:
                        cur.execute('select * from sensor where id >{} and tag = 0 limit 100'.format(selectId))
                        res = cur.fetchall()
                        sendDataToServer(res)  #send data to the server
                        selectId = selectId+100
                        remainingRows = remainingRows-100

                    cur.execute('select * from sensor where id>{} and tag = 0 '.format(selectId))
                    res = cur.fetchall()
                    sendDataToServer(res)
                    selectId =selectId+remainingRows
                    remainingRows = remainingRows-remainingRows

                    cur.execute('update sensor set tag = 1 where id< {}'.format(selectId))
                    cur2.execute('insert into log values(%s)'%selectId)
                except Exception as e:
                    print('error in select data from db and send it to the server',e)
                else:
                    continue

        else:
            currentTime = int(time.time())
            continue


def getConfiguration(s):
    while True:
        conInformation,addr = s.recv(1024)
        conInformation = conInformation.split()


def readData(ser):
    global actime
    id = 0
    tag = 0
    currentTimeI = int(time.time())
    while True:
        if int(time.time() - currentTime > actime):
            data = getData(ser)
            temperature = data['temperature']
            depth = data['depth']
            L = [id, temperature, depth, int(time.time()), tag]
            insertData(conn, cur, L)
            id = id + 1

def main():
    global addirection
    global sleeptime
    global actime
    while True:
        #accpet the configure information
        conf, addr = s.recvfrom(1024)
        strConf = conf.decode()
        lstrConf = strConf.split()
        sleeptime= int(lstrConf[0])
        addirection = int(lstrConf[1])
        actime = int(lstrConf[2])







if __name__=="__main__":
    addirection = 0 #
    sleeptime = 1 #the seconds that use to control duoji
    actime = 0 #the seconds that use to read and send the data


    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    Host = '127.0.0.1'
    Port = 9999
    s.bind((Host,Port))

    currentTime = int(time.time())
    #currentTimeI = int(time.time())
    selectId = 0
    #connected = 0
    l = subprocess.getoutput('ls /dev | grep ttyUSB').split('\n')
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

    portList = getAllPorts()
    port = portList[0]
    for i in portList:
        ser = serial.Serial(i,baudrate=115200,timeout=1)
        msg = ser.read(16)
        p1 = msg.find('T')
        p2 = msg.find('D')
        if p2-p1>5 and msg.find('=')!=-1:
            port=i

    ser = serial.Serial(port,baudrate=115200,timeout=1)

    sendProcess = mp.process(target=sendData,args=(cur,))
    sendProcess.daemon = True
    sendProcess.start()

    readProcess = mp.process(targer=readData,args=(ser,))
    readProcess.daemon = True
    readProcess.start()

    duojiProcess = mp.process(target=duoji.setDirection,args=(addirection,sleeptime))
    duojiProcess.daemon = True
    duojiProcess.start()

    main()