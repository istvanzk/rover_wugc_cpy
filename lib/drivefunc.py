# -*- coding: utf-8 -*-
# CircuitPython implemenation for custom rover drive functions 
# for the 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller
#
# Copyright 2025 Istvan Z. Kovacs. All Rights Reserved.
#
# Version: 1.0.0
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
from os import getenv
from time import sleep
from math import tan, atan2, pi, sqrt
import gc

# The CircuitPython rover libary 
try:
    from rover_cpy import RoverClass
except:
    raise RuntimeError("M.A.R.S. Rover CircuitPython library is not available! Please make sure it is in the /lib folder.")

VERSION = "1.0.5"

# Use the async version of the LEDs functions
# The *_async functions are to be used in async tasks (not implemented in this module)
USE_ASYNC = True

# Steering mode
ROVER_STEERING_MODE = getenv('ROVER_STEERING_MODE','simple') # 'simple' or 'ackermann'

# 4tronix M.A.R.S. Rover physical parameters
# The ratio between the left-right wheel distance (chasis width) and
# the front-back wheel distance (chassis length)
ROVER_DoL = 80.0/77.0
# The wheel radius (mm)
ROVER_WhR = 45.0/2.0

# The direction filter
DIR_FILTER_LNG = 3
dir_filter = [0.0,0.0,0.0]
rover_speed = 0
rover_dir = 0
prev_dir = 0

# The mast pan&tilt parameters
MAST_PAN_STEP = 2
pan_deg = 0
MAST_TILT_STEP = 2
tilt_deg = 0

#
# LED colors
#
LED_BLACK  = (0,0,0)
LED_RED    = (255,0,0)
LED_ORANGE = (255,255,0)
LED_GREEN  = (0,255,0)
LED_BLUE   = (0,0,255)
LED_CYAN   = (0,255,255)
LED_YELLOW = (255,255,0)
LED_MAGENTA = (255,0,255)
LED_WHITE    = (255,255,255)
LED_RED_H    = (100,0,0)
LED_ORANGE_H = (100,100,0)
LED_GREEN_H  = (0,100,0)
LED_BLUE_H   = (0,0,100)
LED_CYAN_H   = (0,100,100)
LED_YELLOW_H = (100,100,0)
LED_MAGENTA_H = (100,0,100)
LED_WHITE_H  = (100,100,100)

#
# Custom rover drive functions
#
rover = None
def init_rover(led_brightness: float = 0) -> None:
    """
    Initialise rover library.

    :param led_brightness: 
        LEDs default brightness, ranges from 0 to 1
    """
    global rover

    if rover is not None:
        return
    
    try:
        rover = RoverClass()
        if led_brightness > 0 and led_brightness <= 1:
            # Init rover with provided LED brightness
            rover.init(led_brightness)
            if not USE_ASYNC:
                # Set all LEDs to green
                flash_all_leds(3, 0.3, LED_GREEN)
                #flash_all_leds(1, 0.1, LED_GREEN_H)
        else:
            # No LEDs used
            rover.init()
    except:
        rover = None
        raise RuntimeError("The custom rover functions could not be initialized!")


