import serial
import paho.mqtt.client as mqtt
import json
import numpy as np
import matplotlib.pyplot as plt

#ser = serial.Serial('COM3',9600)
ser = serial.Serial('/dev/ttyS0',9600)
ser.flushInput()
ser.flushOutput()

HOST = 'localhost'
#THINGSBOARD_HOST = '192.168.43.194'
THINGSBOARD_HOST = HOST

ACCESS_TOKEN = 'CrO5pBokbSw6D0I5cCqr'



thingsboard = mqtt.Client("p1")

# Set access token
thingsboard.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
thingsboard.connect(THINGSBOARD_HOST, 1883, 60)

thingsboard.loop_start()


def on_message(client, userdata, message):
    
    global data
    data = str(message.payload.decode("utf-8"))
    



webserver = mqtt.Client("p2") 
webserver.on_message=on_message
webserver.connect(HOST) 
webserver.loop_start() 
webserver.subscribe("topic/fanstate")
webserver.publish("topic/fanstate","0")

manualOveride = '0'
doorstate = 0

sensor_data = {'Temperature': 0}




while True:
    
    try:
        temp = float(ser.readline().decode('utf-8'))
        webserver.publish('topic/fanstate', temp)
        sensor_data['Temperature'] = temp
    

        manualOveride = data
        print(temp)
        #print(manualOveride)

        if ((doorstate == '1' and temp > 23) or temp > 24) and manualOveride == '0':
            ser.write(b"1")
        elif manualOveride == '1':
            ser.write(b"1")
        else:
            ser.write(b"0")
        




            
        #print(temp)        

        thingsboard.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

        
 
    except:
        pass
    
