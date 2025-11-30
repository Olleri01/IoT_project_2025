import board
import busio
import wifi
import socketpool
import struct
import time
import json

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
    def __init__(self, sock_pool, hostname):
        self.hostname = hostname
        self.pool = sock_pool
        self.sock = self.connect_tcp(self.pool, self.hostname)
        
    def receive_bytes(self, sock, num_of_bytes):
        data = bytearray(num_of_bytes)
        sock.recv_into(data, num_of_bytes)
        return data
        
    def receive_string(self, sock):
        data = bytearray()
        while True:
            bytes = bytearray(1)
            sock.recv_into(bytes, 1)
            if (bytes[0] == 0):
                break
            data += bytes
        
        return data.decode("utf-8")
    
    def connect_tcp(self, pool, host):
        sock = None
        try:
            sock = pool.socket(self.pool.AF_INET, pool.SOCK_STREAM)
            sock.connect(host)
        except Exception as e:
            pass
            
        return sock 
        
    def send_image(self, buf, frame_number):
        if (self.sock == None):
            self.sock = self.connect_tcp(pool, self.hostname)
            
        try:
            self.sock.sendall("send_image\0".encode())
            self.sock.sendall(struct.pack("<I", frame_number))
            self.sock.sendall(struct.pack("<I", len(buf)))
            
            self.sock.sendall(buf)
        except Exception as e:
            self.sock.close()
            self.sock = None
        
        
    def get_objects(self):
        if (self.sock == None):
            self.sock = self.connect_tcp(pool, self.hostname)
            
        objects = []
        try:
            self.sock.sendall("get_objects\0".encode()) 
            num_of_bboxes, = struct.unpack("<I", self.receive_bytes(self.sock, 4))
            for i in range(num_of_bboxes):
                bbox_json = self.receive_string(self.sock)
                
                objects.append(json.loads(bbox_json))
                print(objects[-1])
            
            
        except Exception as e:
            print(e)
            self.sock.close()
            self.sock = None
        
        return objects
        


cam.size = 2
cam.colorspace = 1;

print("{}x{}".format(cam.width, cam.height))

print("allocating framebuffer")
buf = bytearray(2 * cam.width * cam.height)


print("Connect Wifi")
wifi.radio.connect(ssid="wifiname", password="password")

pool = socketpool.SocketPool(wifi.radio)

print("Connecting")
od_client = object_detection_client(pool, ("192.168.1.101", 6969))
print("Connected")

frame_number = 0

while True:
    cam.capture(buf)
    od_client.send_image(buf, frame_number)
    od_client.get_objects()
    
    frame_number += 1


