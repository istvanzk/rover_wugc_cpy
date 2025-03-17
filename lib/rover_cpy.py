# -*- coding: utf-8 -*-
# CircuitPython class implementation for the 4tronix M.A.R.S. Rover Robot related functions and controls. 
#
# Copyright 2025 Istvan Z. Kovacs. All Rights Reserved.
#
# Version: 1.0.2
#
# For maximum backwards compatibility with the original rover.py implementation provided by 4tronix, 
# almost all the function definitions in this class are kept identical.
# This class also implements the original pca9685.py functionalities.
# Built for CircuitPython 9.2.4 or later (February 2025)
# See https://circuitpython.org/board/challenger_rp2350_wifi6_ble5/
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
import board
import digitalio
import pwmio
import busio
import gc
from os import getenv
from traceback import print_exception

# https://docs.circuitpython.org/projects/busdevice/en/stable/
from adafruit_bus_device.i2c_device import I2CDevice

# https://docs.circuitpython.org/projects/pca9685/en/stable/index.html
# https://docs.circuitpython.org/projects/motor/en/stable/examples.html#motor-servo-sweep
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# https://docs.circuitpython.org/projects/hcsr04/en/stable/
from adafruit_hcsr04 import HCSR04

# https://docs.circuitpython.org/projects/neopixel/en/stable/
import neopixel

VERSION = "1.0.2"

###################### Parameters START ####################
# All values are read from the settings.toml if they exist.

# Define accessories to be enabled
# Corresponding GPIOs for SONAR, IRSENSORS and KEYPAD are configured below.
USE_MAST_PAN  = getenv('USE_MAST_PAN', '0') == 1
USE_MAST_TILT = getenv('USE_MAST_TILT', '0') == 1
USE_SONAR     = getenv('USE_MAST_SONAR', '0') == 1
USE_IRSENSORS = getenv('USE_IRSENSORS', '0') == 1
USE_KEYPAD    = getenv('USE_KEYPAD', '0') == 1

# Define the servo numbers (see MARS rover main board connectors)
SERVO_FL = getenv('SERVO_FL', '9')
SERVO_RL = getenv('SERVO_RL', '11')
SERVO_FR = getenv('SERVO_FR', '15')
SERVO_RR = getenv('SERVO_RR', '13')
SERVO_MP = getenv('SERVO_MP', '7')
SERVO_MT = getenv('SERVO_MT', '6')

# Define PWM pins used to control the Left/Right DC motors (via DRV8833)
# when using the Challenger+ RP2350 WiFi6/BLE5
# https://ilabs.se/product/challenger-rp2350-wifi-ble/ development board.
PWML1_Pin = eval(f"board.GP{getenv('PWML1_GPIO', '2')}")
PWML2_Pin = eval(f"board.GP{getenv('PWML2_GPIO', '24')}")
PWMR1_Pin = eval(f"board.GP{getenv('PWMR1_GPIO', '3')}")
PWMR2_Pin = eval(f"board.GP{getenv('PWMR2_GPIO', '25')}")

# Define RGB LEDs Pin
LED_Pin = eval(f"board.GP{getenv('LED_GPIO', '7')}")

# Optional pin definitions for devices controlled via 4 GPIO pins
# when using the Challenger+ RP2350 WiFi6/BLE5
# https://ilabs.se/product/challenger-rp2350-wifi-ble/ development board: GPIO26, GPIO27, GPIO28 and GPIO29
# These 4 GPIOs are routed on the M.A.R.S. Rover main board to the IO marked with #23, #24, #25 and #05, respectively.
# Note that not all these 3 devices can be used simultaneously with these 4 GPIOs.
# The 3 devices are enabled/disabled by setting the USE_* parameters above.

# Define ultrasonic sonar Pin (same pin for both Ping and Echo)
SONAR_Pin = None
if USE_SONAR:
    SONAR_Pin = eval(f"board.GP{getenv('SONAR_GPIO')}") # GP26

