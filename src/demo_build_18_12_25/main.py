from lib import adafruit_minimqtt as MQTT
import board
import busio
import time
import wifi
import adafruit_connection_manager
import config
import adafruit_bmp280
import json
import ssl

import config

#import camera
#import object_detection
import socketpool

import DHT11_masiina
import CRT00549L_masiina
#import gc
#steamy globals

light_sensor = CRT00549L_masiina.CRT00549L()
hum_sensor = DHT11_masiina.DHT11()

#status = False
#collect_interval = 10.0 #data loggin interval in seconds

class Status:
    def __init__(self):
        self.status = False
        self.collect_interval = 10.0
    def getStatus(self):
        return self.status
    def setStatus(self, value):
        self.status = value
    def changeStatus(self):
        self.status = not self.status
        

device_status = Status()

def connect_wifi():
    #This function read wifi.txt file and parses wifi ssid and password
    #returns socketpool
    
    print("Loading wifi credentials")
    wifi_ssid = config.WIFI_SSID
    wifi_pwd  = config.WIFI_PWD

    print(wifi_ssid)
    print(wifi_pwd)

    print("Connect Wifi")
    wifi.radio.connect(ssid=wifi_ssid, password=wifi_pwd)
    
    print("Creating socket pool")
    pool = socketpool.SocketPool(wifi.radio)
    #pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
    
    return pool
    
"""
def get_ssl_context_for_object_detection():
    #This function reads public key cert.pem and creates ssl_context
    #Return ssl_context
    print("Creating ssl_context")
    ssl_context = ssl.create_default_context()

    print("Loading cert file")
    with open("/cert.pem", "r") as f:
        ca_cert = f.read()

    print("Loading cert chain")
    ssl_context.load_verify_locations(cadata=ca_cert)
    
    return ssl_context
"""
   
def collect_data(bmp280):
    data_message = {"datetime": time.time(),
        "currentHourWalkers": 0,
        "currentHourCyclists": 0,
        "location": "asdasddfg",
        "temperature":bmp280.temperature,
        "luminosity": light_sensor.read_luminance(),
        "humidity": hum_sensor.read_humidity(),
        "pressure": bmp280.pressure,
        }
    return json.dumps(data_message)
"""    
class pedestrian_counter:
    def __init__(self):
       self.confidence_treshold = 0.65
       self.passing_duration = 1.0
       
       self.person_count = 0;
       self.cyclist_count = 0;
       
       self.passing_person_count = 0;
       self.passing_cyclist_count = 0;
       self.passing_count_time = -1;
       
       self.frame_number = 0;
       
    def count_objects_per_frame(self, objects):
        frame_dict = {};
        for o in objects:
            framenum = o["frame_number"];
            if (framenum not in frame_dict):
                frame_dict[framenum] = [0, 0];
                
            if (o["class_name"] == "person" and o["confidence"] >= self.confidence_treshold):
                frame_dict[framenum][0] += 1
            elif (o["class_name"] == "bicycle" and o["confidence"] >= self.confidence_treshold):
                frame_dict[framenum][1] += 1
            
        counts = []
        for frame_count in frame_dict.values():
            counts.append(frame_count)
            
        return counts
        
    
    def update(self, cam, framebuffer, od_client):
        cam.capture(framebuffer)
        od_client.send_image(framebuffer, cam.colorspace, cam.width, cam.height, self.frame_number)
        
        objects = od_client.get_objects()
        counts_per_frame = self.count_objects_per_frame(objects)
        
        
        for counts in counts_per_frame:
            if (counts[0] > 0 or counts[1] > 0):
                self.passing_count_time = time.monotonic() + self.passing_duration
                
            self.passing_person_count = max(self.passing_person_count, counts[0])
            self.passing_cyclist_count = max(self.passing_cyclist_count, counts[1])
        
        
        if (time.monotonic() > self.passing_count_time):
            self.person_count += self.passing_person_count;
            self.cyclist_count += self.passing_cyclist_count;
            
            self.passing_person_count = 0;
            self.passing_cyclist_count = 0;
            
        self.frame_number += 1;
    """
    
    
