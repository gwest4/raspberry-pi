# https://cdn.mos.cms.futurecdn.net/BFxYH7LXL2ABjGsEp6DU7Z-970-80.png

from picozero import LED
from time import sleep

red = LED(28)
red.on()
sleep(1)
red.off()