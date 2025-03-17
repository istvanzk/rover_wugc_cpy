# -*- coding: utf-8 -*-
# Main ASYNC CircuitPython implementation for the 4tronix M.A.R.S. Rover Robot remote control 
# using the PiHut Wireless USB Game Controller. 
#
# Copyright 2025 Istvan Z. Kovacs. All Rights Reserved.
#
# Version: 1.1.1
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

import asyncio

# The custom drive functions library
from drivefunc import init_rover, drive_rover, stop_rover, brake_rover, move_mast, reset_mast, cleanup_rover
from drivefunc import seq_all_leds_async, flash_all_leds_async, set_rlfb_led_async, LED_GREEN, LED_RED, LED_BLUE
# The wireless USB Game Controller library
from pihutwugc import PiHutWUSBGameController

VERSION = "1.1.1"

# Debug mode
DEBUG_MODE = True

# LEDs brightness
LED_BRIGHT = 0.4

def debug_print_exception(exc):
    if DEBUG_MODE:
        from traceback import print_exception
        print_exception(exc)

class DriveParams:
    """ Class for sharing the drive control parameters between async tasks. """
    def __init__(self):
        self.active = True

        self.lx_axis = 0.0
        self.ly_axis = 0.0
        self.rx_axis = 0.0
        self.ry_axis = 0.0
        self.stop    = False
        self.brake   = False

class MastParams:
    """ Class for sharing the mast control parameters between async tasks. """
    def __init__(self):
        self.active = True
           
        self.left   = False
        self.right  = False
        self.up     = False
        self.down   = False

class LEDParams:
    """ Class for sharing the LEDs control parameters between async tasks. """
    def __init__(self, brightness=None):
        if brightness > 0:
            self.active = True
        else:
            self.active = False

        self.startup     = False
        self.stop        = False
        self.brake       = False
        self.dir         = 0.0
        self.speed       = 0.0

class OtherParams:
    """ Class for sharing the other control parameters between async tasks. """
    def __init__(self):
        self.active = True

        self.other = 0.0


async def wugctask(drive_params, mast_params, other_params):
    """ The async WUGC task cto read the key presses from the remote controller. """

    # Outer try / except used to init the controller and 
    # catches the critical Exception to end cleanly, shutting the motors down.
    try_usb = True
    while try_usb:
        try:
            # Init the USB controller
            pihutwugc = PiHutWUSBGameController()
            
            while pihutwugc.connected:    
                # Inner loop is where we read the received remote controller commands 
                # and control the driving of the rover.
                try:
                    # Read the controller keys
                    if pihutwugc.read_keys():
                        # Control the driving of the rover based on the received commands from the joysticks
                        drive_params.lx = 0.0
                        drive_params.ly = pihutwugc['ls_y'] 
                        drive_params.rx = pihutwugc['rs_x'] 
                        drive_params.ry = pihutwugc['rs_y']
                        # Coast to stop
                        drive_params.stop = pihutwugc['circle'] == 1.0
                        drive_params.brake = pihutwugc['square'] == 1.0
                    
                        # Control the mast position based on the received commands from the DPad keys
                        mast_params.left  = pihutwugc['dleft'] == 1.0
                        mast_params.right = pihutwugc['dright'] == 1.0
                        mast_params.up    = pihutwugc['dup'] == 1.0
                        mast_params.down  = pihutwugc['ddown'] == 1.0


                    # Wait a short time before reading the controller again
                    await asyncio.sleep(0.1)

                except ValueError as exc:
                    debug_print_exception(exc)
                    await asyncio.sleep(1.0)
                    pass

        except RuntimeError as exc:
            debug_print_exception(exc)
            try_usb = True
            pass
        except Exception as exc:  
            debug_print_exception(exc)
            try_usb = False
            pass
        finally:
            await asyncio.sleep(1.0)

    # Set the shutdown flag for all other tasks
    drive_params.active = False
    mast_params.active  = False
    other_params.active = False

async def drivetask(drive_params, leds_params):
    """ The async task for driving the rover using the received commands. """

    # Init the rover
    init_rover(LED_BRIGHT)

    asyncio.create_task(flash_all_leds_async(3, 0.5, LED_GREEN))
    await asyncio.sleep(2.5)
    print('Init done')

    # Control loop
    while drive_params.active:
        if drive_params.stop:
            # Stop rover movement
            stop_rover()
            print('Drive: stop')
            asyncio.create_task(seq_all_leds_async(3, 0.3, LED_RED))
            await asyncio.sleep(4.0)
        elif drive_params.brake:
            # Brake rover movement
            brake_rover()
            print('Drive: brake')
            asyncio.create_task(seq_all_leds_async(2, 0.2, LED_RED))
            await asyncio.sleep(2.0)
        else:
            # Drive the rover
            _dir, _speed = drive_rover(
                yaw = 0.0, 
                throttle = drive_params.ly, 
                l_r = drive_params.rx, 
                f_b = drive_params.ry)
            #asyncio.create_task(set_rlfb_led_async(_speed, _dir)) # DOES NOT WORK CORRECTLY!
            asyncio.create_task(set_rlfb_led_async(0, 0.0))
            await asyncio.sleep(0.1)

        await asyncio.sleep(0)

    # End/exit
    cleanup_rover()
    leds_params.active = False

async def masttask(mast_params, leds_params):
    """ The async task for moving the mast using the received commands. """

    # Control loop
    while mast_params.active:
        move_mast(mast_params.left, 
                mast_params.right, 
                mast_params.up, 
                mast_params.down)

        await asyncio.sleep(0.1)

    # End/exit
    reset_mast()

async def othertask(other_params, leds_params):
    """ The async task for other actions using the received commands/parameters. """

    while other_params.active:
        # other_params.*
        await asyncio.sleep(0.2)

    # End/exit

async def ledstask(leds_params):
    """ The async task for LEDs control using the received parameters. """

    while leds_params.active:
        if leds_params.startup:
            #asyncio.create_task(flash_all_leds_async(3, 0.5, LED_GREEN))
            leds_params.startup = False
            print('LEDS startup')
            await asyncio.sleep(0)

        elif leds_params.stop:
            #asyncio.create_task(seq_all_leds_async(3, 0.3, LED_RED))
            leds_params.stop = False
            print('LEDS stop')
            await asyncio.sleep(0)

        elif leds_params.brake:
            #asyncio.create_task(seq_all_leds_async(2, 0.2, LED_RED))
            leds_params.brake = False
            print('LEDS brake')
            await asyncio.sleep(0)

        else:
            #asyncio.create_task(set_rlfb_led_async(leds_params.speed>0, leds_params.dir))
            await asyncio.sleep(0)

    # End/exit


async def main():
    """ Main async tasks. """

    # The shared parameters
    drive_params = DriveParams()
    mast_params  = MastParams()
    other_params = OtherParams()
    leds_params  = LEDParams(LED_BRIGHT)

    # Create the async tasks
    wugc_task  = asyncio.create_task(wugctask(drive_params, mast_params, other_params))
    drive_task = asyncio.create_task(drivetask(drive_params, leds_params))
    mast_task  = asyncio.create_task(masttask(mast_params, leds_params))
    other_task = asyncio.create_task(othertask(other_params, leds_params))
    #leds_task  = asyncio.create_task(ledstask(leds_params))

    # This will run until all tasks exit
    await asyncio.gather(wugc_task, drive_task, mast_task, other_task)

# Run the async tasks
asyncio.run(main())