# -*- coding: utf-8 -*-
# Main CircuitPython implementation for the 4tronix M.A.R.S. Rover Robot remote control 
# using the PiHut Wireless USB Game Controller. 
#
# Copyright 2025 Istvan Z. Kovacs. All Rights Reserved.
#
# Version: 1.0.1
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import time
from sys import exit

# The custom drive functions library
from drivefunc import init_rover, drive_rover, stop_rover, cleanup_rover, move_mast
from drivefunc import seq_all_leds, LED_GREEN, LED_RED, LED_BLUE, LED_WHITE, LED_BLACK
# The wireless USB Game Controller library
from pihutwugc import PiHutWUSBGameController

VERSION = "1.0.1"

# Debug mode
DEBUG_MODE = True

SD_SQUARE = False
SD_CIRCLE = False
SD_CMD = False
RB_TRIANGLE = False
RB_CROSS = False
RB_CMD = False

LED_BRIGHT = 0.4

def debug_print_exception(exc):
    if DEBUG_MODE:
        from traceback import print_exception
        print_exception(exc)

# Main loop
# Outer try / except used to init the controller and 
# catches the critical Exception to end cleanly, shutting the motors down.
# Restart possible on reset only.
try_usb = True
while try_usb:
    try:
        # Init the USB controller
        pihutwugc = PiHutWUSBGameController()

        # Init the rover
        init_rover(LED_BRIGHT)

        # Rotating LED lights
        seq_all_leds(2, 0.2, LED_GREEN)
        
        while pihutwugc.connected:
            # Inner loop is where we read the received remote controller commands 
            # and control the driving of the rover.
            try:
                # Read the controller keys
                if pihutwugc.read_keys():

                    # Control the driving of the rover based on the received commands from the joysticks
                    ly_axis = pihutwugc['ls_y'] 
                    rx_axis = pihutwugc['rs_x'] 
                    ry_axis = pihutwugc['rs_y']
                    #print(f"{rx_axis}:{ry_axis}")
                    drive_rover(yaw=0.0, throttle=ly_axis, l_r=rx_axis, f_b=ry_axis)
                
                    # Control the mast position based on the received commands from the DPad keys
                    dpad_left  = pihutwugc['dleft'] == 1.0
                    dpad_right = pihutwugc['dright'] == 1.0
                    dpad_up    = pihutwugc['dup'] == 1.0
                    dpad_down  = pihutwugc['ddown'] == 1.0
                    move_mast(dpad_left, dpad_right, dpad_up, dpad_down)

                    # Coast to stop
                    if pihutwugc['circle']:
                        stop_rover()

                # Wait a short time before reading the controller again?
                time.sleep(0.1)

            except ValueError as exc:
                debug_print_exception(exc)

                seq_all_leds(1, 0.3, LED_RED)
                seq_all_leds(1, 0.3, LED_BLUE)
                seq_all_leds(1, 0.3, LED_RED)

                # Re-initialize the USB controller?
                # Re-try after a short delay?
                
                time.sleep(1.0)
                pass

    except RuntimeError as exc:
        debug_print_exception(exc)
        try_usb = True
        cleanup_rover()
    except KeyboardInterrupt:
        try_usb = False
        cleanup_rover()
        exit(0)
    except Exception as exc:  
        debug_print_exception(exc)
        try_usb = False
        cleanup_rover()
        exit(1)
    finally:
        seq_all_leds(3, 0.2, LED_RED)
        time.sleep(1.0)
        
