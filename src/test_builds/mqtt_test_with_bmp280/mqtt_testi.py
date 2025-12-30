#https://learn.adafruit.com/mqtt-in-circuitpython/circuitpython-wifi-usage

import board
import busio
import time
from lib import adafruit_minimqtt as MQTT
import wifi
import adafruit_connection_manager
import config
import adafruit_bmp280
import json
import DHT11_masiina
import CRT00549L_masiina
print("initializing i2c for bmp280")
i2c = busio.I2C(scl = board.GP1,sda = board.GP0)#scl, sca

bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
print("bmp280 initialization complete")
humidity_sensor = DHT11_masiina.DHT11()
luminance_sensor = CRT00549L_masiina.CRT00549L()





def collect_data():
    data_message = {"datetime": time.time(),
        "currentHourWalkers":0,
        "currentHourCyclists": 	0,
        "location": "Oulu, Akselin WC",
        "temperature":bmp280.temperature,
        "luminosity": 	luminance_sensor.read_luminance(),
        "humidity": humidity_sensor.read_humidity(),
        "pressure": bmp280.pressure,
        }
    print(data_message)
    return json.dumps(data_message)
    
"""topics

"skynet" #root
"skynet/calculator"
"skynet/intel_data"

esimerkkiviesti:

{
"datetime": 0,
"currentHourWalkers":0,
"currentHourCyclists": 	0,
"location": "asdasddfg",
"temperature":0.0,
"luminosity": 	0.0,
"humidity": 0.0,
}

queryt datakyselyitä varten

"skynet/get_all_data" 		   ## client laittaa tämän mqtt välittäjälle, tietokanta saa viestin että
                               ## pukkaa kaikki tavara takaisin tähän topiciin Jiisonnina
"skynet/get_current_week_data" ## client laittaa tämän mqtt välittäjälle, tietokanta saa viestin että
                               ## pukkaa viikon aikana kerätty tavara takaisin tähän topiciin Jiisonnina
"skynet/get_current_day_data"  ## sama homma mutta samalta päivältä

"skynet/save_hourly_data" ## laite lähettää tähän topiciin joka tunti jiisonnin
                          ## joka tallentuu tietokantaan
"""

try: 
    print(f"Connecting to {config.WIFI_SSID}")
    wifi.radio.connect(config.WIFI_SSID, config.WIFI_PWD)
    print(f"Connected to {config.WIFI_SSID}")
except:
    print("wifi connection not succesfull s")

#NTP.begin("pool.ntp.org", "time.nist.gov");

def connected(client, userdata,flags,rc):
    print(f"olemme yhtyneet emqx välittäjään, skipidi foprtnite")
    client.subscribe("skynet/intel_data")

def disconnected(client, userdata,flags,rc):
    print("disconnected from mqtt broker")

def message(client, topic, message):
    print(f'New msg on topic {topic}:{message}')
    
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

def mqttSetup():
    global mqtt_client
    mqtt_client = MQTT.MQTT(
        broker=config.MQTT_BROKER,
        username=config.MQTT_USER,
        password=config.MQTT_PWD,
        socket_pool=pool,
        is_ssl = True,
        ssl_context=ssl_context,
        )
    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message
    mqtt_client.connect(host = config.MQTT_BROKER, port = config.MQTT_PORT)
    

def mqtt_loop():
    while True:
        mqtt_client.loop(timeout=2)
        print("sending new  message to topic skynet/intel_data")
        message = collect_data()
        mqtt_client.publish("skynet/intel_data", message)
        time.sleep(60)

def main():
    print("maini on elossa")
    mqttSetup()
    mqtt_loop()
    

if __name__ == "__main__":
    main()