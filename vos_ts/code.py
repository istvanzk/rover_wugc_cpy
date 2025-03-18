# -*- coding: utf-8 -*-
# A virtual OS shell providing the execution of testing scripts (TS) for the various functionalities of the main CircuitPython modules
# for the 4tronix M.A.R.S. Rover Robot related functions and controls. 
#
# Version: 1.0.0
#
#  The code is a simplified version of the vOS-CircuitPython-Shell (https://github.com/Night-Traders-Dev/vOS-CircuitPython-Shell) 
#  adapted for the purpose of running the individual test scripts specific for the M.A.R.S. Rover Robot.
#
# MIT License, see LICENSE file in this repo folder.
#
#import time
import microcontroller
import sys
from os import listdir, getenv
import gc

VERSION = "1.0.5"

# VT100 control sequences
# https://docs.circuitpython.org/en/latest/shared-bindings/terminalio/index.html
# https://github.com/jedgarpark/parsec/blob/main/2025-03-13/ansi_text_code.py
RED_FG = "\33[31m"
#RED_BG = "\33[41m"
GREEN_FG = "\33[32m"
#GREEN_BG = "\33[42m"
YELLOW_FG = "\33[33m"
#YELLOW_BG = "\33[43m"
BLUE_FG = "\33[34m"
#BLUE_BG = "\33[44m"
MAGENTA_FG = "\33[35m"
#MAGENTA_BG = "\33[45m"
#WHITE_FG = "\33[37m"
#WHITE_BG = "\33[47m"
RST = "\33[0m"

def shell():
    """ The virtual shel script. """
    #start_time = time.monotonic()
    clear_screen()  # Auto-clear screen on start
    print("Welcome to vOS-TS for M.A.R.S Rover Robot drive functions testing.")
    show_versions()
    show_help()
    while True:
        try:
            input_str = input("vOS-TS> ").strip()

            # Skip empty input
            if not input_str:
                continue

            # Handle the available commands
            if input_str in COMMANDS:
                COMMANDS[input_str]()
            elif input_str in COMMANDS_RUN:
                run(COMMANDS_RUN[input_str])  
            else:
                print(f"Unknown command: {input_str}")

        except KeyboardInterrupt:
            clear_screen() 
            print("\nShell command interrupted.")
            show_help()
            pass
        except Exception as e:
            print(f"Shell error: {e}")
            pass

def clear_screen():
    """ Function to clear the screen. """
    print("\033[2J\033[H", end="")  # ANSI escape code to clear screen

def run(script_name):
    """ Function to execute an available Python script. """
    try:
        if script_name.endswith('.py') and script_name in listdir("./testscripts"):
            with open(f"./testscripts/{script_name}") as f:
                exec(f.read(), {})

        else:
            print(f"Error: {script_name} not found or invalid file type. Found {listdir("./testscripts")}")
    except Exception as e:
        print(f"Error running {script_name}: {e}")


def memuse(call:str):
    """ Run garbage collection and get accurate memory usage. """
    gc.collect()  
    total_ram = gc.mem_alloc() + gc.mem_free()
    used_ram = gc.mem_alloc()
    free_ram = gc.mem_free()
    usage_percent = (used_ram / total_ram) * 100 if total_ram > 0 else 0

    usedmsg = (f"Used RAM: {YELLOW_FG}{used_ram:,} bytes{RST}")
    totalmsg = (f"Total RAM: {YELLOW_FG}{total_ram:,} bytes{RST}")
    freemsg  = (f"Free RAM: {YELLOW_FG}{free_ram:,} bytes{RST}")
    percmsg = (f"Memory Usage: {YELLOW_FG}{usage_percent:.2f}%{RST}")
    msg_list = [usedmsg, totalmsg, freemsg, percmsg]
    for msg in msg_list:
        if call == "print":
            print(msg)

def exit():
    """ Custom exit funtion. """
    gc.collect()
    sys.exit()

def show_versions():
    """ Displays the version of this vOS shell and of the rover modules. """
    print (f"vOS-TS version: {YELLOW_FG}{VERSION}{RST}")
    try:
        from rover_cpy import VERSION as rover_version
        print (f"Rover API version: {YELLOW_FG}{rover_version}{RST}")
    except ImportError as e:
        print(f"Error importing rover_cpy library: {e}")

    try:
        from drivefunc import VERSION as drive_version
        print (f"Drive API version: {YELLOW_FG}{drive_version}{RST}")
    except ImportError as e:
        print(f"Error importing drivefunc library: {e}")

    try:
        from pihutwugc import VERSION as pihut_version
        print (f"PiHut controller API version: {YELLOW_FG}{pihut_version}{RST}")
    except ImportError as e:
        print(f"Error importing pihutwugc library: {e}")

