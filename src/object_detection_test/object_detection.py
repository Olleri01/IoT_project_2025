import struct
import time
import json
import aesio
#import os

import gc

class object_detection_client:
    def __init__(self, sock_pool, ssl_context, host_ip, host_port0, host_port1, begin_ssl_callback, end_ssl_callback):
        self.host_ip = host_ip
        self.host_port0 = host_port0
        self.host_port1 = host_port1
        self.pool = sock_pool
        self.ssl_context = ssl_context
        self.sock = None
        
        self.begin_ssl_callback = begin_ssl_callback;
        self.end_ssl_callback = end_ssl_callback;
        
        self.encrypt_buff = bytearray(128)
        
    def send_data(self, sock, aes, data):
        if (aes == None):
            sock.sendall(data)
        else:
            #Force garbage collector to run before sending image
            gc.collect()
            
            dataleft = len(data)
            src_mv = memoryview(data)
            dst_mv = memoryview(self.encrypt_buff)
            
            index = 0
            while (dataleft > 0):
                packet_size = min(dataleft, 128)
                aes.encrypt_into(src_mv[index:index+packet_size], dst_mv[0:packet_size])
                sock.sendall(dst_mv[0:packet_size])
                index += packet_size
                dataleft -= packet_size
            
        
    def receive_data(self, sock, aes, num_of_bytes):
        if (aes == None):
            data = bytearray(num_of_bytes)
            sock.recv_into(data, num_of_bytes)
            return data
        else:
            dataleft = num_of_bytes
            
            data = bytearray(num_of_bytes)
            
            src_mv = memoryview(self.encrypt_buff)
            dst_mv = memoryview(data)
            
            index = 0
            while (dataleft > 0):
                packet_size = min(dataleft, 128)
                
                sock.recv_into(src_mv[0:packet_size], packet_size)
                aes.decrypt_into(src_mv[0:packet_size], dst_mv[index:index+packet_size])
 
                index += packet_size
                dataleft -= packet_size
            
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
        
        print("Received token")
            
        return (token, key)
        
        
    def connect(self):
        sock = None
        
        if (self.ssl_context != None):
            self.begin_ssl_callback();
        
        try:
            if (self.ssl_context == None):
                self.aes = None
 
                sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
                sock.connect((self.host_ip, self.host_port1))
                sock.sendall(b'unsafeplaintext')
                
                sock.settimeout(5)
            else:
                (token, key) = self.receive_session_keys()

                self.aes = aesio.AES(key, aesio.MODE_CTR)
                
                sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_STREAM)
                sock.connect((self.host_ip, self.host_port1))
                sock.sendall(token)
                
                sock.settimeout(5)
        except Exception as e:
            print(e)
            sock = None
            pass
            
        if (self.ssl_context != None):
            self.end_ssl_callback();
            
        if (sock != None):
            print("Connected to OD server")
            
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
                                                            len(framebuffer),
                                                            colorspace,
                                                            width,
                                                            height))
            self.send_data(self.sock, self.aes, framebuffer)
        except Exception as e:
            print(e)
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
        