def connected(client, userdata,flags,rc):
    print("mqtt connected")
    client.subscribe("skynet/intel_data")
    client.subscribe("skynet/mqtt_set_status")

def disconnected(client, userdata,flags):
    print("disconnected from mqtt broker")

def message(client, topic, message):
    print(f'New msg on topic {topic}:{message}')
    if topic=="skynet/mqtt_set_status":
        print(topic)
        print(device_status.getStatus())
        changeStatus()
        print(device_status.getStatus())
        ####################kesken, viimeistele tämä
def sendCurrentStatus():
    if device_status.getStatus():
        message = json.dumps({"status":1})
        mqtt_client.publish("skynet/mqtt_get_status", message)
    else:
        message = json.dumps({"status":0})
        mqtt_client.publish("skynet/mqtt_get_status", message)

def changeStatus():#changes sampling frequency between 1min and 1hour
    device_status.changeStatus() # if status is true,
    if device_status.getStatus():
        device_status.collect_interval = 30.0 #data loggin interval in seconds
    else:
        device_status.collect_interval = 10.0 #data loggin interval in seconds
    print(device_status.getStatus())
    sendCurrentStatus()
    
    
def mqttSetup(pool, ssl_contx):
    global mqtt_client
    mqtt_client = MQTT.MQTT(
        broker=config.MQTT_BROKER,
        username=config.MQTT_USER,
        password=config.MQTT_PWD,
        socket_pool=pool,
        is_ssl = True,
        ssl_context=ssl_contx,
        )
    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message
    mqtt_client.connect(host = config.MQTT_BROKER, port = config.MQTT_PORT)
"""  
def print_memory_consumption():
    free = gc.mem_free()
    used = gc.mem_alloc()
    total = free + used

    print("RAM usage: {} kB / {} kB {}%".format(round(used/1024), round(total/1024), used*100 / total))
"""

#Circuitpython can use only 1 SSL connection at time
#These callback are used to disconnect and reconnect mqtt when object_detection_client uses SSL for key-exchange
"""
def object_detection_client_ssl_begin():
    mqtt_client.disconnect()
    
def object_detection_client_ssl_end():
    mqtt_client.connect(host = config.MQTT_BROKER, port = config.MQTT_PORT)
"""
def main():
    sockpool = connect_wifi()
    #ssl_context_for_od = get_ssl_context_for_object_detection()
    ssl_context_for_mqtt = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
    
    mqttSetup(sockpool, ssl_context_for_mqtt);
    
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(busio.I2C(scl = board.GP3,sda = board.GP2), address=0x76)
    #(cam, framebuffer) = camera.init_camera(2, 0) #160x120 rgb888
    
    #od_client = object_detection.object_detection_client(sockpool, ssl_context_for_od, "80.220.42.45", 6968, 6969, object_detection_client_ssl_begin, object_detection_client_ssl_end)

    #counter = pedestrian_counter()
    
    #collect_interval = 10.0 #data loggin interval in seconds
    next_collect_time = time.monotonic() + device_status.collect_interval
    
#    prev_person_count = 0
#    prev_cyclist_count = 0
    print("Going to mainloop")
    while True:
#counter.update(cam, framebuffer, od_client)
        mqtt_client.loop()
#      print_memory_consumption()
  
        """
        if (prev_person_count != counter.person_count or prev_cyclist_count != counter.cyclist_count):
            prev_person_count = counter.person_count
            prev_cyclist_count = counter.cyclist_count
            print("Persons: {}  Cyclists: {}".format(counter.person_count, counter.cyclist_count))
        """   
        if (time.monotonic() > next_collect_time):
            next_collect_time = time.monotonic() + device_status.collect_interval
            
            print("Data collection")
            #Data is collected 1 min intervals
            message = collect_data(bmp280)
            print(message)
            mqtt_client.publish("skynet/intel_data", message)
            

if __name__ == "__main__":
    main()