def show_envs():
    """ Display the environment variables defined in settings.toml """

    # The env parameters and their default values
    _env_wifi = {'CIRCUITPY_WIFI_SSID': 'None', 'CIRCUITPY_WIFI_PASSWORD': 'None', 'CIRCUITPY_WEB_API_PORT': '80', 'CIRCUITPY_WEB_API_PASSWORD': 'None'}
    _env_bool = {'USE_MAST_PAN': '0', 'USE_MAST_TILT': '0', 'USE_SONAR': '0', 'USE_IRSENSORS': '0', 'USE_KEYPAD': '0'}
    _env_str  = {'ROVER_STEERING_MODE': 'simple'}
    _env_indx = {'SERVO_FL' : '9', 'SERVO_FR': '11', 'SERVO_RL': '15', 'SERVO_RR': '13', 'SERVO_MP': '7', 'SERVO_MT': '6'}
    _env_pwm  = {'PWML1_GPIO': '2', 'PWML2_GPIO': '24', 'PWMR1_GPIO': '3', 'PWMR2_GPIO': '25', 'LED_GPIO': '7'}
    _env_gpio = {'SONAR_GPIO': 'None', 'IRFL_GPIO': 'None', 'IRFR_GPIO': 'None', 'IRLL_GPIO': 'None', 'IRLR_GPIO': 'None', 'KEYPADIN_GPIO': 'None', 'KEYPADOUT_GPIO': 'None'}


    def print_env(env_str, def_val):
        """ Print env variable values: set=green or default=red. """
        _v  = getenv(env_str)
        if _v:
            _fg = GREEN_FG
        else:
            _fg = RED_FG
            _v = def_val      
        print(f"  {env_str} = {_fg}{_v}{RST}")
        #print(f"  {env_str} = {_v}")

    def print_env_bool(env_str, def_val):
        """ Print boolean env variable values: set 1=green, set 0=blue or default=red. """
        _v  = getenv(env_str)
        if _v == 1:
            _fg = GREEN_FG
        elif _v == 0:
            _fg = BLUE_FG
        else:
            _fg = RED_FG
            _v = def_val      
        print(f"  {env_str} = {_fg}{_v}{RST}")
        #print(f"  {env_str} = {_v}")

    # Reset the colors
    #print(RST)

    # Display env variables and their values (set or default)
    print("# Used for WiFi and Web API access\n(set=green, default=red):")
    for _env, _def_val in _env_wifi.items():
        print_env(_env, _def_val)

    print()
    print("# Used in drivefunc.py")
    print("## Steering mode\n(set=green, default=red):")
    for _env, _def_val in _env_str.items():
        print_env(_env, _def_val)

    print()
    print("# Used in rover_cpy.py")
    print("## Define accessories to be enabled\n(Yes=green, No=blue, default=red):")
    for _env, _def_val in _env_bool.items():
        print_env_bool(_env, _def_val)

    print()
    print("## Define the servo indeces\n(set=green, default=red):")
    for _env, _def_val in _env_indx.items():
        print_env(_env, _def_val)

    print()
    print("## Mandatory 4 PWM GPIO pins used to control\nthe Left&Right DC motors and the RGB LED strip\n(set=green, default=red):")
    for _env, _def_val in _env_pwm.items():
        print_env(_env, _def_val)

    print()
    print("## Optional 4 GPIO pins\n(set=green, default=red):")
    for _env, _def_val in _env_gpio.items():
        print_env(_env, _def_val)


def show_help():
    """ Display the available commands. """
    print(f"{MAGENTA_FG}Available commands:{RST}")
    print(f" {MAGENTA_FG}clear{RST}       - Clear the screen")
    print(f" {MAGENTA_FG}help{RST}        - Show this help message")
    print(f" {MAGENTA_FG}exit{RST}        - Exit the shell")
    print(f" {MAGENTA_FG}reboot{RST}      - Reboot the system")
    print(f" {MAGENTA_FG}mem{RST}         - Show memory usage")
    print(f" {MAGENTA_FG}ver{RST}         - Show the vOS-TS, rover_cpy, driefunc and pihutwugc implementation versions")
    print(f" {MAGENTA_FG}env{RST}         - Show environment variables defined in settings.toml")
    print(f" {MAGENTA_FG}motor{RST}       - Run motorTest.py")
    print(f" {MAGENTA_FG}servo{RST}       - Run servoTest.py")
    print(f" {MAGENTA_FG}calib{RST}       - Run calibrateServos.py")
    print(f" {MAGENTA_FG}mast{RST}        - Run mastTest.py")
    print(f" {MAGENTA_FG}leds{RST}        - Run ledTest.py")
    print(f" {MAGENTA_FG}drive{RST}       - Run driveTest.py")
    print(f" {MAGENTA_FG}wugc{RST}        - Run wugcTest.py")
    print(f" {MAGENTA_FG}usbhost{RST}     - Run usbhostTest.py")
    print(f" {MAGENTA_FG}usbrep{RST}      - Run usbreportTest.py")


# The available commands
COMMANDS = {
    "clear": clear_screen,
    "help": show_help,
    "exit": lambda: print("Exiting shell.") or exit(),
    "reboot": lambda: print("Exiting shell.") or microcontroller.reset(),
    "mem": lambda: memuse("print"),
    "ver": show_versions,
    "env": show_envs,
}
COMMANDS_RUN = {
    "motor": "motorTest.py",
    "servo": "servoTest.py",
    "calib": "calibrateServos.py",
    "mast": "mastTest.py",
    "leds": "ledTest.py",
    "drive": "driveTest.py",
    "wugc": "wugcTest.py",
    "usbhost": "usbhostTest.py",
    "usbrep": "usbreportTest.py"
}

# Run the shell
shell()