# Define IR Sensors Pins
IRFL_Pin = None
IRFR_Pin = None
IRLL_Pin = None
IRLR_Pin = None
if USE_IRSENSORS:
    IRFL_Pin = eval(f"board.GP{getenv('IRFL_GPIO')}") # GP26
    IRFR_Pin = eval(f"board.GP{getenv('IRFR_GPIO')}") # GP27
    IRLL_Pin = eval(f"board.GP{getenv('IRLL_GPIO')}") # GP28
    IRLR_Pin = eval(f"board.GP{getenv('IRLR_GPIO')}") # GP29


# Define Keypad Pins
KEYPADIn_Pin  = None
KEYPADOut_Pin = None
if USE_KEYPAD:
    KEYPADIn_Pin  = eval(f"board.GP{getenv('KEYPADIN_GPIO')}")  # GP28
    KEYPADOut_Pin = eval(f"board.GP{getenv('KEYPADOUT_GPIO')}") # GP29

if SONAR_Pin is None:
    USE_SONAR = False
if IRFL_Pin is None or IRFR_Pin is None or IRLL_Pin is None or IRLR_Pin is None:
    USE_IRSENSORS = False
if KEYPADIn_Pin is None or KEYPADOut_Pin is None:
    USE_KEYPAD = False

###################### Parameters END ######################


