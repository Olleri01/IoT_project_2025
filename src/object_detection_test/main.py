import board
import busio
import wifi
import socketpool
import struct
import time
import json
import ssl
import aesio
import os

from adafruit_ov7670 import OV7670, OV7670_SIZE_DIV16

i2c = busio.I2C(scl=board.GP9, sda=board.GP8)
cam = OV7670(
    i2c,
    data_pins=[
        board.GP12, board.GP13, board.GP14, board.GP15,
        board.GP16, board.GP17, board.GP18, board.GP19
    ],
    clock=board.GP11,
    vsync=board.GP7,
    href=board.GP21,
    mclk=board.GP20,
    shutdown=None,
    reset=board.GP10,
)
              
class object_detection_client:
    def __init__(self, sock_pool, ssl_context, host_ip, host_port0, host_port1):
        self.host_ip = host_ip
        self.host_port0 = host_port0
        self.host_port1 = host_port1
        self.pool = sock_pool
        self.ssl_context = ssl_context
        self.sock = None
        
        
    def send_data(self, sock, aes, data):
        if (aes == None):
            sock.sendall(data)
        else:
            buffer = bytearray(len(data))
            aes.encrypt_into(data, buffer)
            sock.sendall(buffer)
        
    def receive_data(self, sock, aes, num_of_bytes):
        if (aes == None):
            data = bytearray(num_of_bytes)
            sock.recv_into(data, num_of_bytes)
            return data
        else:
            buffer = bytearray(num_of_bytes)
            data = bytearray(num_of_bytes)
            
            sock.recv_into(buffer, num_of_bytes)
            aes.decrypt_into(buffer, data)
            
            return data
        
    def receive_string(self, sock, aes):
        string_len, = struct.unpack("<I", self.receive_data(sock, aes, struct.calcsize("<I")))
        return self.receive_data(sock, aes, string_len).decode("utf-8")
    
    def send_string(self, sock, aes, str):
        self.send_data(sock, aes, struct.pack("<I", len(str)))
        self.send_data(sock, aes, str.encode('utf-8'))
        
    
    def receive_session_keys(self):
        ssl_socket = self.ssl_context.wrap_socket(self.pool.socket(), server_hostname="coursework")
        ssl_socket.connect((self.host_ip, self.host_port0))
        
        token = bytearray(16)
        key = bytearray(16)
        
        ssl_socket.recv_into(token, 16)
        ssl_socket.recv_into(key, 16)
        ssl_socket.close()
        
        return (token, key)
        
        
    def connect(self):
        sock = None
                
        try:
            if (self.ssl_context == None):
                self.aes = None
                
                sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
                sock.connect((self.host_ip, self.host_port1))
                sock.sendall(b'unsafeplaintext')
            else:
                (token, key) = self.receive_session_keys()

                self.aes = aesio.AES(key, aesio.MODE_CTR)
                
                sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
                sock.connect((self.host_ip, self.host_port1))
                sock.sendall(token)
        except Exception as e:
            pass
            
        return sock 
        
    def send_image(self, framebuffer, colorspace, width, height, frame_number):
        if (self.sock == None):
            self.sock = self.connect()
            if (self.sock == None):
                return
        
        try:
            self.send_string(self.sock, self.aes, "send_image")
            self.send_data(self.sock, self.aes, struct.pack("<IIIII",
                                                            frame_number,
                                                            len(buf),
                                                            colorspace,
                                                            width,
                                                            height))
            self.send_data(self.sock, self.aes, framebuffer)
        except Exception as e:
            self.sock.close()
            self.sock = None
        
        
    def get_objects(self):
        if (self.sock == None):
            self.sock = self.connect()
            if (self.sock == None):
                return []
            
        objects = []
        try:
            self.send_string(self.sock, self.aes, "get_objects")
            
            num_of_bboxes, = struct.unpack("<I", self.receive_data(self.sock, self.aes, 4))
            for i in range(num_of_bboxes):
                bbox_json = self.receive_string(self.sock, self.aes)
                objects.append(json.loads(bbox_json))
            
            
        except Exception as e:
            print(e)
            self.sock.close()
            self.sock = None
        
        return objects
        


cam.size = 2
cam.colorspace = 0

print("{}x{}".format(cam.width, cam.height))

print("allocating framebuffer")
buf = bytearray(2 * cam.width * cam.height)

print("Loading wifi credentials")
with open("/wifi.txt", "r") as f:
    wifi_credentials = f.read()
    wifi_ssid = wifi_credentials.split(' ')[0].strip()
    wifi_pwd  = wifi_credentials.split(' ')[1].strip()

print(wifi_ssid)
print(wifi_pwd)

print("Connect Wifi")
wifi.radio.connect(ssid=wifi_ssid, password=wifi_pwd)

    
print("Creating ssl_context")
ssl_context = ssl.create_default_context()

print("Loading cert file")
with open("/cert.pem", "r") as f:
    ca_cert = f.read()

print("Loading cert chain")
ssl_context.load_verify_locations(cadata=ca_cert)

print("Creating socket pool")
pool = socketpool.SocketPool(wifi.radio)

print("Connecting")
od_client = object_detection_client(pool, ssl_context, "192.168.1.101", 6968, 6969)

frame_number = 0

while True:
    cam.capture(buf)
    od_client.send_image(buf, cam.colorspace, cam.width, cam.height, frame_number)
    objects = od_client.get_objects()

    for o in objects:
        print(o)

    frame_number += 1