def drive_rover(
    yaw: float = 0.0,
    throttle: float = 0.0,
    l_r: float = 0.0,
    f_b: float = 0.0
) -> None:
    """
    Drive/steer the rover based on the yaw, throttle, left-right and front-back input values.

    :param yaw: 
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle: 
        Throttle axis value, ranges from -1.0 to 1.0
    :param l_r: 
        Left-right axis value, ranges from -1.0 to +1.0
    :param f_b: 
        Fwd-back axis value, ranges from -1.0 to +1.0

    : return rover_dir:
        Rover steering angle (-50 to +50 deg)
    : return rover_speed:
        Rover speed (-100 to 100)
    """
    # Driving modes
    global rover_speed
    global rover_dir
    global rover
    if rover is None:
        return

    if ROVER_STEERING_MODE == 'simple':
        # Get rover speed from mixer function (= rover speed value for all 6 motors)
        rover_speed_current, _ = _mixer_speed(
            yaw=yaw,
            throttle=throttle)

        # Get rover direction from mixer function (= angle value for all 4 motors)
        rover_dir_current = _mixer_dir(
            l_r=l_r,
            f_b=f_b,
            max_dir=50)
        
        # Set rover direction and rover speed
        if rover_speed != rover_speed_current or rover_dir != rover_dir_current:
            _move_rover(
                dir_deg=rover_dir_current,
                speed_per=rover_speed_current)
            rover_dir = rover_dir_current
            rover_speed = rover_speed_current

    elif ROVER_STEERING_MODE == 'ackermann':
        # Get rover speed from mixer function (= speed of the rover)
        rover_speed_current, _ = _mixer_speed(
            yaw=yaw,
            throttle=throttle)

        # Get rover direction from mixer function (= steering angle of the rover)
        rover_dir_current = _mixer_dir(
            l_r=l_r,
            f_b=f_b,
            max_dir=50)

        # Set rover rover direction and rover speed
        if rover_speed != rover_speed_current or rover_dir != rover_dir_current:
            _move_rover_ackermann(
                dir_deg=rover_dir_current,
                speed_per=rover_speed_current)
            rover_dir = rover_dir_current
            rover_speed = rover_speed_current

    return rover_dir, rover_speed

def stop_rover() -> None:
    """
    Coast to stop.
    """
    global rover
    if rover is None:
        return

    # Stop rover
    rover.stop()

    if not USE_ASYNC:
        # Flash 3 times all LEDs in red
        flash_all_leds(2, 0.4, LED_RED)

def brake_rover() -> None:
    """
    Brake and stop quickly.
    """
    global rover
    if rover is None:
        return

    rover.brake()

    if not USE_ASYNC:
        # Flash 3 times all LEDs in red
        flash_all_leds(2, 0.2, LED_RED)


def move_mast(
    dleft: bool = False,
    dright: bool = False, 
    dup: bool = False, 
    ddown: bool = False
) -> None:
    """
    Move the pan&tilt mast on the rover.

    :param dleft: 
        Indicates a pan step to left.
    :param dright: 
        Indicates a pan step to right.        
    :param dup: 
        Indicates a tilt step to up.        
    :param ddown: 
        Indicates a tilt step to down.                

    """
    global pan_deg
    global tilt_deg
    global rover
    if rover is None:
        return

    # Pan step
    if dleft:
        pan_deg -= MAST_PAN_STEP
        pan_deg = max(-90, pan_deg)
    elif dright:
        pan_deg += MAST_PAN_STEP
        pan_deg = min(90, pan_deg)

    # Tilt step
    if dup:
        tilt_deg += MAST_TILT_STEP
        tilt_deg = min(90, tilt_deg)
    elif ddown:
        tilt_deg -= MAST_TILT_STEP
        tilt_deg = max(-90, tilt_deg)

    # Mode the mast
    _move_mast(p_deg=pan_deg, t_deg=tilt_deg)


def reset_mast():
    """ Reset the position of the mast. """
    _move_mast(p_deg=0, t_deg=0)


def cleanup_rover() -> None:
    """
    Cleanup rover library.
    """
    global rover
    if rover is None:
        gc.collect()
        return

    if not USE_ASYNC:
        # Rotating LED lights
        seq_all_leds(2, 0.25, LED_RED)

    # Clean exit
    del rover
    rover = None
    gc.collect()


#
# TODO: Force-feedback functions
#
def rumble_start(wugc: int = None) -> None:
    """
    Activate force-feedback.
    Rumble tow times shortly.

    :param wugc: 
        WUSBGameController
    """
    pass

def rumble_end(wugc: int = None) -> None:
    """
    Activate force-feedback.
    Rumble tow times shortly.

    :param wugc: 
        WUSBGameController
    """
    pass


