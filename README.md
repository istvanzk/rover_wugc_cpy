# CircuitPython code on RP2350 for 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller

![Exp](https://img.shields.io/badge/Dev-Experimental-orange.svg)
[![Lic](https://img.shields.io/badge/License-Apache2.0-green)](http://www.apache.org/licenses/LICENSE-2.0)
![CircuitPy](https://img.shields.io/badge/CircuitPython-9.2.4-green)
![Ver](https://img.shields.io/badge/Version-1.0-blue)

This folder contains the [CircuitPython 9.2.4](https://circuitpython.org/board/challenger_rp2350_wifi6_ble5/) code and interconnection diagram for controlling the [4tronix M.A.R.S. Rover Robot](https://4tronix.co.uk/blog/?p=2409
) using a [Challenger+ RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) development board instead of the Raspberry Pi Zero computer board.

## Table of contents
<!--ts-->
* [Hardware](#hardware)
* [CircuitPython modules](#circuitpython-modules)
  * [Installation](#installation)
  * [Configuration](#configuration)
  * [Main modules](#main-modules)
  * [Test scripts](#testing-scripts)
* [Virtual OS shell](./vos_ts/README-vosts.md)
* [USB Host implementation](./README-USBHost.md)
<!--te-->

## Hardware

The Rover control requires the following signals from the RP2350-based board to be provided to the main rover board, via the the 2x20-pin connector normally used for connecting the Raspberry Pi Zero. The Table below summarizes the connections and the CircuitPython modules used to control the required I/O signals.

The corresponding interconnection diagram is available in [ChallangerRP2350-MARS](./circuit/ChallangerRP2350-MARS.pdf).

|               Controls     |   I/O  | RasPi GPIO  | RP2350 GPIO (JP1/2 pin) | CircuitPython module |
|----------------------------|-------------|-------------|--------------------|--------------------|
|DC motors (via DRV8833)     | 4x PWM      | 12, 16, 13, 19 | 24(D6), 25(D9), 2(D10), 3(D11) | [pwmio](https://docs.circuitpython.org/en/latest/shared-bindings/pwmio/index.html) |
|Servo motoros (via PCS9685) | I2C @ 0x40  | 2, 3        | 20 (SDA), 21 (SCL) | [busio.I2C](https://docs.circuitpython.org/en/latest/shared-bindings/busio/index.html#busio.I2C), [PCA9685](https://docs.circuitpython.org/projects/pca9685/en/stable/index.html), [motor-servo](https://docs.circuitpython.org/projects/motor/en/stable/examples.html#motor-servo-sweep) |
|EEROM                       | I2C @ 0x50  | 2, 3        | 20 (SDA), 21 (SCL) | [I2C Bus device](https://docs.circuitpython.org/projects/busdevice/en/stable/api.html#adafruit-bus-device-i2c-device-i2c-bus-device) |
|LED control (direct)        | 1x PWM      | 18          | 7 (D13) | [newopixel](https://docs.circuitpython.org/projects/neopixel/en/latest/) |
|#23, #24, #25, #05          | 4x GPIO     | 23, 24, 25, 5 | 26 (A3), 27(A2), 28(A1), 29(A0) | [digitalio](https://docs.circuitpython.org/en/latest/shared-bindings/digitalio/index.html) |

## CircuitPython modules

The code was built for and tested with:
* [Challenger+ RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) development board.
* [CircuitPython version en_GB-9.2.4](https://circuitpython.org/board/challenger_rp2350_wifi6_ble5/) from Adafruit.
* [mpy-cross-*-9.2.4-236](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/mpy-cross/)
* [PiHut Wireless USB Game Controller](https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller)

### Installation

Steps:

1) [Install CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython) on the device. The following libraries are required to be present in the `lib` folder in the root of the CircuitPython device, on the [Challenger+ RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) board: `adafruit_motor`folder , `neopiel.mpy`, `adafruit_pixelbuf.mpy`, `adafruit_pca9685.mpy` and `adafruit_hcsr04.mpy`.

2) Copy the content of the root folder, including the [lib](./lib/) folder, from the repo into the root of the CircuitPython device. The library files in [lib](./lib/) can be [compiled to mpy format](https://learn.adafruit.com/welcome-to-circuitpython/frequently-asked-questions#faq-3105290) to save space.

3) Copy the [main.py](./code.py) and [boot.py](./boot.py) files into the root of the CircuitPython device. Note that this operation will overwrite the potentially existing main.py and boot.py files. 
   * There are four options: code.txt, code.py, main.txt and main.py, see [Creating and Editing Code](https://learn.adafruit.com/welcome-to-circuitpython/creating-and-editing-code#naming-your-program-file-2977482). CircuitPython looks for those files, in that order, and then runs the first one it finds. Hence, we use the `main.py` here to allow running the optional [virtual OS shell](./vos_ts/README-vosts.md) from the `code.py` without overwriting the `main.py`.

The main code will run automatically after (soft) reboot and does not require serial terminal access.

### Configuration

The [settings.toml](./settings.toml) is used to configure the parameters for the custom M.A.R.S Rover drive modules. The variables in this file are read a [environment variables](https://docs.circuitpython.org/en/latest/docs/environment.html) in CircuitPython.

### Main modules

The [main](./main.py) is the main CircuitPython implementation for the 4tronix M.A.R.S. Rover Robot remote control using the [PiHut Wireless USB Game Controller](https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller). It uses the modules `rover_cpy`, `drivefunc` and `pihutwugc` described below.

The [rover_cpy](./lib/rover_cpy.py) implements the API to the rover hardware. For maximum backwards compatibility with the original `rover.py` implementation provided by 4tronix, almost all the function definitions in this class are kept identical. This class also implements the original pca9685.py functionalities.

The [pihutwugc](./lib/pihutwugc.py) implements the API for the PiHut Wireless USB Game Controller, loosely insipired by the [Approximate Engineering](https://approxeng.github.io/approxeng.input/simpleusage.html#standard-names) implementation and adapted for CircuitPython. This class implements only the API for the [PiHut Wireless USB Game Controller](https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller) for now, see details in [README-USBHost](./README-USBHost.md#usb-hid-report-on-a-rp2350-based-board).

The [drivefunc](./lib/drivefunc.py) implements the custom functions to drive and control the rover. It uses the `rover_cpy` API. This implementation is based on the Python code from [rover_wugc](https://github.com/istvanzk/rover_wugc).

### Test scripts

The [servoTest](./testscripts/servoTest.py), [motorTest](./testscripts/motorTest.py) and [mastTest](./testscripts/mastTest.py) scripts provide manual tests for various [rover_cpy](./lib/rover_cpy.py) functionalities. These scripts are based on their original counterparts provided by 4tronix. The [ledTest](./testscripts/ledTest.py) and [driveTest](./testscripts/driveTest.py) scripts provide manual tests for various [drivefunc](./lib/drivefunc.py) functionalities. The [wugcTest](./testscripts/wugcTest.py) script provides manual tests for various [pihutwugc](./lib/pihutwugc.py) functionalities.

The [calibrateServos](./testscripts/calibrateServos.py) can be used to calibrate the 0-degree position of the servo motors (1 to 6) and save the offsets in the EEPROM on the main rover board. This script is based on the original counterpart provided by 4tronix.

The [usbhostTest](./testscripts/usbhostTest.py) and [usbreportTest](./testscripts/usbreportTest.py) are standalone scripts, do not depend on the custom rover libraries above, and can be used for testing the USB host functionalities in general. More details on USB host related implementation can be found in [README-USBHost](./README-USBHost.md). The [usbhostTest](./testscripts/usbhostTest.py) uses the [Adafruit USB Host Descriptors](https://github.com/adafruit/Adafruit_CircuitPython_USB_Host_Descriptors) library (`adafruit_usb_host_descriptors.mpy`).

All these test scripts require a serial terminal, while the RP2350-based board is connected to a PC, and can be run from the [virtual OS shell](./vos_ts/README-vosts.md) or from the REPL.
