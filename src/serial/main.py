# Max image size 320*240 (DIV2)

import sys
import time
import machine
from ov7670_wrapper import *

data_pin_base   = 0 # 0 and the next 7 pins. So GPIO 0-7 in this case.
pclk_pin_no     = 9
mclk_pin_no     = 8
href_pin_no     = 11
vsync_pin_no    = 10
reset_pin_no    = 14
shutdown_pin_no = 15
sda_pin_no      = 12
scl_pin_no      = 13

i2c = machine.I2C(0, freq=100000, scl=machine.Pin(scl_pin_no), sda=machine.Pin(sda_pin_no))
ov7670 = OV7670Wrapper(
    i2c_bus=i2c,
    mclk_pin_no=mclk_pin_no,
    pclk_pin_no=pclk_pin_no,
    data_pin_base=data_pin_base,
    vsync_pin_no=vsync_pin_no,
    href_pin_no=href_pin_no,
    reset_pin_no=reset_pin_no,
    shutdown_pin_no=shutdown_pin_no,
    half_capture=True, #True for grayscale, False for rgb
    
)

ov7670.wrapper_configure_yuv() #grayscale
#ov7670.wrapper_configure_rgb() #rgb
ov7670.wrapper_configure_base()
width,height = ov7670.wrapper_configure_size(OV7670_WRAPPER_SIZE_DIV2)
ov7670.wrapper_configure_test_pattern(OV7670_WRAPPER_TEST_PATTERN_NONE)

buf = bytearray(width*height)
#buf = bytearray(width*height*2)

ov7670.capture(buf)

ready = sys.stdin.buffer.read(1)
    
if ready and ready[0] == 1:
    sys.stdout.buffer.write(buf)

    
    