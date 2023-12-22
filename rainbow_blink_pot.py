from picozero import Pot # Pot is short for Potentiometer
from picozero import LED
from time import sleep

pot = Pot(0) # Connected to pin A0 (GP_26)

def lerp(x, y, a):
    return ((y - x) * a) + x

leds = [LED(0), LED(1), LED(2), LED(3), LED(4), LED(5), LED(6),
        LED(7), LED(8), LED(9), LED(10)]

for led in leds:
    led.off()

while True:
    for led in leds:
        t = lerp(0.01, 0.05, pot.value)
        led.blink(on_time=t, off_time=t, n=1, wait=True) # Synchronous