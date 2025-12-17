import board
import busio
import wifi
import socketpool
import struct
import time
import ssl
import os

import digitalio

import camera
import object_detection

def connect_wifi():
    #This function read wifi.txt file and parses wifi ssid and password
    #returns socketpool
    
    print("Loading wifi credentials")
    with open("/wifi.txt", "r") as f:
        wifi_credentials = f.read()
        wifi_ssid = wifi_credentials.split(' ')[0].strip()
        wifi_pwd  = wifi_credentials.split(' ')[1].strip()

    print(wifi_ssid)
    print(wifi_pwd)

    print("Connect Wifi")
    wifi.radio.connect(ssid=wifi_ssid, password=wifi_pwd)
    
    print("Creating socket pool")
    pool = socketpool.SocketPool(wifi.radio)
    
    return pool
    

def get_ssl_context():
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
            print("Registering objects!!")
            
            self.person_count += self.passing_person_count;
            self.cyclist_count += self.passing_cyclist_count;
            
            self.passing_person_count = 0;
            self.passing_cyclist_count = 0;
            
        

        self.frame_number += 1;
    
    
    
def main():
    sockpool = connect_wifi()
    ssl_context = get_ssl_context()

    (cam, framebuffer) = camera.init_camera(2, 0) #160x120 rgb888
    od_client = object_detection.object_detection_client(sockpool, ssl_context, "192.168.1.101", 6968, 6969)

    counter = pedestrian_counter()
    
    while True:
        counter.update(cam, framebuffer, od_client)
        
        print("Persons: {}  Cyclists: {}".format(counter.person_count, counter.cyclist_count))
        



    #frame_number = 0
    #capturing = False
    #capture_time = 2

    #while True:
        
    #    if pir.value and not capturing:
            
    #        start = time.time()
    #        capturing = True

            
    #    if capturing:
    #        if time.time() - start < capture_time:
    #            print("Motion detected, taking photo")
    #            cam.capture(buf)
    #            od_client.send_image(buf, cam.colorspace, cam.width, cam.height, frame_number)
    #            frame_number += 1
    #            time.sleep(0.2)
    #        else:
    #            capturing = False
        
    #    objects = od_client.get_objects()
    #    for o in objects:
    #        print(o)



if __name__ == "__main__":
    main()


