from PIL import Image
import socket
import ssl

from threading import Thread
import struct
import io
import json
import time
import numpy as np

from Crypto.Cipher import AES
import os
import base64

def rgb565_to_pil(framebuffer: bytes, width=160, height=120) -> Image.Image:
    arr = np.frombuffer(framebuffer, dtype='>u2').reshape((height, width))
    
    r = (arr >> 11) & 0x1F       # 5 bits
    g = (arr >> 5)  & 0x3F       # 6 bits
    b =  arr        & 0x1F       # 5 bits

    r = np.clip(r * 255 / 31, 0, 255).astype(np.uint8)
    g = np.clip(g * 255 / 63, 0, 255).astype(np.uint8)
    b = np.clip(b * 255 / 31, 0, 255).astype(np.uint8)

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

class ctr_stream_state:
    #CTR mode in circuitpython's aesio library doesn't work like streamcipher with arbitary sized inputs
    #It's encrypt_into and decrypt_into functions uses begin of the block and increments always counter
    #This class is used to emulate same behaviour in serverside
    def __init__(self, key):
        #Counter starts from 0, should be safe because key is unique for each connection
        self.key = key
        self.counter = 0

    def increment(self, datalen):
        #Increment counter as aesio library does
        self.counter += int(datalen/16)
        if (datalen % 16 != 0):
            self.counter += 1

    def get_aes(self):
        #AES instance is created for each encrypt/decrypt call
        #IV is counter increased after each packet
        return AES.new(self.key, AES.MODE_CTR, initial_value=self.counter, nonce=b"")

def filter_objects(objects):
    confidence_treshold = 0.55
    class_names = ["person", "bicycle"]
    
    filtered_objects = []
    for o in objects:
        if (o["confidence"] > confidence_treshold and o["class_name"] in class_names):
            filtered_objects.append(o)
            
    return filtered_objects


