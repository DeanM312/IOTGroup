import serial
import paho.mqtt.client as mqtt
import json
import numpy as np
import matplotlib.pyplot as plt


ser = serial.Serial('/dev/ttyS0',9600)
ser.flushInput()
ser.flushOutput()

HOST = 'localhost'

#THINGSBOARD_HOST = '10.1.44.147'
THINGSBOARD_HOST = '192.168.43.194'
#THINGSBOARD_HOST = '192.168.0.45'
ACCESS_TOKEN = 'CrO5pBokbSw6D0I5cCqr'



thingsboard = mqtt.Client("p1")
thingsboard.username_pw_set(ACCESS_TOKEN)
thingsboard.connect(THINGSBOARD_HOST, 1883, 60)
thingsboard.loop_start()


def on_message(client, userdata, message):
    global data
    data = str(message.payload.decode("utf-8"))
    print(data)
    



webserver = mqtt.Client() 
webserver.on_message=on_message
webserver.connect(HOST) 
webserver.loop_start() 
webserver.subscribe("topic/fanstate")



sensor_data = {'Temperature': 0}
data = 0


while True:
    
    try:
        temp = float(ser.readline().decode('utf-8'))
        webserver.publish('topic/temperature', temp)
        sensor_data['Temperature'] = temp
        

        command = data
        
        if (command == 'ON'):
            ser.write(b"1")
        else:
            ser.write(b"0")

        print(sensor_data)
        thingsboard.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
    
        
 
    except:
        pass
    
