# CircuitPython virtual OS shell with testing scripts for 4tronix M.A.R.S. Rover Robot

A virtual OS shell with testing scripts for the various functionalities of the [main CircuitPython modules](../README.md#circuitpython-modules).
The implementation is a simplified version of the [vOS-CircuitPython-Shell](https://github.com/Night-Traders-Dev/vOS-CircuitPython-Shell), adapted for the purpose of running the [test scripts](#test-scripts) specific for the M.A.R.S. Rover Robot.

## Main shell

### Installation

The code was built for and tested with:
* [Challenger+ RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) development board.
* [CircuitPython version en_GB-9.2.4](https://circuitpython.org/board/challenger_rp2350_wifi6_ble5/) from Adafruit.
* [mpy-cross-*-9.2.4-236](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/mpy-cross/)

Steps:

1) Install CircuitPython and all the custom rover modules as explained in the main [README](../README.md#installation).

2) Copy the [code.py](./code.py) file from this folder into the root of the CircuitPython device. Note that this operation will overwrite the potentially existing code.py file. 

   * There are four options: code.txt, code.py, main.txt and main.py, see [Creating and Editing Code](https://learn.adafruit.com/welcome-to-circuitpython/creating-and-editing-code#naming-your-program-file-2977482). CircuitPython looks for those files, in that order, and then runs the first one it finds. Hence, we use the `code.py` here to avoid overwriting the `main.py` which is needed to run the main rover code, see [README](../README.md#installation).

The code will run automatically after (soft) reboot and initiate the virtual OS shell in a serial terminal, while the RP2350-based board is connected to a PC. 

### Provided commands:

* `clear`: clear terminal
* `help`: display help with these commands
* `exit`: exit vOS shell
* `reboot`: exit and reset the microcontroller (reboot)
* `memuse`: diplay memory usage
* `versions`: display implementation version of this vOS shell, and of the custom rover related modules [rover_cpy](../lib/rover_cpy.py), [drivefunc](../lib/drivefunc.py) and [pihutwugc](../lib/pihutwugc.py)
* `env`: display environment variables defined in settings.toml 
* `motor`: run [motorTest.py](../testscripts/motorTest.py)
* `servo`: run [servoTest.py](../testscripts/servoTest.py)
* `calib`: run [calibrateServos.py](../testscripts/calibrateServos.py)
* `mast`: run [mastTest.py](../testscripts/mastTest.py)
* `leds`: run [ledTest.py](../testscripts/ledTest.py)
* `drive`: run [driveTest.py](../testscripts/driveTest.py)
* `wugc`: run [wugcTest](../testscripts/wugcTest.py)
* `usbhost`: run [usbhostTest.py](../testscripts/usbhostTest.py)
* `usbrep`: run [usbreportTest.py](../testscripts/usbreportTest.py)


## Test scripts

The [servoTest](../testscripts/servoTest.py), [motorTest](../testscripts/motorTest.py) and [mastTest](../testscripts/mastTest.py) scripts provide manual tests for various [rover_cpy](../lib/rover_cpy.py) functionalities. These scripts are based on their original counterparts provided by 4tronix. The [ledTest](../testscripts/ledTest.py) and [driveTest](../testscripts/driveTest.py) scripts provide manual tests for various [drivefunc](../lib/drivefunc.py) functionalities. The [wugcTest](../testscripts/wugcTest.py) script provides manual tests for various [pihutwugc](./lib/pihutwugc.py) functionalities.

The [calibrateServos](../testscripts/calibrateServos.py) can be used to calibrate the 0-degree position of the servo motors (1 to 6) and save the offsets in the EEPROM on the main rover board. This script is based on the original counterpart provided by 4tronix.

The [usbhostTest](../testscripts/usbhostTest.py) and [usbreportTest](../testscripts/usbreportTest.py) are standalone scripts, do not depend on the custom rover libraries, and can be used for testing the USB host functionalities in general. More details on USB host related implementation can be found in [README-USBHost](../README-USBHost.md). The [usbhostTest](../testscripts/usbhostTest.py) uses the [Adafruit USB Host Descriptors](https://github.com/adafruit/Adafruit_CircuitPython_USB_Host_Descriptors) library.