# https://cdn.mos.cms.futurecdn.net/BFxYH7LXL2ABjGsEp6DU7Z-970-80.png

from picozero import LED
from time import sleep

red = LED(28)

red.blink() # 1s interval, asynchronous
print("Blinking 3 times over 6 seconds")
sleep(6)
red.off()

sleep(1)

print("Blinking 5 more times")
red.blink(on_time=0.5, off_time=0.2, n=5, wait=True) # Synchronous

print("Finished blinking")