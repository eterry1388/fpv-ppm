#!/usr/bin/env python3

import sys
import numpy as np
import sounddevice as sd
import pygame
from pygame import locals
from threading import Thread
from time import sleep

channels = {
  1: 50.0,
  2: 50.0,
  3: 50.0,
  4: 50.0,
  5: 0.0,
  6: 0.0,
  7: 0.0,
  8: 0.0,
}

pygame.init()
pygame.joystick.init()

sticks = pygame.joystick.Joystick(0)
sticks.init()

def threaded_function():
    try:
        def callback(outdata, frames, time, status):
            if status:
                print(status, file=sys.stderr)

            # print(channels)

            a = float(44100)/10000

            wave_array = []
            wave_array += [[-1.0]] * int(a*4)
            for i in channels:
              wave_array += [[1.0]] * int(a*7)
              b = channels[i] * 0.75/100
              channel_metric = (a*10) * b
              wave_array += [[1.0]] * int( channel_metric )
              wave_array += [[-1.0]] * int(a*4)

            list = []
            for i in range(0, frames-len(wave_array)):
              list += [[1.0]]

            list += wave_array

            # print(list)

            stuff = np.array(list)
            outdata[:] = stuff

        with sd.OutputStream(device=1, channels=1, callback=callback, samplerate=44100, blocksize=992):
            input()
    except KeyboardInterrupt:
        parser.exit('Exited')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))

if __name__ == "__main__":
    thread = Thread(target = threaded_function)
    thread.start()
    # thread.join()

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.locals.JOYAXISMOTION:
                a, b, c, d = sticks.get_axis(0), sticks.get_axis(1), sticks.get_axis(2), sticks.get_axis(3)

                channels[1] = ((d + 1) / 2.0) * 100.0
                channels[2] = ((c + 1) / 2.0) * 100.0
                channels[3] = ((a + 1) / 2.0) * 100.0
                channels[4] = ((b + 1) / 2.0) * 100.0
