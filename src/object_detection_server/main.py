from PIL import Image
from PIL import ImageDraw

import pygame
import time
import server

from ultralytics import YOLO

import object_detection


def draw_objects(image, objects, width, height):
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    for o in objects:
        if (o["confidence"] < 0.65):
            continue;
    
        box = o["bbox"]
        label = "{}: {}".format(o["class_name"], o["confidence"])
        
        x0 = (box[0] - box[2]/2)*width
        x1 = (box[0] + box[2]/2)*width
    
        y0 = (box[1] - box[3]/2)*height
        y1 = (box[1] + box[3]/2)*height
    
        draw.rectangle([(x0, y0), (x1, y1)], outline="red", width=4)
        draw.text((x0, y0 - 10), label, fill="red")
        
    return image

    
def main_loop():
    od = object_detection.object_detection("yolo11m.pt")

    serv = server.server("0.0.0.0", 6969, od)

    width, height = 640, 480
    screen = pygame.display.set_mode((width, height))

    running = True
    while running:

        if (len(serv.get_clients()) > 0):
            image = serv.get_last_received_image(serv.get_clients()[0])

            if (image != None):
                image = image.resize((width, height))
                
                objects = serv.get_last_sent_bboxes(serv.get_clients()[0])

                if (objects != None):
                    image = draw_objects(image, objects, width, height)
                
                width, height = image.size
                surf = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
                screen.blit(surf, (0, 0))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        time.sleep(0.0166)
    
    serv.close()
    pygame.quit()

if __name__ == "__main__":
    main_loop()