#
# LED effects functions
#
def flash_all_leds(
    fnum: int = 3, 
    dly: float = 0.5, 
    col: tuple = (0, 0, 0),
) -> None:
    """
    Flash all LEDs simultanously.

    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes
    :param col: 
        LED light color to use
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    for _ in range(fnum):
        rover.clear()
        sleep(dly)
        rover.setColor(col)
        sleep(dly)          
    rover.clear()

async def flash_all_leds_async(
    fnum: int = 3, 
    dly: float = 0.5, 
    col: tuple = (0, 0, 0),
) -> None:
    """
    ASYNC Flash all LEDs simultanously.

    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes
    :param col: 
        LED light color to use
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    for _ in range(fnum):
        rover.clear()
        await asyncio.sleep(dly)
        rover.setColor(col)
        await asyncio.sleep(dly)          
    rover.clear()


def seq_all_leds(
    fnum: int = 3, 
    dly: float = 0.5, 
    col: tuple = (0, 0, 0)
) -> None:
    """
    Flash all LEDs in sequence.

    :param fnum: 
        Number of sequences (all LEDs)
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col: 
        LED light color to use
    """
    global rover
    if rover is  None:
        return
    if rover.LED_Device is None:
        return
    rover.clear()
    for _ in range(fnum):
        for _l in range(rover.LED_numPixels):
            rover.clear()
            rover.setPixel(_l, col)
            rover.show()
            sleep(dly)
    rover.clear()

async def seq_all_leds_async(
    fnum: int = 3, 
    dly: float = 0.5, 
    col: tuple = (0, 0, 0)
) -> None:
    """
    ASYNC Flash all LEDs in sequence.

    :param fnum: 
        Number of sequences (all LEDs)
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col: 
        LED light color to use
    """
    global rover
    if rover is  None:
        return
    if rover.LED_Device is None:
        return
    rover.clear()
    for _ in range(fnum):
        for _l in range(rover.LED_numPixels):
            rover.clear()
            rover.setPixel(_l, col)
            rover.show()
            await asyncio.sleep(dly)
    rover.clear()

def flash_led(
    led: int = 0,
    fnum: int = 3, 
    dly: float = 0.5, 
    col1: tuple = LED_BLACK, 
    col2: tuple = LED_WHITE
) -> None:
    """
    Flash a LED between two colors.

    :param led: 
        LED number, ranges from 0 to LED_NUM-1
    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col1: 
        First LED light color to use
    :param col2: 
        Second LED light color to use
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    for _ in range(fnum):
        rover.setPixel(led, col1)
        rover.show()
        sleep(dly)
        rover.setPixel(led, col2)
        rover.show()
        sleep(dly)
    rover.clear()

async def flash_led_async(
    led: int = 0,
    fnum: int = 3, 
    dly: float = 0.5, 
    col1: tuple = LED_BLACK, 
    col2: tuple = LED_WHITE
) -> None:
    """
    ASYNC Flash a LED between two colors.

    :param led: 
        LED number, ranges from 0 to LED_NUM-1
    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col1: 
        First LED light color to use
    :param col2: 
        Second LED light color to use
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    for _ in range(fnum):
        rover.setPixel(led, col1)
        rover.show()
        await asyncio.sleep(dly)
        rover.setPixel(led, col2)
        rover.show()
        await asyncio.sleep(dly)
    rover.clear()

