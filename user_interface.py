from flask import Flask, render_template, request, url_for, flash, redirect
import paho.mqtt.client as mqtt
import re
import pymysql, time
from DBComs import DBComs
from PolyRegression import PolyRegression
import threading

intRe = re.compile('(?P<num>^\d+$)')
msgRe = re.compile('{"state":"(?P<state>[a-zA-Z_]+)","pirOutput":"(?P<pirOutput>[a-zA-Z_]+)","color":"(?P<color>[0-9,]+)"}')

app = Flask(__name__)

ml = PolyRegression()

deanHost = 'localhost'
alexHost = '192.168.43.118'
jaredHost = '192.168.43.5'

fanOveride = '0'

temp = 0
doorstate = 0

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

def on_message_temperature(client, userdata, message):
    global fanOveride
    global temp
    
    
    temp = float(message.payload.decode("utf-8"))

    print(temp)
    
    #mqttDean.publish("topic/fanstate","0")
    if ((doorstate == 'OPEN' and temp > 21) or temp > 25) and fanOveride == '0':
        mqttDean.publish("topic/fanstate","ON")
    elif fanOveride == '1':
        mqttDean.publish("topic/fanstate","ON")
    else:
        mqttDean.publish("topic/fanstate","OFF")
    
    temp = str(message.payload.decode("utf-8"))
    
    colData = [time.time(), data]
    cols = ['_time', 'temperature']
    command = 'INSERT INTO templog (_time, temperature) VALUES ({}, {})'.format(colData[0], colData[1])
    c = db.cursor()
    c.execute(command)
    db.commit()
    
def on_message_distance(client, userdata, message):
    # Door automation goes here
    pass
    
    
    
def on_message_pir(client, userdata, message):
    # Light automation goes here
    pass

# Dean's Node
mqttDean = mqtt.Client() 
mqttDean.on_message= on_message_temperature
mqttDean.connect(deanHost)
mqttDean.subscribe('topic/temperature', 0)
mqttDean.loop_start() 


# Alex's Node
#mqttAlex = mqtt.Client()
#mqttAlex.connect(alexHost)
#mqttAlex.loop_start()

# Jared's Node
#mqttJared = mqtt.Client()
#mqttJared.connect(jaredHost)
#mqttJared.loop_start()

def predictTemp():
    cursor = db.cursor()
    command = 'SELECT * FROM templog ORDER BY id DESC LIMIT 100'
    cursor.execute(command)
    rows = cursor.fetchall()

    #print(rows)
    x = []
    y = []
    for row in rows:
        x.append(row['_time'])
        y.append(row['temperature'])

    print(x)
    print(y)

    model = ml.predict(x, y, 'fig')

@app.route('/')
def index():
    return render_template('index.html')
    
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
            
        
            
        """
        if doorvalue == "ON":
            mqttJared.publish("topic/doorState","close")
        else:
            mqttJared.publish("topic/doorState","open")
        """
            
        
            
        
        
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
    #mqttAlex.publish('lighting/on', 'e', qos=0)
    predictTemp()

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
    
    
