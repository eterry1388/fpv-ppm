#!/usr/bin/env python3

import sys
import numpy as np
import sounddevice as sd
from threading import Thread
from time import sleep
import asyncio
import websockets
import json

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

# initial_mag_blah
last_twenty_frames = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
last_five_direction_frames = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
last_uaac_y = 0
absolute_uacc_y = 0
uaac_down_movement_active = False
uaac_up_movement_active = False
initial_heading = None

def clamp(num, min_value, max_value):
  return max(min(num, max_value), min_value)

async def consumer_handler(websocket, path):
  async for message in websocket:
    sensors = json.loads(message)

    acc_x = clamp(float(sensors["accX"]), -1, 1)
    acc_y = clamp(float(sensors["accY"]), -1, 1)

    mag_x = float(sensors["magX"])
    mag_y = float(sensors["magY"])
    mag_z = float(sensors["magZ"])

    gra_x = float(sensors["graX"])
    gra_y = float(sensors["graY"])
    gra_z = float(sensors["graZ"])

    uacc_x = float(sensors["uaccX"])
    uacc_y = round(float(sensors["uaccY"]), 1)
    uacc_z = float(sensors["uaccZ"])

    heading = float(sensors["heading"])

    touch_x = float(sensors["touchX"])
    touch_y = float(sensors["touchY"])

    global last_twenty_frames
    global last_five_direction_frames
    global last_uaac_y
    global absolute_uacc_y
    global uaac_down_movement_active
    global uaac_up_movement_active
    global initial_heading

    last_twenty_frames.pop(0)
    last_twenty_frames.append(uacc_y)

    # if sum(map(lambda a: abs(a), last_twenty_frames)) < 3.0:
    if sum(last_five_direction_frames) == 0:
      uaac_down_movement_active = False
      uaac_up_movement_active = False

    diff_array = []

    for i in range(len(last_twenty_frames)-1):
      diff_array.append(last_twenty_frames[i+1] - last_twenty_frames[i])

    pop_it = False

    if uaac_up_movement_active == False and sum(diff_array) > 0.5:
      print("down")
      last_five_direction_frames.pop(0)
      last_five_direction_frames.append(1)
      uaac_down_movement_active = True
      pop_it = True

    if sum(diff_array) > 0.5:
      uaac_down_movement_active = True

    if uaac_down_movement_active == False and sum(diff_array) < -0.5:
      print("up")
      last_five_direction_frames.pop(0)
      last_five_direction_frames.append(1)
      uaac_up_movement_active = True
      pop_it = True

    if sum(diff_array) < -0.5:
      uaac_up_movement_active = True

    if pop_it == False:
      last_five_direction_frames.pop(0)
      last_five_direction_frames.append(0)

    # if uaac_up_movement_active == False and uacc_y > 0 and uacc_y > last_uaac_y and abs(uacc_y - last_uaac_y) > 0.3:
    #   # print("down")
    #   uaac_down_movement_active = True
    #   absolute_uacc_y += uacc_y

    # if uaac_down_movement_active == False and uacc_y < 0 and uacc_y < last_uaac_y and abs(uacc_y - last_uaac_y) > 0.3:
    #   # print("up")
    #   uaac_up_movement_active = True
    #   absolute_uacc_y += uacc_y

    # last_uaac_y = uacc_y

    # print(absolute_uacc_y)

    # print(f"{round(mag_x, 4)} | {round(mag_y, 4)} | {round(mag_z, 4)}")
    # print(f"{round(gra_x, 4)} | {round(gra_y, 4)} | {round(gra_z, 4)}")
    # print(f"{round(uacc_x, 4)} | {round(uacc_y, 4)} | {round(uacc_z, 4)}")

    if initial_heading == None:
      initial_heading = heading

    diff_heading = heading - initial_heading

    yaw = clamp(50.0 + (diff_heading * 1.5), 0.0, 100.0)
    roll = clamp((((acc_x + 1) / 2.0) * 100.0), 0.0, 100.0)
    pitch = clamp((((acc_y + 1) / 2.0) * 100.0), 0.0, 100.0)
    throttle = clamp((550.0 - touch_y) / 4.0, 0.0, 100.0)

    # print(f"{round(pitch, 4)} | {round(acc_y, 4)}")

    # print(heading)

    channels[1] = yaw
    channels[2] = pitch
    channels[3] = throttle
    channels[4] = roll

def threaded_function():
    try:
        samplerate = 44100

        def callback(outdata, frames, time, status):
            if status:
                print(status, file=sys.stderr)

            # print(channels)

            a = float(samplerate)/10000

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

        with sd.OutputStream(device=1, channels=1, callback=callback, samplerate=samplerate, blocksize=992):
            input()
    except KeyboardInterrupt:
        parser.exit('Exited')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))

if __name__ == "__main__":
    thread = Thread(target = threaded_function)
    thread.start()

    start_server = websockets.serve(consumer_handler, "0.0.0.0", 8080)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