class RoverClass:
    """ 
    Class for 4tronix M.A.R.S. Rover Robot related functions and controls. 

    For maximum backwards compatibility with the original rover.py implementation provided by 4tronix, 
    almost all the function names in this class are kept identical.
    This class also implements the original pca9685.py functionalities.

    Usage:
        from rover_cpy import RoverClass
        rover = RoverClass()
        rover.init(brightness=0.3)
        rover.forward(50)
        ...
        rover.stop()
        ...
        rover.cleanup()
    
    """

    def __init__(self):
        """ Internal initializations. """

        # Version string
        self.version = VERSION

        # Initialization status
        self.InitializedControls = False
        self.InitializedDevices = False
        self.I2Cbus = None
        self.EEPROM_OffsetValues = [0]*16
        self.PCA9685_Device = None
        self._servos = 16*[None]
        self.LED_Device = None
        self.SONAR_Device = None
        self.irFL = None
        self.irFR = None
        self.lineLeft = None
        self.lineRight = None
        self.KEYPADOut = None
        self.KEYPADIn = None

        # PWM controls for the Left/Right DC motors (via DRV8833)
        # The L1-R1 and L2-R2 pairs are on the same PWM slices, 1 and 5, respectively, and share the clock frequency
        self._lDir = 0
        self._rDir = 0
        self._pwmL1 = None
        self._pwmR1 = None
        self._pwmL2 = None
        self._pwmR2 = None
        try:
            self._pwmL1 = pwmio.PWMOut(PWML1_Pin, duty_cycle=0, frequency=30) #, variable_frequency=True)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No PWM L1 output initialized! Cannot control the Rover without 4 PWMs.")
        try:
            self._pwmL2 = pwmio.PWMOut(PWML2_Pin, duty_cycle=0, frequency=30) #, variable_frequency=True)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No PWM L2 output initialized! Cannot control the Rover without 4 PWMs.")
        try:
            self._pwmR1 = pwmio.PWMOut(PWMR1_Pin, duty_cycle=0, frequency=30)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No PWM R1 output initialized! Cannot control the Rover without 4 PWMs.")
        try:
            self._pwmR2 = pwmio.PWMOut(PWMR2_Pin, duty_cycle=0, frequency=30)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No PWM R2 output initialized! Cannot control the Rover without 4 PWMs.")
       
        # Initialize the I2C bus
        try:
            self.I2Cbus = busio.I2C(board.SCL, board.SDA) # (board.GP21, board.GP20)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No I2C bus detected! Cannot control the Rover without I2C.")

        # EEPROM I2C device
        try:
            self.EEPROM_Device = I2CDevice(self.I2Cbus, 0x50)
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No EEPROM (I2C) initialized! Cannot control the Rover without EEPROM.")

        # PCA9685 I2C device (for Servos)
        try:
            self.PCA9685_Device = PCA9685(self.I2Cbus, address=0x40)
            # Frequency corresponds to the prescaler value of 101 set in regiser 0xFE
            self.PCA9685_Device.frequency = 60
        except Exception as exc:
            self._clean_up_raise_with_msg(exc, "No PCA9685 (I2C) initialized! Cannot control the Rover without PCA9685.")

        # Servos (controlled via PCA9685)
        for _s in range(len(self._servos)):
            try:
                self._servos[_s] = servo.Servo(self.PCA9685_Device.channels[_s])
                self._servos[_s].angle = 90
            except Exception as exc:
                self._clean_up_raise_with_msg(exc, f"Servo on PCA9685 channel #{_s} not initialized! Cannot control the Rover without Servos.")

        # LED pixels
        # NOTE: The self.LED_Device is initialized in the init() function to maintain backwards compatibility with thr original rover.py code
        self.LED_numPixels = 4
        self.LED_brightness = 0

        # Sonar device
        if USE_SONAR and SONAR_Pin:
            try:
                self.SONAR_Device = HCSR04(trigger_pin=SONAR_Pin, echo_pin=SONAR_Pin)
            except Exception as exc:
                #print_exception(exc)
                print("No SONAR (HCSR04) initialized! SONAR use will be disabled.")
                pass

        # IR sensor device(s)
        # Comment out the ones not used!
        if USE_IRSENSORS:
            if IRFL_Pin:
                try:
                    self.irFL = digitalio.DigitalInOut(IRFL_Pin)
                    self.irFL.direction = digitalio.Direction.INPUT
                except Exception as exc:
                    #print_exception(exc)
                    print(f"No IRSENSOR GPIO{IRFL_Pin} initialized! IRFL use will be disabled.")
                    pass
            if IRFR_Pin:
                try:
                    self.irFR = digitalio.DigitalInOut(IRFR_Pin)
                    self.irFR.direction = digitalio.Direction.INPUT
                except Exception as exc:
                    #print_exception(exc)
                    print(f"No IRSENSOR GPIO{IRFR_Pin} initialized! IRFR use will be disabled.")
                    pass
            if IRLL_Pin:
                try:
                    self.lineLeft = digitalio.DigitalInOut(IRLL_Pin)
                    self.lineLeft.direction = digitalio.Direction.INPUT
                except Exception as exc:
                    #print_exception(exc)
                    print(f"No IRSENSOR GPIO{IRLL_Pin} initialized! IRLL use will be disabled.")
                    pass
            if IRLR_Pin:
                try:
                    self.lineRight = digitalio.DigitalInOut(IRLR_Pin)
                    self.lineRight.direction = digitalio.Direction.INPUT
                except Exception as exc:
                    #print_exception(exc)
                    print(f"No IRSENSOR GPIO{IRLR_Pin} initialized! IRLR use will be disabled.")
                    pass

        # Initialize Keypad device
        if USE_KEYPAD and KEYPADOut_Pin and KEYPADIn_Pin:
            try:
                self.KEYPADOut = digitalio.DigitalInOut(KEYPADOut_Pin)
                self.KEYPADIn  = digitalio.DigitalInOut(KEYPADIn_Pin)
                self.KEYPADOut.direction = digitalio.Direction.OUTPUT
                self.KEYPADIn.direction  = digitalio.Direction.INPUT
            except Exception as exc:
                #print_exception(exc)
                print(f"No KEYPAD GPIO{KEYPADOut_Pin} and GPIO{KEYPADIn_Pin} initialized! KEYPAD use will be disabled.")
                pass
        
        self.InitializedDevices = True

    def __del__(self):
        """
        Perfom custom clean-up and garbage collection.
        """
        self.cleanup()

    def __getattr__(self, item: str) -> any:
        """
        Property short-cut access for certain attribute values.

        :param item:
            attribute name
        :return:
            The attribute value or AttributeError if property access for item is not implemented
        """
        if item == 'offsets':
            self.loadOffsets()
            return self.EEPROM_OffsetValues
        elif item == 'brightness':
            return self.LED_brightness
        raise AttributeError

    def __repr__(self):
        return 'CircuitPython class for the 4tronix M.A.R.S. Rover Robot related functions and controls.'


    #
    # General Functions
    #
    def init(self, brightness: float = 0.0) -> None:
        """ 
        Initialize the rover controls. 
        
        :param brightness: 
            Brightness of the RGB LEDs (0.0-1.0)
            When 0, the LEDs are not initialized and cannot be used subsequently.
        :return: 
            None
        """
        if self.InitializedDevices and not self.InitializedControls:

            # Initialize LEDs (possible only once after each reboot!)
            if self.LED_Device is None:
                if (brightness >= 0.1 and brightness <= 1.0):
                    self.LED_brightness = brightness
                    try:
                        self.LED_Device = neopixel.NeoPixel(
                            LED_Pin, 
                            self.LED_numPixels, 
                            brightness=brightness, 
                            auto_write=False, 
                            pixel_order=neopixel.GRB)
                        self.clear()
                        self.show()
                    except Exception as exc:
                        #print_exception(exc)
                        print("No LED (neopixel) initialized! LED use will be disabled.")
                        pass

            # Load stored Stpper Motor offsets
            # Initialize all Servo motors control
            self.initServos()
            
            if USE_MAST_PAN:
                # The Servo motor control has been initialized already with initServos()
                pass
            
            if USE_MAST_TILT:
                # The Servo motor control has been initialized already with initServos()
                pass

            # Initialize Sonar sensor
            if USE_SONAR:
                pass

            # Initialize IR sensors
            if USE_IRSENSORS:
                pass

            # Initialize Keypad control
            if USE_KEYPAD:
                pass

        # Initialization status
        self.InitializedControls = True


    def cleanup(self):
        """ Clean-up and close. """
        self.brake()
        time.sleep(0.2)
        print('Cleanup start.')
        if self._pwmL1:
            self._pwmL1.deinit()
        if self._pwmR1:
            self._pwmR1.deinit()
        if self._pwmL2:
            self._pwmL2.deinit()
        if self._pwmR2:
            self._pwmR2.deinit()
        if self.PCA9685_Device:
            self.PCA9685_Device.deinit()
            self.I2Cbus.deinit()
        if self.SONAR_Device:
            self.SONAR_Device.deinit()
        if self.irFL:
            self.irFL.deinit()
        if self.irFR:
            self.irFR.deinit()
        if self.lineLeft:
            self.lineLeft.deinit()
        if self.lineRight:
            self.lineRight.deinit()
        if self.KEYPADOut:
            self.KEYPADOut.deinit()
        if self.KEYPADIn:
            self.KEYPADIn.deinit()
        if self.LED_Device:
            # Insert LED animation
            self.clear()
            self.show()
            self.LED_Device.deinit()
        time.sleep(0.2)
        self.InitializedDevices = False
        self.InitializedControls = False
        gc.collect()
        print('Cleanup done.')

    def _clean_up_raise_with_msg(self, exc: Exception, msg: str = None):
        """ Display exception info, cleanup and then raise a RuntimeError with the custom error message. """
        self.cleanup()
        print_exception(exc)
        raise RuntimeError(msg)

    #
    # Motor Functions
    #
    def stop(self):
        """ Stops both motors - coasts slowly to a stop. """
        self._lDir = 0
        self._rDir = 0
        self._pwmL1.duty_cycle = 0
        self._pwmR1.duty_cycle = 0
        self._pwmL2.duty_cycle = 0
        self._pwmR2.duty_cycle = 0
        self.stopServos()

    def brake(self):
        """ Stops both motors - regenerative braking to stop quickly. """
        self._lDir = 0
        self._rDir = 0
        if self._pwmL1 and self._pwmR1 and self._pwmL2 and self._pwmR2:
            self._pwmL1.duty_cycle = 65535
            self._pwmR1.duty_cycle = 65535
            self._pwmL2.duty_cycle = 65535
            self._pwmR2.duty_cycle = 65535

    def forward(self, speed: int) -> None:
        """ 
        Sets both left and right motors to move forward at speed. 
        
        :param speed:
            Speed of the motors (0-100)
        :return:
            None
        """
        if self._lDir == -1 or self._rDir == -1:
            self.brake()
            time.sleep(0.2)
        _speed = min(speed, 100)
        _speed = max(_speed, 0)
        self._pwmL1.duty_cycle = int(65535*_speed/100)
        self._pwmL2.duty_cycle = 0   
        self._pwmR1.duty_cycle = int(65535*_speed/100)
        self._pwmR2.duty_cycle = 0  
        #self._pwmL1.frequency(max(_speed/2, 10))
        #self._pwmR1.frequency(max(_speed/2, 10))
        self._lDir = 1
        self._rDir = 1

    def reverse(self, speed: int) -> None:
        """ 
        Sets both left and right motors to reverse at speed. 
        
        :param speed:
            Speed of the motors (0-100)
        :return:
            None
        """
        if self._lDir == 1 or self._rDir == 1:
            self.brake()
            time.sleep(0.2)
        _speed = min(speed, 100)
        _speed = max(_speed, 0)
        self._pwmL1.duty_cycle = 0
        self._pwmL2.duty_cycle = int(65535*_speed/100)  
        self._pwmR1.duty_cycle = 0
        self._pwmR2.duty_cycle = int(65535*_speed/100)  
        #self._pwmL2.frequency(max(_speed/2, 10))
        #self._pwmR2.frequency(max(_speed/2, 10))
        self._lDir = -1
        self._rDir = -1

    def spinLeft(self, speed: int) -> None:
        """ 
        Sets left and right motors to turn opposite directions at speed.

        :param speed:
            Speed of the motors (0-100)
        :return:
            None
        """
        if self._lDir == 1 or self._rDir == -1:
            self.brake()
            time.sleep(0.2)
        _speed = min(speed, 100)
        _speed = max(_speed, 0)
        self._pwmL1.duty_cycle = 0
        self._pwmL2.duty_cycle = int(65535*_speed/100)  
        self._pwmR1.duty_cycle = int(65535*_speed/100)
        self._pwmR2.duty_cycle = 0  
        #self._pwmL2.frequency(min(_speed+5, 20))
        #self._pwmR1.frequency(min(_speed+5, 10))
        self._lDir = -1
        self._rDir = 1

    def spinRight(self, speed: int) -> None:
        """
        Sets left and right motors to turn opposite directions at speed.

        :param speed:
            Speed of the motors (0-100)
        :return:
            None
        """
        if self._lDir == -1 or self._rDir == 1:
            self.brake()
            time.sleep(0.2)
        _speed = min(speed, 100)
        _speed = max(_speed, 0)
        self._pwmL1.duty_cycle = int(65535*_speed/100)
        self._pwmL2.duty_cycle = 0  
        self._pwmR1.duty_cycle = 0
        self._pwmR2.duty_cycle = int(65535*_speed/100)
        #self._pwmL1.frequency(min(_speed+5, 20))
        #self._pwmR2.frequency(min(_speed+5, 10))
        self._lDir = 1
        self._rDir = -1

    def turnForward(
            self, 
            leftSpeed: int, 
            rightSpeed: int
    ) -> None:
        """ 
        Moves forwards in an arc by setting different speeds for left and right motors. 
        
        :param leftSpeed:   
            Speed of the left motor (0-100)
        :param rightSpeed:  
            Speed of the right motor (0-100)
        :return:
            None
        """
        if self._lDir == -1 or self._rDir == -1:
            self.brake()
            time.sleep(0.2)
        _speed_L = min(leftSpeed, 100)
        _speed_L = max(_speed_L, 0)
        _speed_R = min(rightSpeed, 100)
        _speed_R = max(_speed_R, 0)
        self._pwmL1.duty_cycle = int(65535*_speed_L/100)
        self._pwmL2.duty_cycle = 0   
        self._pwmR1.duty_cycle = int(65535*_speed_R/100)
        self._pwmR2.duty_cycle = 0  
        #self._pwmL1.frequency(min(_speed_L+5, 20))
        #self._pwmR1.frequency(min(_speed_R+5, 20))
        self._lDir = 1
        self._rDir = 1

    def turnReverse(
        self, 
        leftSpeed: int, 
        rightSpeed: int
    ) -> None:
        """
        Moves backwards in an arc by setting different speeds for left and right motors.
        0 <= leftSpeed,rightSpeed <= 100. 
        
        :param leftSpeed:
            Speed of the left motor (0-100)
        :param rightSpeed:  
            Speed of the right motor (0-100)
        :return:
            None
        """
        if self._lDir == 1 or self._rDir == 1:
            self.brake()
            time.sleep(0.2)
        _speed_L = min(leftSpeed, 100)
        _speed_L = max(_speed_L, 0)
        _speed_R = min(rightSpeed, 100)
        _speed_R = max(_speed_R, 0)
        self._pwmL1.duty_cycle = 0
        self._pwmL2.duty_cycle = int(65535*_speed_L/100)
        self._pwmR1.duty_cycle = 0
        self._pwmR2.duty_cycle = int(65535*_speed_R/100)  
        #self._pwmL2.frequency(min(_speed_L+5, 20))
        #self._pwmR2.frequency(min(_speed_R+5, 20))
        self._lDir = -1
        self._rDir = -1


    #
    # EEPROM Functions
    # First 16 bytes are used for 16 servo offsets (signed bytes)
    #
    def _rdEEROM(self, address: int) -> int:
        """ Low level read function. Reads 1 byte data from address. """
        address_to_read = bytearray([(address >> 8) & 0xFF, address & 0xFF])
        result = bytearray(1)
        with self.EEPROM_Device:
            self.EEPROM_Device.write_then_readinto(address_to_read, result)
            res = ((result[0] + 0x80) & 0xff) - 0x80  # sign extend
        return res

    def _wrEEROM(self, address: int, data: int) -> None:
        """ Low level write function. Writes 1 byte Data to address. """
        data_to_write = bytearray([(address >> 8) & 0xFF, address & 0xFF] + list(data))
        with self.EEPROM_Device:
            self.EEPROM_Device.write(data_to_write)
        time.sleep(0.01)

    def loadOffsets(self):
        """ Load all Servo offset values. """
        for idx in range(len(self.EEPROM_OffsetValues)):
            self.EEPROM_OffsetValues[idx] =  self._rdEEROM(idx)

    def saveOffsets(self):
        """ Save all Servo offsets values. """
        for idx in range(len(self.EEPROM_OffsetValues)):
            self._wrEEROM(idx,  self.EEPROM_OffsetValues[idx])

    def readEEROM(self, address: int) -> int:
        """ General Read Function. Ignores first Servo offset bytes. """
        return self._rdEEROM(address + len(self.EEPROM_OffsetValues))

    def writeEEROM(self, address, data: int) -> None:
        """ General Write Function. Ignores first Servo offset bytes. """
        self._wrEEROM(address + len(self.EEPROM_OffsetValues), data)

    #
    # Servo Functions
    # 
    def initServos(self):
        """ Initialize to 90 degree all servos and apply offset values. """
        self.loadOffsets()
        for _s in range(len(self._servos)):
            if self._servos[_s] is not None:
                self._servos[_s].angle = 90 + self.EEPROM_OffsetValues[_s]

    def setServo(self, Servo: int, Degrees: float) -> None:
        """ Set the specified Servo to the specified angle Degree. """

        # Change degrees to a value between 0 (-85) to 180 (+90)
        if (
            self._servos[Servo] is not None 
            and (Servo>=0) and (Servo<len(self._servos)) 
            and (Degrees>= -85) and (Degrees<=90)
        ):
            self._servos[Servo].angle = (Degrees+90) + self.EEPROM_OffsetValues[Servo]

    def stopServos(self):
        """ Stop all servos. Backwards compatibility shim. """
        self.initServos()

    def setServoFrontLeft(self, Degrees: float) -> None:
        """ Set the Front-Left Servo to the specified angle Degree. """
        self.setServo(SERVO_FL, Degrees)
        
    def setServoFrontRight(self, Degrees: float) -> None:
        """ Set the Front-Right Servo to the specified angle Degree. """
        self.setServo(SERVO_FR, Degrees)

    def setServoRearLeft(self, Degrees: float) -> None:
        """ Set the Rear-Left Servo to the specified angle Degree. """
        self.setServo(SERVO_RL, Degrees)

    def setServoRearRight(self, Degrees: float) -> None:
        """ Set the Rear-Right Servo to the specified angle Degree. """
        self.setServo(SERVO_RR, Degrees)

    def setServoMastPan(self, Degrees: float) -> None:
        """ Set the Mast Azimuth/Pan Servo to the specified angle Degree. """
        if USE_MAST_PAN:
            self.setServo(SERVO_MP, Degrees)

    def setServoMastTilt(self, Degrees: float) -> None:
        """ Set the Mast Elevation/Tilt Servo to the specified angle Degree. """
        if USE_MAST_TILT:
            self.setServo(SERVO_MT, Degrees)

    #
    # RGB LED (Pixel) Functions
    #
    def setColor(self, color: tuple) -> None:
        """ Set all LED pixels  to specified color. """
        if self.LED_Device:
            for i in range(self.LED_numPixels):
                self.setPixel(i, color)
            self.LED_Device.show()

    def setPixel(self, ID: int, color: tuple) -> None:
        """ Set specified LED pixel index (ID) to specified color. """
        if self.LED_Device:
            if ID >= 0 and ID < self.LED_numPixels:
                self.LED_Device[ID] = color

    def showPixel(self, ID: int, color: tuple) -> None:
        """ Set & show specified LED pixel index (ID) to specified color. """
        if self.LED_Device:
            if ID >= 0 and ID < self.LED_numPixels:
                self.LED_Device[ID] = color
                self.LED_Device.show()

    def show(self):
        """ Show the current LED pixels. """
        if self.LED_Device:
            self.LED_Device.show()

    def clear(self):
        """ Clear/turn off all LED pixels. """
        if self.LED_Device:
            for i in range(self.LED_numPixels):
                self.setPixel(i, (0, 0, 0))
            self.LED_Device.show()

    def rainbow(self):
        """ Sets the LEDs to rainbow colors. """
        if self.LED_Device:
            for i in range(self.LED_numPixels):
                self.setPixel(i, self._wheel(i * 256 // self.LED_numPixels))
            self.LED_Device.show()

    def _fromRGB(self, red:int, green:int, blue:int) -> tuple:
        """ Creates a color tuple value from R, G and B values. """
        return (red, green, blue)

    def _toRGB(self, color: tuple) -> tuple:
        """ Converts a color value to separate R, G and B. """
        return color

    def _wheel(self, pos: int) -> tuple:
        """ Generates rainbow colors across 0-255 positions. """
        if pos < 85:
            return self._fromRGB(255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return self._fromRGB(0, 255 - pos * 3, pos * 3)
        else:
            pos -= 170
            return self._fromRGB(pos * 3, 0, 255 - pos * 3)


    #
    # IR Sensors Functions
    # 
    def irLeft(self):
        """ Returns state of Left IR Obstacle sensor. """
        if self.irFL is not None and not self.irFL.value:
            return True
        else:
            return False

    def irRight(self):
        """ Returns state of Right IR Obstacle sensor. """
        if self.irFR is not None and not self.irFR.value:
            return True
        else:
            return False

    def irAll(self):
        """ Returns true if either of the Obstacle sensors are triggered. """
        if (
            self.irFL is not None
            and self.irFR is not None
            and (not self.irFL.value or not self.irFR.value)
        ):
            return True
        else:
            return False

    def irLeftLine(self):
        """ Returns state of Left IR Line sensor. """
        if self.lineLeft is not None and not self.lineLeft.value:
            return True
        else:
            return False

    def irRightLine(self):
        """ Returns state of Right IR Line sensor. """
        if self.lineRight is not None and not self.lineRight.value:
            return True
        else:
            return False

    #
    # Ultrasonic Sensor Functions
    #
    def getDistance(self):
        distance = 0
        if self.SONAR_Device is not None:
            try:
                distance = self.SONAR_Device.distance
            except RuntimeError:
                distance = 0
        return distance


    #
    # Keypad Functions
    #
    def getKey(self):
        keys = 0
        if (self.KEYPADOut is not None
            and self.KEYPADIn is not None
        ):
            count = 0
            self.KEYPADOut.value = False
            while keys == 0:
                time.sleep(0.00001)
                while self.KEYPADIn.value:
                    count += 1
                    if count > 1000:
                        count = 0
                        time.sleep(0.001)
                while not self.KEYPADIn.value:
                    pass
                for index in range(16):
                    self.KEYPADOut.value = False
                    keys = (keys << 1) + self.KEYPADIn.value
                    self.KEYPADOut.value = True
                keys = 65535 - keys
        return keys

    #
    # Wheel Sensor Functions
    # ???


