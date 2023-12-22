# https://cdn.mos.cms.futurecdn.net/BFxYH7LXL2ABjGsEp6DU7Z-970-80.png

from picozero import LED
from time import sleep

red = LED(28)

red.pulse() # 1s to brighten and 1s to dim, asynchronous
print("Pulsing 3 times over 6 seconds")
sleep(6)
red.off()

sleep(1)

print("Pulsing 5 more times")
red.pulse(fade_in_time=0.5, fade_out_time=0.2, n=5, wait=True)

print("Finished pulsing")