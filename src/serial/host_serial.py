import serial
import numpy as np
from PIL import Image


# Uncomment for rgb

# Adjust serial port to match os
# For example /dev/ttyACM0 for linux and COM3 for windows
ser = serial.Serial("/dev/ttyACM0", 115200)  

width = 320
height = 240

#Write 1 to buffer to signal that host is ready to recieve data
ser.write(b'\x01')

#Read data from buffer
data = ser.read(width*height*2)

buf = np.frombuffer(data, dtype=np.uint8)

high = buf[0::2]
low  = buf[1::2]

# Extract R,G,B components
r = ((high >> 3) & 0x1F) << 3   # 5 bits → 8 bits
g = (((high & 0x07) << 3) | ((low >> 5) & 0x07)) << 2  # 6 bits → 8 bits
b = (low & 0x1F) << 3            # 5 bits → 8 bits

# Stack into RGB image
rgb = np.dstack([r, g, b]).astype(np.uint8)
rgb = rgb.reshape((height, width, 3))

# Save using PIL
img = Image.fromarray(rgb, 'RGB')
img.save('image.png') 



""" 
#Uncomment the following for grayscale version

ser = serial.Serial("/dev/ttyACM0", 115200)  

width = 320
height = 240

#Write 1 to buffer to sigal that host is ready to recieve data
ser.write(b'\x01')

#Read data from buffer
data = ser.read(width*height)

with open("image.pgm", "wb") as f:
    f.write(f"P5\n{width} {height}\n255\n".encode())
    f.write(data)
"""