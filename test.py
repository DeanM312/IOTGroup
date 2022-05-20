import paho.mqtt.client as mqtt
HOST = 'localhost'

def on_message(client, userdata, message):
    
    global data
    data = str(message.payload.decode("utf-8"))
    print(data)




webserver = mqtt.Client("P1") 
webserver.on_message=on_message
webserver.connect(HOST) 
webserver.loop_start() 
webserver.subscribe("topic/fanstate")
webserver.publish("topic/fanstate","1")