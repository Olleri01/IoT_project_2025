from ultralytics import YOLO
from PIL import Image
from threading import Thread, Semaphore

class object_detection:
    def __init__(self, model_name):
        print("Creating object_detection instance")
        print("Model: {}".format(model_name))
    
        self.model = YOLO(model_name)
        self.queue = []
        self.objects = {}
        self.running = True
        self.queue_semaphore = Semaphore(0)

        new_thread = Thread(target=self.object_detection_loop)
        new_thread.start()

    def queue_object_detection(self, image, client, frame_number):
        #Images are queued for object detection
        self.queue.append((image, client, frame_number))
        self.queue_semaphore.release()

    def get_client_objects(self, client):
        if (not client in self.objects):
            return []

        client_objects = self.objects[client]
        if (client_objects == None):
            return []
            
        self.objects[client] = None

        return client_objects


    def run_object_detection_for_image(self, image, frame_number):
        #Run object detection
        #results = self.model(image, classes=[0], verbose=False) #classes=[0] for detecting people only
        
        #We are also counting cyclists. Bounding boxes can be filtered in pico
        results = self.model(image, verbose=False)
        
        objects_data = []
        
        for r in results:
            boxes = r.boxes

            xywh = boxes.xywhn.cpu().numpy()
            conf = boxes.conf.cpu().numpy()
            cls  = boxes.cls.cpu().numpy()

            for (x, y, w, h), c, cl in zip(xywh, conf, cls):
                objects_data.append({
                    "bbox": [float(x), float(y), float(w), float(h)],
                    "confidence": float(c),
                    "class_id": int(cl),
                    "class_name": self.model.names[int(cl)] if hasattr(self.model, "names") else "",
                    "frame_number" : frame_number
                })

        return objects_data

    def object_detection_loop(self):
        while True:
            self.queue_semaphore.acquire()
            if (self.running == False):
                return

            (image, client, frame_number) = self.queue[0]
            self.queue = self.queue[1:] #Remove image from queue

            objects = self.run_object_detection_for_image(image, frame_number)

            if (len(objects) == 0):
                continue

            if (not client in self.objects):
                self.objects[client] = objects
            elif (self.objects[client] == None):
                self.objects[client] = objects
            else:
                self.objects[client] += objects

    