def set_rlfb_led(
    fwd: bool = True, 
    dir_deg: float = 0.0
) -> None:
    """
    Set forward-rear and left-right LEDs.

    :param fwd: 
        Movement forward (True) or reverse (False)
    :param dir_deg: 
        Movement right (>0) or straight (=0) or left (<0)
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    if fwd:
        # Set all LEDs
        rover.setPixel(1, LED_WHITE)
        rover.setPixel(2, LED_WHITE)
        rover.setPixel(0, LED_RED_H)
        rover.setPixel(3, LED_RED_H)
        rover.show()

        # Blink forward-right LED
        if dir_deg > 0:  # right
            flash_led(2, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(2, LED_WHITE)
            rover.show()
        # Blink forward-left LED
        elif dir_deg < 0:  # left
            flash_led(1, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(1, LED_WHITE)
            rover.show()

    else:
        # Set all LEDs
        rover.setPixel(1, LED_WHITE_H)
        rover.setPixel(2, LED_WHITE_H)
        rover.setPixel(0, LED_RED)
        rover.setPixel(3, LED_RED)
        rover.show()

        # Blink back-right LED
        if dir_deg > 0:  # right
            flash_led(3, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(3, LED_RED)
            rover.show()

        # Blink back-left LED
        elif dir_deg < 0:  # left
            flash_led(0, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(0, LED_RED)
            rover.show()

async def set_rlfb_led_async(
    fwd: bool = True, 
    dir_deg: float = 0.0
) -> None:
    """
    ASYNC Set forward-rear and left-right LEDs.

    :param fwd: 
        Movement forward (True) or reverse (False)
    :param dir_deg: 
        Movement right (>0) or straight (=0) or left (<0)
    """
    global rover
    if rover is None:
        return
    if rover.LED_Device is None:
        return
    if fwd:
        # Set all LEDs
        rover.setPixel(1, LED_WHITE)
        rover.setPixel(2, LED_WHITE)
        rover.setPixel(0, LED_RED_H)
        rover.setPixel(3, LED_RED_H)
        rover.show()

        # Blink forward-right LED
        if dir_deg > 0:  # right
            flash_led_async(2, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(2, LED_WHITE)
            rover.show()
        # Blink forward-left LED
        elif dir_deg < 0:  # left
            flash_led_async(1, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(1, LED_WHITE)
            rover.show()

    else:
        # Set all LEDs
        rover.setPixel(1, LED_WHITE_H)
        rover.setPixel(2, LED_WHITE_H)
        rover.setPixel(0, LED_RED)
        rover.setPixel(3, LED_RED)
        rover.show()

        # Blink back-right LED
        if dir_deg > 0:  # right
            flash_led_async(3, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(3, LED_RED)
            rover.show()

        # Blink back-left LED
        elif dir_deg < 0:  # left
            flash_led_async(0, 2, 0.5, LED_RED, LED_BLACK)
            rover.setPixel(0, LED_RED)
            rover.show()

    await asyncio.sleep(0)

    
#
# Internal Joystick controlls mixers functions
#
def _mixer_speed(
    yaw: float = 0.0,
    throttle: float = 0.0,
    max_speed: int = 100
) -> tuple[float, float]:
    """
    Mix a pair of controller axes, returning a pair of wheel speeds. 
    This is where the mapping from controller positions to wheel powers is defined.

    :param yaw: 
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle: 
        Throttle axis value, ranges from -1.0 to 1.0
    :param max_speed: 
        Maximum speed that should be returned from the mixer
        defaults to 100.0 (percentage of max speed)
    :return: 
        When yaw <> 0: a pair of power_left, power_right values 
        to send to the left and right motor drivers
        Else: a single power  value to send to both motor drivers
    """
    if yaw == 0.0:
        scale = float(max_speed) / max(1, abs(throttle))
        return throttle * scale, 0

    left = throttle + yaw
    right = throttle - yaw
    scale = float(max_speed) / max(1, abs(left), abs(right))
    return left * scale, right * scale


def _mixer_dir(
    l_r: float = 0.0,
    f_b: float = 0.0,
    max_dir: float = 65.0
) -> float:
    """
    Mix a pair of controller axes, returning a direction/angle. 
    This is where the mapping from controller positions to wheel direction is defined.

    :param l_r: 
        Left-right axis value, ranges from -1.0 to +1.0
    :param f_b: 
        Fwd-back axis value, ranges from -1.0 to +1.0
    :param max_dir: 
        Maximum direction that should be returned from the mixer
        defaults to 45 (degrees)
    :return: 
        A direction value to send to the motor drivers (degrees)
    """
    global dir_filter 
    angle_rel = (2/pi)*atan2(l_r, abs(f_b))
    scale = float(max_dir) / max(1, abs(angle_rel))
    # print(f"angle_deg={angle_rel*scale}")
    if len(dir_filter) >= DIR_FILTER_LNG:
        dir_filter.pop(0)
    dir_filter.append(angle_rel * scale)
    return sum(dir_filter)/len(dir_filter)


def _calc_ackermann_steering(
    dir_deg: float = 0,
    speed_per: float = 20
) -> tuple[int, int, int, int]:
    """
    Calculate Ackermann rover steering.
    Left and Right motors can be set to different speeds and angles 
    according to Ackermann steering geometry. 
    See https://www.mathworks.com/help/sm/ug/mars_rover.html
    NOTE: Due to the 4tronix circuit design of the Main Board 
    all three wheels on the same side of the rover are set to the same speed!

    The max steering angle is limited to the value allowed by the rover chassis width
    i.e. the turn radius must be larger than the half of the chassis width (D).
    We choose to limit the minimum turn radius to 0.6 of the chassis width, 
    i.e. a bicycle steering angle of max atan2(L/2, 0.6*D) = 38.73 deg
    This limits to max 78.26 deg the (higher) angle of the inner wheels

    :param dir_deg: 
        Direction angle value (bicycle steering angle of the rover)
        ranges from -90.0 to +90.0 (degrees)
    :param speed_per: 
        Speed value (chassis speed of the rover)
        ranges from -100.0 to 100.0 (percentage of max speed)
    :return:
        A tuple with calculated dir_left, dir_right, speed_left, speed_right
    """
    dir_rad = (pi/180.0) * dir_deg
    if dir_deg != 0.0:
        dir_rad = min(abs(dir_rad), atan2(1.0, 1.2*ROVER_DoL))
        dir_up_scale = atan2(1.0, (1.0/tan(dir_rad) - ROVER_DoL))
        dir_down_scale = atan2(1.0, (1.0/tan(dir_rad) + ROVER_DoL))

    # Limit the (higher) speed of the outer wheels to 100 (=max PWM duty cycle value, see rover.py)
    speed_up_scale = 1.0
    speed_down_scale = 1.0
    if speed_per != 0.0:
        speed_up_scale = sqrt(
            tan(dir_rad)**2 + (1 + ROVER_DoL*tan(dir_rad))**2)
        speed_down_scale = sqrt(
            tan(dir_rad)**2 + (1 - ROVER_DoL*tan(dir_rad))**2)
        if speed_up_scale > 100/speed_per:
            speed_per = 100/speed_up_scale

    if dir_deg > 0:
        dir_left = int((180.0/pi) * dir_down_scale)
        dir_right = int((180.0/pi) * dir_up_scale)
        speed_left = int(speed_per * speed_up_scale)
        speed_right = int(speed_per * speed_down_scale)
    elif dir_deg < 0:
        dir_left = int((-180.0/pi) * dir_up_scale)
        dir_right = int((-180.0/pi) * dir_down_scale)
        speed_left = int(speed_per * speed_down_scale)
        speed_right = int(speed_per * speed_up_scale)
    else:
        dir_left = 0
        dir_right = 0
        speed_left = int(speed_per)
        speed_right = int(speed_per)

    return dir_left, dir_right, speed_left, speed_right


#
# Internal rover drive functions
#
def _move_rover(
    dir_deg: float = 0,
    speed_per: float = 20
) -> None:
    """
    Set simple rover steering: direction (left or right) and speed (forward or reverse).
    All motors set to the same speed.

    :param dir_deg: 
        Direction angle value
        ranges from -90.0 to +90.0 (degrees)
        A None value keeps unchnaged the current direction
    :param speed_per: 
        Speed value
        ranges from -100.0 to 100.0 (percentage of max speed)
    """
    global rover

    if dir_deg is not None:
        rover.setServoFrontLeft(dir_deg)
        rover.setServoFrontRight(dir_deg)
        rover.setServoRearLeft(-1*dir_deg)
        rover.setServoRearRight(-1*dir_deg)

    if speed_per == 0:
        # Coast to stop
        rover.stop()

        if not USE_ASYNC:
            # Set all LED to red
            flash_all_leds(1, 0.1, LED_RED_H)

    elif speed_per > 0:
        # Move forward
        rover.forward(abs(int(speed_per)))

        # Set forward-back left-right LED
        #set_rlfb_led(True, dir_deg)

    elif speed_per < 0:
        # Move backward
        rover.reverse(abs(int(speed_per)))

        # Set forward-back left-right LED
        #set_rlfb_led(False, dir_deg)

def _move_rover_ackermann(
    dir_deg: float = 0,
    speed_per: float = 20
) -> None:
    """
    Set Ackermann rover steering: direction (left or right) and speed (forward or reverse).
    Left and Right motors can be set to different speeds and angles 
    according to Ackermann steering geometry. 
    See https://www.mathworks.com/help/sm/ug/mars_rover.html
    NOTE: Due to the 4tronix design choice for the Main Board 
    all three wheels on the same side of the rover are set to the same speed!

    :param dir_deg: 
        Direction angle value (steering angle of the rover)
        ranges from -90.0 to +90.0 (degrees)
        A None value keeps unchanged the current direction
    :param speed_per: 
        Speed value (speed of the rover) 
        ranges from -100.0 to 100.0 (percentage of max speed)
    """
    global prev_dir
    global rover

    # Calculate the Ackermann steering parameters
    if dir_deg is not None:
        dir_left, dir_right, speed_left, speed_right = _calc_ackermann_steering(
            dir_deg, speed_per)
        prev_dir = dir_deg
    else:
        # Use the last direction value
        dir_deg = prev_dir
        dir_left, dir_right, speed_left, speed_right = _calc_ackermann_steering(
            dir_deg, speed_per)

    # Apply new steering angles
    rover.setServoFrontLeft(dir_left)
    rover.setServoFrontRight(dir_right)
    rover.setServoRearLeft(-1*dir_left)
    rover.setServoRearRight(-1*dir_right)

    if speed_per == 0:
        # Coast to stop
        rover.stop()

        speed_left = 0
        speed_right = 0

        if not USE_ASYNC:
            # Set all LED to red
            flash_all_leds(1, 0.1, LED_RED_H)

    elif speed_per > 0:
        # Move forward
        rover.turnForward(speed_left, speed_right)

        if not USE_ASYNC:
            # Set front-back left-right LEDs
            set_rlfb_led(True, dir_deg)

    elif speed_per < 0:
        # Move backward
        rover.turnReverse(speed_left, speed_right)

        if not USE_ASYNC:
            # Set front-back left-right LEDs
            set_rlfb_led(False, dir_deg)

#
# Internal rover mast control functions
#
def _move_mast(p_deg: float = None, t_deg: float = None) -> None:
    """
    Moves the pan or pan&tilt mast.

    :param p_deg: 
        Paning (horizontal) angle value of the mast
        ranges from -90.0 to +90.0 (degrees)
        A None value keeps unchanged the current direction
    :param t_deg: 
        Tilt (vertical) angle value of the mast
        ranges from -90.0 to +90.0 (degrees)
        A None value keeps unchanged the current direction       
    """
    global rover

    if p_deg is not None:
        rover.setServoMastPan(p_deg)
    if t_deg is not None:
        rover.setServoMastTilt(t_deg)