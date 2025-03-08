# -*- coding: utf-8 -*-
# CircuitPython class implementation for the PiHut Wireless USB Game Controller
#
# Copyright 2025 Istvan Z. Kovacs. All Rights Reserved.
#
# Version: 1.0.0
#
# The PiHut Wireless USB Game Controller can be switched between 3 different operating 'modes' 
# by using a key press combination of the Analog button and the Right Stick (see below). 
# The description below uses the PiHut button snames as listed for the 
# Approximate Engineering (https://approxeng.github.io/approxeng.input/simpleusage.html#standard-names) 
# implementation. Some parts of this implementation are based on the
# src/python/approxeng/input/__init__.py file of the Approximate Engineering library.
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

import array
from time import sleep, monotonic
import board
import usb_host
import usb.core
import gc
#from traceback import print_exception

VERSION = "1.0.0"

# For the PiHut controller only!
NUM_REPORT_BYTES = 15
IDVENDOR  = 0x2563
IDPRODUCT = [0x0575, 0x0526]

class PiHutWUSBGameController:

    def __init__(self, operating_mode: int=0, usb_dp = board.GP12, usb_dn = board.GP13):

        # Version string
        self.version = VERSION

        # Initialize internal parameters
        self.device = None
        self.repbuf = None
        self.cmdmasks = None
        self.idVendor = None
        self.idProduct = None
        self.connected = False
        self.operatingmode = -1
        self.targetmode = operating_mode
        self._init_cmdmasks_fnc = None
        self._decode_keys_fnc   = None
        self.prevreadtime = 0
        self.crtreadtime = 0
        
        # Initialize the list of keys
        self.keys = {
            'dup' : {'name': 'DPad_Up', 'value': 0, 'pressduration': 0},
            'ddown' : {'name': 'DPad_Down', 'value': 0, 'pressduration': 0},
            'dleft' : {'name': 'DPad_Left', 'value': 0, 'pressduration': 0},
            'dright' : {'name': 'DPad_Right', 'value': 0, 'pressduration': 0},
            'start' : {'name': 'Start', 'value': 0, 'pressduration': 0},
            'select' : {'name': 'Select', 'value': 0, 'pressduration': 0},
            'l1' : {'name': 'L1_Trigger', 'value': 0, 'pressduration': 0},
            'r1' : {'name': 'R1_Trigger', 'value': 0, 'pressduration': 0},
            'analog' : {'name': 'Analog', 'value': 0, 'pressduration': 0},
            'cross' : {'name': 'Cross', 'value': 0, 'pressduration': 0},
            'circle' : {'name': 'Circle', 'value': 0, 'pressduration': 0},
            'square' : {'name': 'Square', 'value': 0, 'pressduration': 0},
            'triangle' : {'name': 'Triangle', 'value': 0, 'pressduration': 0},
            'l2' : {'name': 'L2_Trigger', 'value': 0, 'pressduration': 0},
            'r2' : {'name': 'R2_Trigger', 'value': 0, 'pressduration': 0},
            'ls_x' : {'name': 'LeftStick_LR', 'value': 0, 'pressduration': 0},
            'ls_left' : {'name': 'LeftStick_Left', 'value': 0, 'pressduration': 0},
            'ls_right' : {'name': 'LeftStick_Right', 'value': 0, 'pressduration': 0},
            'ls_y' : {'name': 'LeftStick_DU', 'value': 0, 'pressduration': 0},
            'ls_down' : {'name': 'LeftStick_Down', 'value': 0, 'pressduration': 0},
            'ls_up' : {'name': 'LeftStick_Up', 'value': 0, 'pressduration': 0},
            'rs_x' : {'name': 'RightStick_LR', 'value': 0, 'pressduration': 0},
            'rs_left' : {'name': 'RightStick_Left', 'value': 0, 'pressduration': 0},
            'rs_right' : {'name': 'RightStick_Right', 'value': 0, 'pressduration': 0},
            'rs_y' : {'name': 'RightStick_DU', 'value': 0, 'pressduration': 0},
            'rs_down' : {'name': 'RightStick_Down', 'value': 0, 'pressduration': 0},
            'rs_up' : {'name': 'RightStick_Up', 'value': 0, 'pressduration': 0}
        }

        # Intialize the usb host
        # Default pins correspond to TX and RX on JP2 connector of the Challanger+ RP2350 board.
        self.usb_dp = usb_dp
        self.usb_dn = usb_dn
        self._init_usbhost()

        # Detect USB devices
        self._detect_usb_devices()

        # Read the first report and check the operating mode
        self._read_validate_report()

        # Initialize the lists of handling functions for the operating modees
        self._init_cmdmasks_fnc = [self._init_cmdmasks_mode0, self._init_cmdmasks_mode1, self._init_cmdmasks_mode2]
        self._decode_keys_fnc = [self._decode_keys_mode0, self._decode_keys_mode1, self._decode_keys_mode2]

        # Initialize the command masks for the selected operating mode and run a first decoding of the keys
        self._init_cmdmasks_fnc[operating_mode]()
        self._decode_keys_fnc[operating_mode]()

    def __getitem__(self, item: tuple | str) -> float | None:
        """
        Simple index access to list of key values
        Based on https://github.com/ApproxEng/approxeng.input/src/python/approxeng/input/__init__.py

        :param item:
            the sname of an key, or a tuple thereof
        :return:
            for a key, the corrected value or None if not pressed/activated. Raises AttributeError
            if the given name doesn't correspond to key name. If a tuple is supplied as an argument, result
            will be a tuple of values.
        """

        if isinstance(item, tuple):
            return [self.__getattr__(single_item) for single_item in item]
        return self.__getattr__(item)

    def __getattr__(self, item: str) -> float | None:
        """
        Property short/cut access to self.keys[]['values'].
        Based on https://github.com/ApproxEng/approxeng.input/src/python/approxeng/input/__init__.py

        :param item:
            sname of a key
        :return:
            The key corrected value (None if not pressed), or AttributeError if sname not found
        """
        if item in self.keys.keys():
            return self.keys[item]['value']
        raise AttributeError
    
    def __repr__(self):
        return 'CircuitPython class for PiHut PS3-alike controller API'
    
    def __del__(self):
        """ Custom cleanup and garbage collection. """
        del self.device
        self.device = None
        gc.collect()

    #
    # The API functions
    #
    def read_keys(self) -> bool:
        """
        Read the USB HID report from the device and decode the keys for the configured operating mode.
        """
        # Read and validate a new report
        self._read_validate_report()

        # Ensure the operating mode has not changed
        # TODO: Handle the mode change, self.targetmode
        #self._check_mode()

        # Decode the keys
        # Only updates self.keys entries which have changed!
        return self._decode_keys_fnc[self.targetmode]()

    #
    # Internal functions
    #
    def _init_usbhost(self):
        """
        Initialize the USB host for the controller
        """
        # Create a port to use for the USB host. This USB host remains valid outside the VM.
        try:
            usb_host.Port(self.usb_dp, self.usb_dn)
            sleep(0.1)
        except:
            print(f"USB Host Port on pins/GPIOs {self.usb_dp} and {self.usb_dn} already created!")
        

    def _detect_usb_devices(self):
        """
        Detect the USB devices connected to the controller
        """

        # Find the target USB device
        for _d in range(len(IDPRODUCT)):
            try:
                self.device = usb.core.find(idVendor=IDVENDOR, idProduct=IDPRODUCT[_d])
                self.idVendor  = IDVENDOR
                self.idProduct = IDPRODUCT[_d]
                break
            except Exception as exc:
                self.device = None
                print(f"Target USB Device VID={hex(IDVENDOR)}, PID={hex(IDPRODUCT[_d])} was not found!")

        # If the target USB device was not found, list all the found devices and raise an error
        if self.device is None:
            print("USB Device(s) found:")
            for device in usb.core.find(find_all=True):
                print(f"  VID={hex(device.idVendor)}, PID={hex(device.idProduct)}")
            raise RuntimeError("Target USB device is not connected")

        # Test to see if the kernel is using the device and detach it.
        try:
            if self.device.is_kernel_driver_active(0):
                self.device.detach_kernel_driver(0)
        except Exception as exc:
            #print_exception(exc)
            raise RuntimeError("USB kernel driver active!")

        # Get Report Descriptor (Class Descriptor Type Report)
        # NOTE: DOES NOT ALWAYS WORK, AND RETURNS STANDARD DESCRIPTOR INSTEAD!
        try:
            # Section 7.1.1 in https://www.usb.org/sites/default/files/hid1_11.pdf
            # - The wValue field specifies the Descriptor Type in the high byte and the Descriptor Index in the low byte
            # - The low byte is the Descriptor Index used to specify the set for Physical Descriptors, and is reset to zero for other HID class descriptors
            _rep = array.array("B", [0] * 146) #137
            _count = self.device.ctrl_transfer(
                0x81, # bmRequestType = CTRL_IN | CTRL_TYPE_STANDARD | CTRL_RECIPIENT_INTERFACE = HID Class Descriptor
                0x06, # bRequest = GET_DESCRIPTOR
                0x2200, # wValue = Class Descriptor Type Report
                0x0, # wIndex = HID Interface Number
                _rep, # data_or_wLength
                2000 # timeout (in ms)
            )
            sleep(0.1)
        except Exception as exc:
            #print_exception(exc)
            raise RuntimeError("Failed to get the USB HID Report Descriptor!")

        # Set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:    
            self.device.set_configuration()
            sleep(0.1)
        except Exception as exc:
            #print_exception(exc)
            raise RuntimeError("Failed to set the USB device configuration!")

        # From now on, the device is ready to be used
        # Read quickly a few reports, otherwise the first reports carry other info (vendor specific?)
        self.repbuf = array.array("B", [0] * NUM_REPORT_BYTES)
        for _ in range(10):
            self.device.read(0x81, self.repbuf, timeout=1000)
            sleep(0.1)
        self.connected = True
        print(f"Target USB Device VID={hex(self.idVendor)}, PID={hex(self.idProduct)} is connected!")

    def _read_validate_report(self):
        """
        Read a USB HID report from the device.
        Validate the report.
        Update the read timestamps.
        """
        self.count = 0
        if self.connected:
            try:
                self.count = self.device.read(0x81, self.repbuf, timeout=1000)
                self._check_mode()
                self._update_read_timestamps()

            except ValueError as exc:
                #print_exception(exc)
                raise    
            except usb.core.USBTimeoutError as exc:
                #print_exception(exc)
                raise ValueError("USB Timeout Error!")
            except usb.core.USBError as exc:
                #print_exception(exc)
                raise ValueError("USB core Error!")
        
    def _check_mode(self):
        """
        Check the operating mode of the controller: 0, 1, or 2.
        """
        if self._check_report():
            if self.operatingmode != self.targetmode:
                raise ValueError(f"USB HID Report for operating mode{self.operatingmode} was detected while report expected for mode{self.targetmode}.\n  Report = {self.repbuf}!")
        else:
            raise ValueError(f"No (valid) USB HID Report available!\n  Report = {self.repbuf}")

    def _check_report(self) -> bool:
        """
        Check if the USB HID report is valid (any of the implemented modes 0, 1 or 2).
        """
        self.operatingmode = -1
        if not self.connected:
            return False
        
        if self.count < NUM_REPORT_BYTES:
            return False
        elif self.repbuf[0] == 0 and self.repbuf[1] == 20:
            self.operatingmode = 0
            return True
        elif self.repbuf[2] == 15 and self.repbuf[5] == 128 and self.repbuf[6] == 128:
            self.operatingmode = 1
            return True
        elif self.repbuf[2] == 15 and (self.repbuf[3] == 127 or self.repbuf[4] == 127):
            self.operatingmode = 2
            return True
        else:
            return False


    def _update_read_timestamps(self):
        """
        Update the read timestamps. 
        """
        if self.crtreadtime == 0:
            self.prevreadtime = monotonic()
        else:
            self.prevreadtime = self.crtreadtime
        self.crtreadtime = monotonic()

    def _update_value_duration(self, keys_action:str, value:float):
        """
        Update the value and press duration of the key.
        """
        if self.keys[keys_action]['value'] != value:
            self.keys[keys_action]['pressduration'] = monotonic() - self.crtreadtime
            self.keys[keys_action]['value'] = value
        else:
            self.keys[keys_action]['pressduration'] = self.crtreadtime - self.prevreadtime



    def _init_cmdmasks_mode0(self):
        """
        Initialize the command masks list (of dict) for the USB Controller for operating mode 0.
    
        Mode 0: Game Pad outputs 15 bytes when in, activated at start-up/reset

        array('B', [0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        buf[0]: Dummy = 0
        buf[1]: Dummy = 20
        buf[2]: 1 = DPad Up, 2 = DPad Down, 4 = DPad Left, 8 = DPad Right, 16 = Start, 32 = Select
        buf[3]: 1 = L1 Trigger, 2 = R1 Trigger, 4 = Analog, 16 = Cross, 32 = Circle, 64 = Square, 128 = Triangle
        buf[4]: 0-255 L2 Trigger
        buf[5]: 0-255 R2 Trigger
        buf[6-9]: Left Stick : 0/255 = Center
        buf[6] = 255 when buf[7] = 127, 0 = otherwise
        buf[7] = 0 - 127 RIGHT, 255 - 128 LEFT  
        buf[8] = 255 when buf[9] = 127, 0 = otherwise
        buf[9] = 0 - 127 UP, 255 - 128 DOWN   
        buf[10-13]: Right Stick: 0/255 = Center
        buf[10-13]: Same as Left Stick
        buf[14]: Dummy = 0
        """
        self.cmdmasks = [
            # The mode 1 can be identified by checking these first two bytes
            {0x00: 'dummy'},
            {0x14: 'dummy'}, 
            # DPad Up/Down/Left/Right, START, SELECT
            {
                0x01: 'dup',
                0x02: 'ddown',
                0x04: 'dleft',
                0x08: 'dright',
                0x10: 'start',
                0x20: 'select'
            },
            # L1/R1 Trigger, Home, Cross, Circle, Square, Triangle
            {
                0x01: 'l1',
                0x02: 'r1',
                0x04: 'analog', # Analog/Mode selection key
                0x10: 'cross',
                0x20: 'circle',
                0x40: 'square',
                0x80: 'triangle'
            },
            # L2/R2 Throttle
            {
                0xFF: 'l2'
            },
            {
                0xFF: 'r2'
            },
            # Left Stick
            {
                0x00: 'ignore'
            },
            {
                0xFE:{
                    0x80: ['ls_left', 'ls_right', 'ls_x']
                }
            },
            {
                0x00: 'ignore'
            },
            {
                0xFE:{
                    0x80: ['ls_down', 'ls_up', 'ls_y']
                }
            },
            # Right Stick
            {
                0x00: 'ignore'
            },
            {
                0xFE:{
                    0x80: ['rs_left', 'rs_right', 'rs_x']
                }
            },
            {
                0x00: 'ignore'
            },
            {
                0xFE:{
                    0x80: ['rs_down', 'rs_up', 'rs_y']
                }
            },
            {
                0x00: 'dummy'
            }
        ]

    def _decode_keys_mode0(self) -> bool:
        """ 
        Map the input report bytes to command values for operating mode 0.
        """
        if not self.connected:
            return False
        if self.count < NUM_REPORT_BYTES:
            return False
        
        # Iterate through each byte in the report and its corresponding masks
        for i, byte in enumerate(self.repbuf[:NUM_REPORT_BYTES]):
            for bit_mask, action in self.cmdmasks[i].items():

                # Dummy/ignore bytes
                if bit_mask == 0x00 or bit_mask == 0x14:
                    continue

                # The Trigger or Throttle buttons
                elif bit_mask == 0xFF:
                    self._update_value_duration(action, float(byte/255))
                    
                # The Joysticks with X-Y axis
                # TODO: https://approxeng.github.io/approxeng.input/simpleusage.html#circular-analogue-axes
                # https://approxeng.github.io/approxeng.input/api/input.html#approxeng.input.CircularCentredAxis
                elif bit_mask == 0xFE:
                    for bit_mask2, action2 in action.items():
                        if byte & bit_mask2:
                            #self._update_value_duration(action2[0], float((255-byte)/127))
                            #self._update_value_duration(action2[1], 0.0)
                            self._update_value_duration(action2[2], float((byte-255)/127)) # negative value
                        else:
                            #self._update_value_duration(action2[0], 0.0)
                            #self._update_value_duration(action2[1], float(byte/127))
                            self._update_value_duration(action2[2], float(byte/127)) # positive value

                # The on/off buttons
                else:
                    if byte & bit_mask:
                        self._update_value_duration(action, 1.0)
                    else:
                        self._update_value_duration(action, 0.0)

        return True

    def _init_cmdmasks_mode1(self):
        """
        Initialize the command masks list (of dict) for the USB Controller for operating mode 1.

        Mode 1: Game Pad outputs 15 bytes when activated with press on Analog + Right Stick UP x 7 times, then switching Analog OFF

        array('B', [0, 0, 15, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0])
        buf[0]: 1 = Right Stick Up (N) or Triangle, 2 = Right Stick Right (E) or Circle, 4 = Right Stick Down (S) or Cross, 8 = Right Stick Left (W) or Square; 
                3,6,12,9 = Right Stick NE, SE, SW, NW; 
                16 = L1 Trigger, 32 = R1 Trigger, 64 = L2 Trigger, 128 = R2 Trigger
        buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
        buf[2]: Dummy = 15
        buf[3-4]: Left Stick: 128 = Center, 0 = Left, 255 = Right, 0 = Up, 255 = Down
        buf[5-6]: Dummy = 128
        buf[7]: 0-255 = DPad Right
        buf[8]: 0-255 = DPad Left
        buf[9]: 0-255 = DPad Up
        buf[10]: 0-255 = DPad Down
        buf[11]: 0-255 = Triangle
        buf[12]: 0-255 = Circle
        buf[13]: 0-255 = Cross
        buf[14]: 0-255 = Square
        """
        self.cmdmasks = [
            {

            },

        ]

    def _decode_keys_mode1(self) -> bool:
        """ 
        Map the input report bytes to command values for operating mode 1.
        """
        if not self.connected:
            return False
        if self.count != NUM_REPORT_BYTES:
            return False

        return True


    def _init_cmdmasks_mode2(self):
        """
        Initialize the command masks list (of dict) for the USB Controller for operating mode 2.

        Mode 2: Game Pad outputs 15 bytes when activated with press on Analog + Right Stick UP x 7 times, then switching Analog ON

        array('B', [0, 0, 15, 127, 127, 127, 127, 0, 0, 0, 0, 0, 0, 0, 0])
        buf[0]: 1 = Triangle, 2 =  Circle, 4 = Cross, 8 = Square;
                16 = L1 Trigger, 32 = R1 Trigger, 64 = L2 Trigger, 128 = R2 Trigger
        buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
        buf[2]: 15 = No DPad press, 0 = DPad Up, 2 = DPad Right, 4 = DPad Down, 6 = DPad Left
        buf[3-4]: Left Stick: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
        buf[5-6]: Right Stick: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
        buf[7]: 0-255 = DPad Right 
        buf[8]: 0-255 = DPad Left 
        buf[9]: 0-255 = DPad Up 
        buf[10]: 0-255 = DPad Down 
        buf[11]: 0-255 = Triangle
        buf[12]: 0-255 = Circle
        buf[13]: 0-255 = Cross
        buf[14]: 0-255 = Square
        """
        self.cmdmasks = [
            {

            },
        ]

    def _decode_keys_mode2(self) -> bool:
        """ 
        Map the input report bytes to command values for operating mode 2.
        """
        if not self.connected:
            return False
        if self.count != NUM_REPORT_BYTES:
            return False
        
        return True