class server:

    def send_bytes(self, sock, streamstate, data):
        if (streamstate == None):
            #Plaintext is used
            sock.sendall(data)
        else:
            #Data is encrypted with AES128 (CTR mode)
            aes = streamstate.get_aes()
            streamstate.increment(len(data))

            encrypted_data = aes.encrypt(data)
            sock.sendall(encrypted_data)

    def receive_bytes(self, sock, streamstate, num_of_bytes):
        data_left = num_of_bytes
        data = bytearray()
        
        timeout_time = time.time() + 5
        while (data_left > 0):
            if (time.time() > timeout_time):
                raise Exception("receive_bytes timeout")
            
            bytes = sock.recv(data_left)
            data += bytes
            data_left -= len(bytes)

        if (streamstate == None):
            return data
        else:
            aes = streamstate.get_aes()
            streamstate.increment(num_of_bytes)

            return aes.decrypt(data)
    
    def receive_string(self, sock, streamstate):
        #Receive header (string length)
        string_len, = struct.unpack("<I", self.receive_bytes(sock, streamstate, struct.calcsize("<I")))
        return self.receive_bytes(sock, streamstate, string_len).decode("utf-8")
    
    def send_string(self, sock, streamstate, str):
        #Strings are sent with header which is length of the string
        self.send_bytes(sock, streamstate, struct.pack("<I", len(str)))
        self.send_bytes(sock, streamstate, str.encode('utf-8'))

    def close(self):
        self.running = False
        self.thread.join()

    def handle_connection(self, addr, sock):
        sock.setblocking(True)
        sock.settimeout(5)
        
        #Receive one use token
        token = sock.recv(16)

        streamstate = None
        #Generate random id for client, this is used to prevent another client getting results from another
        client = base64.b64encode(os.urandom(16))

        if (token == b'unsafeplaintext'):
            print("New client {}:{},  plaintext!!!  id {}".format(addr[0], addr[1], client))
        else:
            if ((not token in self.session_keys) or self.session_keys[token] == None):
                sock.close() #Connection is rejected if no valid token
                return
            
            #Token is invalitaded immediately so that same key/token pair cannot be reused
            key = self.session_keys[token]
            self.session_keys[token] = None
            streamstate = ctr_stream_state(key)
            print("New client {}:{}, token {}   key {}   id {}".format(addr[0], addr[1], base64.b64encode(token), base64.b64encode(key), client))

        self.active_connections += 1
        self.clients.append(client)
            
        try:
            while True:
                request = self.receive_string(sock, streamstate)
                if (request == "send_image"):
                    #Receive image header
                    frame_number, image_data_length, colorspace, width, height = struct.unpack("<IIIII", self.receive_bytes(sock, streamstate, struct.calcsize("<IIIII")))
                    
                    #Lets check length before allocating buffers in case of header corruption
                    #AES in CTR mode without HMAC doesn't prevent attacker from flipping bits
                    if (image_data_length >= 1024*1024):
                        raise Exception("too big image")
                    
                    #Receive image data
                    image_data = self.receive_bytes(sock, streamstate, image_data_length)
                    image = None
                    
                    #OV7670 uses either RGB565 or YUV422
                    #Image is converted to RGB888
                    if (colorspace == 0):
                        image = rgb565_to_pil(image_data, width, height)
                    elif (colorspace == 1):
                        image = yuv422_to_pil(image_data, width, height)

                    if (image != None):
                        #Image is queued for object detection. Frame number attached for each bbox
                        self.detector.queue_object_detection(image, client, frame_number)
                        self.last_received_image[client] = image

                elif (request == "get_objects"):
                    objects = self.detector.get_client_objects(client)
                    
                    objects = filter_objects(objects)
                    
                    #Header is only number of objects
                    self.send_bytes(sock, streamstate, struct.pack("<I", len(objects)))

                    for o in objects:
                        #Object are sent as json
                        bbox_json_str = json.dumps(o)
                        self.send_string(sock, streamstate, bbox_json_str)


                    self.last_sent_bboxes[client] = objects
                else:
                    print("unknown request")
        except Exception as e:
            print(e)
        
        print("Closing connection {}".format(client))
        sock.close()
        
        self.clients.remove(client)

        self.active_connections -= 1

    def server_loop(self, ip, port):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind((ip, port))
        tcp_socket.setblocking(False)
        tcp_socket.listen(5)

        while self.running:
            try:
                client_socket, addr = tcp_socket.accept()

                print("Accepting connection {}".format(addr))
                
                #New thread is created for each client
                new_thread = Thread(target=self.handle_connection, args=(addr, client_socket))
                new_thread.start()
            except BlockingIOError:
                pass

        tcp_socket.close()


    def session_server_loop(self, ip, port):
        #Server uses ssl to send token + key pair for client
        #After client has received token + key via secure channel
        #it opens TCP connection, send token in plaintext
        #Then AES128 CTR is used to encrypt/decrypt data
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='cert.pem', keyfile='cert.key')

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip, port))
        server.setblocking(False)
        server.listen(5)
        
        
        while self.running:
            try:
                client, addr = server.accept()  # plain TCP accept
            except BlockingIOError:
                time.sleep(0.01)
                continue
            except OSError:
                break

            try:
                tls = context.wrap_socket(client, server_side=True)
                print(f"New session {addr}")
                
                #Unique key-token pair is created
                token = os.urandom(16)
                key = os.urandom(16)

                self.session_keys[token] = key
                tls.sendall(token)
                tls.sendall(key)
                
            except (ssl.SSLError, ConnectionResetError, BrokenPipeError) as e:
                print(f"TLS failed from {addr}: {e!r}")

            finally:
                try:
                    tls.close()
                except Exception:
                    pass
                try:
                    client.close()
                except Exception:
                    pass
  
        
        
        
        
        tcp_socket.close()
            
    def __init__(self, ip, port0, port1, od):
        self.detector = od
        self.running = True
        self.active_connections = 0
        self.last_received_image = {}
        self.last_sent_bboxes = {}
        self.session_keys = {}
        self.clients = []

        self.thread0 = Thread(target = self.session_server_loop, args = (ip, port0))
        self.thread1 = Thread(target = self.server_loop, args = (ip, port1))
        self.thread0.start()
        self.thread1.start()

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
