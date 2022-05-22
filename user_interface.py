from flask import Flask, render_template, request, url_for, flash, redirect
import paho.mqtt.client as mqtt
import re, os
import pymysql, time
from DBComs import DBComs
from PolyRegression import PolyRegression
import threading
from TempAPI import TempAPI

intRe = re.compile('(?P<num>^\d+$)')
msgRe = re.compile('{"state":"(?P<state>[a-zA-Z_]+)","pirOutput":"(?P<pirOutput>[a-zA-Z_]+)","color":"(?P<color>[0-9,]+)"}')

app = Flask(__name__)

ml = PolyRegression()

deanHost = 'localhost'
alexHost = '192.168.43.118'
jaredHost = '192.168.43.5'

fanOveride = '0'

temp = 0
doorState = 0
lastDoorOpenTime = 0
openDoorTriggered = True

pirState = None

mqttAlex = None

realTemp = 0
tempAPI = TempAPI()
#db = DBComs(
#    host=deanHost,
#    user='pi',
#    pwd='',
#    dbName='smarthome'
#)

db = pymysql.connect(
    host='127.0.0.1',
    user='pi',
    password='',
    database='smarthome',
    cursorclass=pymysql.cursors.DictCursor
) or die('failed')

def pollTempAPI():
    while True:
        global realTemp
        realTemp = tempAPI.getTemp()
        #print(realTemp)
        time.sleep(2)

def on_message(client, userdata, message):
    topic = message.topic
    msg = message.payload.decode()
    
    global fanOveride
    global temp
    global doorState
    global realTemp
    global lastDoorOpenTime
    global openDoorTriggered
        
    if topic == 'topic/temperature':
        print('topic: {}, message: {}'.format(topic, msg))
        
        temp = float(message.payload.decode("utf-8"))
        
        #mqttDean.publish("topic/fanstate","0")
        #print('fs: ', fanOveride)
        #print(type(msg))
        msg = float(msg)
        if ((doorState == 0 and temp > 21) or temp > 29) and fanOveride == '0':
            mqttDean.publish("topic/fanstate","ON")
        elif fanOveride == '1':
            mqttDean.publish("topic/fanstate","ON")
        else:
            mqttDean.publish("topic/fanstate","OFF")
                    
        temp = str(message.payload.decode("utf-8"))
        
        colData = [time.time(), temp]
        cols = ['_time', 'temperature']
        command = 'INSERT INTO templog (_time, temperature) VALUES ({}, {})'.format(colData[0], colData[1])
        #print(command)
        c = db.cursor()
        c.execute(command)
        db.commit()
        
        
        
        
        
        
    elif topic == 'webserver/doorState':
        print('topic: {}, message: {}'.format(topic, msg))
        #print(1)

        msg = int(msg)
        print('msg: ', msg)
        print('ds: ', doorState)

        # reset time if state has changed, and door state is set to open
        setTime = msg != doorState and msg == 0
        doorState = msg
        if setTime:
            print('new')
            lastDoorOpenTime = time.time()
            openDoorTriggered = True
        else:
            if openDoorTriggered:
                # if door is opened
                print('allow')
                if doorState == 0:
                    print('{} - {}'.format(time.time(), lastDoorOpenTime))
                    timeElapsed = time.time() - lastDoorOpenTime > 3
                    if timeElapsed:
                        print('time elapsed')
                        if abs(float(realTemp) - float(temp)) > 12:
                            print('temp cond met')
                            mqttJared.publish('edge/doorState', 'close')
                            openDoorTriggered = False
                            print('pub')
                        else:
                            print('temp cond not met')
                    else:
                        print('waiting')

            
        if doorState == 0:
            #print('opening')
            mqttAlex.publish('lighting/on', 'e', qos=0)
            #print('open')
    elif topic == 'webserver/lighting':
        print('topic: {}, message: {}'.format(topic, msg))
    else:
        print('err')
        print(topic)

