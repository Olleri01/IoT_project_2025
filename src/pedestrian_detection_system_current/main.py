from lib import adafruit_minimqtt as MQTT
import board
import busio
import adafruit_bmp280
import time
import wifi
import adafruit_connection_manager
import config
import json
import ssl

import analogio

import camera
import object_detection

import socketpool

#import adafruit_dht

collect_interval = 10.0
status = False

def connect_wifi():
    #This function read wifi.txt file and parses wifi ssid and password
    #returns socketpool
    wifi_ssid = config.WIFI_SSID
    wifi_pwd  = config.WIFI_PWD
    wifi.radio.connect(ssid=wifi_ssid, password=wifi_pwd)
    pool = socketpool.SocketPool(wifi.radio)
    #pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
    
    return pool

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
lumsensor = analogio.AnalogIn(board.GP26)
#humsensor = adafruit_dht.DHT11(board.GP27)
   
def collect_data(bmp280, counter):
    cum_luminance = 0.0
    i =0
    while(i<3):
        cum_luminance = cum_luminance + lumsensor.value*3.3 /65535
        i = i+1
    cum_luminance= cum_luminance/3.0 #return average value of the luminance
    
    data_message = {"datetime": time.time(),
        "currentHourWalkers": counter.person_count,
        "currentHourCyclists": counter.cyclist_count,
        "location": "paskareika",
        "temperature":bmp280.temperature,
        "luminosity": cum_luminance,
        "humidity": 0.0,#humsensor.humidity,
        "pressure": bmp280.pressure,
        }
    
    counter.person_count = 0
    counter.cyclist_count = 0
    
    return json.dumps(data_message)
    
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
       # gc.collect() #Try to avoid heap fragmentation
        
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
    
    
    
def connected(client, userdata,flags,rc):
    print("mqtt connected")
    client.subscribe("skynet/mqtt_set_status")

def disconnected(client, userdata,flags):
    print("disconnected from mqtt broker")

def message(client, topic, message):
    if topic=="skynet/mqtt_set_status":
        changeStatus()

def sendCurrentStatus():
    global status
    if status:
        message = json.dumps({"status":1})
        mqtt_client.publish("skynet/mqtt_get_status", message)
    else:
        message = json.dumps({"status":0})
        mqtt_client.publish("skynet/mqtt_get_status", message)

def changeStatus():#changes sampling frequency between 10s and 30s
    global collect_interval
    global status
    status =not status # if status is true,
    if status:
        collect_interval = 30.0 #data loggin interval in seconds
    else:
        collect_interval = 10.0 #data loggin interval in seconds
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
   
#Circuitpython can use only 1 SSL connection at time
#These callback are used to disconnect and reconnect mqtt when object_detection_client uses SSL for key-exchange
def object_detection_client_ssl_begin():
    mqtt_client.disconnect()

def object_detection_client_ssl_end():
    mqtt_client.connect(host = config.MQTT_BROKER, port = config.MQTT_PORT)


def main():
    sockpool = connect_wifi()
    ssl_context_for_od = get_ssl_context_for_object_detection()
    ssl_context_for_mqtt = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
    
    mqttSetup(sockpool, ssl_context_for_mqtt);
    
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(busio.I2C(scl = board.GP3,sda = board.GP2), address=0x76)
    (cam, framebuffer) = camera.init_camera(2, 0) #160x120 rgb888
    
    od_client = object_detection.object_detection_client(sockpool, ssl_context_for_od, "80.220.42.45", 6968, 6969, object_detection_client_ssl_begin, object_detection_client_ssl_end)
    global collect_interval
    counter = pedestrian_counter()
    
    collect_interval = 10.0 #data loggin interval in seconds
    next_collect_time = time.monotonic() + collect_interval
    
    prev_person_count = 0
    prev_cyclist_count = 0
    print("Going to mainloop")
    while True:
        counter.update(cam, framebuffer, od_client)
        
        print("elossa")
        if (prev_person_count != counter.person_count or prev_cyclist_count != counter.cyclist_count):
            prev_person_count = counter.person_count
            prev_cyclist_count = counter.cyclist_count
            print("Persons: {}  Cyclists: {}".format(counter.person_count, counter.cyclist_count))
        
        if (time.monotonic() > next_collect_time):
            next_collect_time = time.monotonic() + collect_interval 
            
            print("Data collection")
            #Data is collected 1 min intervals
            mqtt_client.loop(timeout=2)
            message = collect_data(bmp280, counter)
            mqtt_client.publish("skynet/intel_data", message)
            

if __name__ == "__main__":
    main()


