from picozero import LED
from time import sleep

leds = [LED(0), LED(1), LED(2), LED(3), LED(4), LED(5), LED(6), LED(7), LED(8), LED(9), LED(10)]

for led in leds:
    led.on()