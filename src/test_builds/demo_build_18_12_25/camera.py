import board
import busio

from adafruit_ov7670 import OV7670, OV7670_SIZE_DIV16

def init_camera(resolution, colorspace):
    #This function creates camera interface for ov7670 and allocates framebuffer
    #colorspace 0 is rgb888
    #colorspace 1 is yuv422
    #both colorspaces are supported in objectdetection server
    
    #resolution 2 is 160x120
    #resolution 1 is 320x240
    
    #return tuple (ov7670 interface, framebuffer)

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
    cam.size = resolution
    cam.colorspace = colorspace
    print("{}x{}".format(cam.width, cam.height))

    print("allocating framebuffer")
    buf = bytearray(2 * cam.width * cam.height)
    
    return (cam, buf)