mqttSub = mqtt.Client()
mqttSub.on_message = on_message
mqttSub.connect(deanHost)
mqttSub.subscribe('topic/temperature', 0)
mqttSub.subscribe('webserver/lighting', 0)
mqttSub.subscribe('webserver/doorState', 0)
mqttSub.loop_start()

# Dean's Node
mqttDean = mqtt.Client() 
mqttDean.connect(deanHost)
#mqttDean.subscribe('topic/temperature', 0)
mqttDean.loop_start() 


# Alex's Node
mqttAlex = mqtt.Client()
mqttAlex.connect(alexHost)
#mqttAlex.subscribe('webserver/lighting', 0)
mqttAlex.loop_start()

# Jared's Node
mqttJared = mqtt.Client()
mqttJared.connect(jaredHost)
mqttJared.subscribe('webserver/doorState', 0)
mqttJared.loop_start()

apiThread = threading.Thread(target=pollTempAPI)
apiThread.start()

def predictTemp():
    tempDB = pymysql.connect(
        host='127.0.0.1',
        user='pi',
        password='',
        database='smarthome',
        cursorclass=pymysql.cursors.DictCursor
    ) or die('failed')
    cursor = tempDB.cursor()
    command = 'SELECT * FROM templog ORDER BY id DESC LIMIT 100'
    cursor.execute(command)
    rows = cursor.fetchall()

    #print(rows)
    x = []
    y = []
    for row in rows:
        x.append(float(row['_time']))
        y.append(float(row['temperature']))

    minTime = min(x)
    for i in range(len(x)):
        x[i] -= minTime - 1

    print(x)
    print(y)

    pr = PolyRegression()
    model = pr.predict(x, y, 'fig')
    #if os.path.exists('static/fig.png'):
    #    print('file exists, deleting')
    #    os.system('rm static/fig.png')
    #    os.system('rm fig.png')
    os.system('mv fig.png static/')

@app.route('/')
def index():
    ctx = {
       'data' : {
           'apiTemp' : realTemp
        }
    }
    return render_template('index.html', **ctx)
    
@app.route('/mlTemp')
def mlTemp():
    predictTemp()
    
    return home()

def home():
    return redirect(url_for('index'))

@app.route('/fanPub', methods=('GET', 'POST'))
def fanPub():
    global fanOveride
    if request.method == 'POST':
        fanvalue = request.form['fanstate']
        doorvalue = request.form['door']
        
        
        if fanvalue == "ON":
            fanOveride = '1'
            mqttDean.publish("topic/fanstate","ON")
        elif fanvalue == "OFF":
            fanOveride = '0'
            mqttDean.publish("topic/fanstate","OFF")
            
        
            
        
        if doorvalue == "close":
            mqttJared.publish("edge/doorState","close")
        elif doorvalue == "open":
            mqttJared.publish("edge/doorState","open")
            
        
            
        
        
    return home()
        
        
        
@app.route('/setColor', methods=['GET', 'POST'])
def setColor():
    r = request.values.get('rVal') 
    g = request.values.get('gVal')
    b = request.values.get('bVal')

    r = checkInt(r)
    g = checkInt(g)
    b = checkInt(b)

    if r is None:
        r = 0
    if g is None:
        g = 0
    if b is None:
        b = 0

    color = '{},{},{}'.format(r, g, b)

    #print('topic: {}\npubMsg: {}'.format('lighting/rgb', color))
    if r != 0 or g != 0 or b != 0:
        mqttAlex.publish('lighting/rgb', color, qos=0)

    return home()
    
@app.route('/toggleOn', methods=['GET'])
def turnOn():
    mqttAlex.publish('lighting/on', 'e', qos=0)
    #predictTemp()

    return home()

def checkInt(string):
    ret = None
    match = intRe.search('{}'.format(string))
    if match is not None:
        ret = int(match.group('num'))

    return ret

if __name__ == '__main__':
    
    ws2 = threading.Thread(target= lambda: app.run(debug=False, host='0.0.0.0', port=8080,use_reloader=False))
    ws2.start()
    
    
