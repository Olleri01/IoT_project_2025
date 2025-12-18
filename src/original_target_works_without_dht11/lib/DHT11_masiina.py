import time
import adafruit_dht
import board

class DHT11:
    
#temperature_c = 0.0
    def __init__(self, pin =board.GP27):
        self.sensor = adafruit_dht.DHT11(pin)
        

    def read_humidity(self, samplesize=3, delay = 2.0):
        
        humidity = 0.0
        i = 0
        cum_temp = 0.0
        error_count = 0
        while(i<samplesize):
            try: 
                #temperature_c = sensor.temperature
                cum_temp = cum_temp + self.sensor.humidity
                i = i+1
            except RuntimeError as error:
                if error_count>4: #if keeps erroring return null to not jam the device
                    return None
                error_count = error_count+1
                time.sleep(2.0)
                continue
        return cum_temp/3.0 #return average value of the temperatures

