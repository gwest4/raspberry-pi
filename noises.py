from picozero import Speaker
from time import sleep
from random import randint

speaker = Speaker(14)
speaker.off()

def win(): # rising frequency
    for i in range(2000, 5000, 100):
        speaker.play(i, 0.05) # short duration
        
def chirp(): # series of high-pitched chirps
    for _ in range(2): # decreasing frequency
        for i in range(5000, 2999, -100):
            speaker.play(i, 0.02) # very short duration
        sleep(0.2)
        
def sound_machine():
    for i in range(8):
        speaker.play(randint(500, 5000), duration=.02)
        sleep(0.001)
        speaker.off()
        sleep(0.5)

win()
sleep(1)
chirp()
sleep(1)
sound_machine()