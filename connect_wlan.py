import time
import network
from picozero import pico_led

ssid = 'West 2G'
password = 'fudgiemilkyway204'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
pico_led.blink(on_time=0.5)
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('Waiting for connection...')
    time.sleep(1)
    
# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('Network connection failed with status {}'.format(wlan.status()))
else:
    print('Connected to {}'.format(ssid))
    status = wlan.ifconfig()
    print('IP = ' + status[0])
    pico_led.blink(on_time=0.1, off_time=0.1, n=3, wait=True)
    
