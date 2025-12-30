import time
import analogio
import board

class CRT00549L:
    
    
    def __init__(self, pin = board.GP26):
        self.sensor = analogio.AnalogIn(pin)
        
    def read_sensor():
        try:
            return self.sensor.value *3.3 /65535
        except: 
            return None
        
    def read_luminance(self, samplesize=3, delay = 2.0):
        
        luminance = 0.0
        i = 0
        cum_luminance = 0.0
        error_count = 0
        while(i<samplesize):
            try: 
                #temperature_c = sensor.temperature
                cum_luminance = cum_luminance + self.sensor.value*3.3 /65535
                i = i+1
            except RuntimeError as error:
                if error_count>4: #if keeps erroring return null to not jam the device
                    return None
                error_count = error_count+1
                time.sleep(2.0)
                continue
        return cum_luminance/3.0 #return average value of the temperatures