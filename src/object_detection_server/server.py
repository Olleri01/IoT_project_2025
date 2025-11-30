from PIL import Image
import socket
import time

from threading import Thread
import struct
import io
import time
import json

import numpy as np

def rgb565_to_pil(framebuffer: bytes, width=160, height=120) -> Image.Image:
    arr = np.frombuffer(framebuffer, dtype='>u2').reshape((height, width))
    
    r = (arr >> 11) & 0x1F       # 5 bits
    g = (arr >> 5)  & 0x3F       # 6 bits
    b =  arr        & 0x1F       # 5 bits

    r = (r * 255 / 31).astype(np.uint8)
    g = (g * 255 / 63).astype(np.uint8)
    b = (b * 255 / 31).astype(np.uint8)

    rgb = np.dstack((r, g, b))
    
    return Image.fromarray(rgb, mode='RGB')


def yuv422_to_pil(framebuffer: bytes, width=160, height=120) -> Image.Image:
    
    Y  = np.frombuffer(framebuffer[0::4], dtype=np.uint8).reshape((height, int(width/2))).astype(float)
    V  = np.frombuffer(framebuffer[1::4], dtype=np.uint8).reshape((height, int(width/2))).astype(float)
    Y1 = np.frombuffer(framebuffer[2::4], dtype=np.uint8).reshape((height, int(width/2))).astype(float)
    U  = np.frombuffer(framebuffer[3::4], dtype=np.uint8).reshape((height, int(width/2))).astype(float)
    
    R0 = Y + 1.4075 * (V - 128)
    G0 = Y - 0.3455 * (U - 128) - (0.7169 * (V - 128))
    B0 = Y + 1.7790 * (U - 128)
    
    R1 = Y1 + 1.4075 * (V - 128)
    G1 = Y1 - 0.3455 * (U - 128) - (0.7169 * (V - 128))
    B1 = Y1 + 1.7790 * (U - 128)

    p0 = np.dstack((R0, G0, B0))
    p1 = np.dstack((R1, G1, B1))

    rgb = np.empty((height, width, 3), dtype=np.uint8)

    rgb[:, 0::2, :] = np.clip(p0, 0, 255).astype(np.uint8)
    rgb[:, 1::2, :] = np.clip(p1, 0, 255).astype(np.uint8)

    return Image.fromarray(rgb, mode='RGB');


class server:

    def receive_bytes(self, sock, num_of_bytes):

        #print("Receiving {} bytes".format(num_of_bytes))

        data_left = num_of_bytes
        data = bytearray()
        while (data_left > 0):
            bytes = sock.recv(data_left)
            data += bytes
            data_left -= len(bytes)
            
        return data
    
    def receive_string(self, sock):
        data = bytearray()
        while self.running:
            bytes = sock.recv(1)
            if (len(bytes) == 0):
                continue

            if (bytes[0] == 0):
                break
            data += bytes
            
        return data.decode("utf-8")
    
    def send_string(self, sock, str):
        data = str.encode('utf-8') + b'\0'
        sock.sendall(data)

    def send_objects(self, sock, objects):
        sock.sendall(struct.pack("<I", len(objects))) #send number of objects

        for o in objects:
            bbox_json_str = json.dumps(o)
            print("sending {}\n".format(bbox_json_str));
            self.send_string(sock, bbox_json_str)


    def receive_image(self, sock):
        image_data_length, = struct.unpack("<I", self.receive_bytes(sock, struct.calcsize("<I")))
        image_data = self.receive_bytes(sock, image_data_length)

        return yuv422_to_pil(image_data);
        
    def close(self):
        self.running = False
        self.thread.join()

    def handle_connection(self, addr, sock):
        self.active_connections += 1

        client = addr[0]
        if (client not in self.clients):
            print("New client {}".format(client))
            self.clients.append(client)

        sock.setblocking(True)
    
        try:
            while True:
                request = self.receive_string(sock)
                if (request == "send_image"):
                    frame_number, = struct.unpack("<I", self.receive_bytes(sock, struct.calcsize("<I")))

                    image = self.receive_image(sock)
                    if (image != None):
                        self.detector.queue_object_detection(image, client, frame_number)
                        self.last_received_image[client] = image

                elif (request == "get_objects"):
                    objects = self.detector.get_client_objects(client)
                    self.send_objects(sock, objects)

                    self.last_sent_bboxes[client] = objects
                else:
                    print("unknown request")
        except Exception as e:
            print(e)

        sock.close()

        self.active_connections -= 1

    def server_loop(self, ip, port):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind((ip, port))
        tcp_socket.setblocking(False)
        tcp_socket.listen(0)

        while self.running:
            try:
                client_socket, addr = tcp_socket.accept()

                print("Accepting connection {}".format(addr))

                new_thread = Thread(target=self.handle_connection, args=(addr, client_socket))
                new_thread.start()
            except BlockingIOError:
                pass

        tcp_socket.close()
            
    def __init__(self, ip, port, od):
        self.detector = od
        self.running = True
        self.active_connections = 0
        self.last_received_image = {}
        self.last_sent_bboxes = {}
        self.clients = []

        self.last_received_image_time = time.perf_counter()

        self.thread = Thread(target = self.server_loop, args = (ip, port))
        self.thread.start()

    def get_clients(self):
        return self.clients

    def get_last_received_image(self, client):
        if (client in self.last_received_image):
            return self.last_received_image[client]
        else:
            return None
    
    def get_last_sent_bboxes(self, client):
        if (client in self.last_sent_bboxes):
            return self.last_sent_bboxes[client]
        else:
            return None
