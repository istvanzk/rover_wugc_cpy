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
import os
import gc

VERSION = "1.0.0"

def shell():
    """ The virtual shel script. """
    show_versions()
    #start_time = time.monotonic()
    clear_screen()  # Auto-clear screen on start
    print("Welcome to vOS-TS for M.A.R.S Rover Robot drive functions testing.")
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
        if script_name.endswith('.py') and script_name in os.listdir("./testscripts"):
            with open(f"./testscripts/{script_name}") as f:
                exec(f.read(), {})

        else:
            print(f"Error: {script_name} not found or invalid file type. Found {os.listdir("./testscripts")}")
    except Exception as e:
        print(f"Error running {script_name}: {e}")


def memuse(call:str):
    """ Run garbage collection and get accurate memory usage. """
    gc.collect()  
    total_ram = gc.mem_alloc() + gc.mem_free()
    used_ram = gc.mem_alloc()
    free_ram = gc.mem_free()
    usage_percent = (used_ram / total_ram) * 100 if total_ram > 0 else 0

    usedmsg = (f"Used RAM: {used_ram:,} bytes")
    totalmsg = (f"Total RAM: {total_ram:,} bytes")
    freemsg  = (f"Free RAM: {free_ram:,} bytes")
    percmsg = (f"Memory Usage: {usage_percent:.2f}%")
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
    print (f"vOS-TS version: {VERSION}")
    try:
        from rover_cpy import VERSION as rover_version
        print (f"Rover API version: {rover_version}")
    except ImportError as e:
        print(f"Error importing rover_cpy library: {e}")

    try:
        from drivefunc import VERSION as drive_version
        print (f"Drive API version: {drive_version}")
    except ImportError as e:
        print(f"Error importing drivefunc library: {e}")

    try:
        from pihutwugc import VERSION as pihut_version
        print (f"PiHut controller API version: {pihut_version}")
    except ImportError as e:
        print(f"Error importing pihutwugc library: {e}")

def show_help():
    """ Display the available commands. """
    print("Available commands:")
    print(" clear       - Clear the screen")
    print(" help        - Show this help message")
    print(" versions    - Show the vOS-TS, rover_cpy and pihutwugc implementation versions")
    print(" exit        - Exit the shell")
    print(" reboot      - Reboot the system")
    print(" memuse      - Show memory usage")
    print(" motor       - Run motorTest.py")
    print(" servo       - Run servoTest.py")
    print(" calib       - Run calibrateServos.py")
    print(" mast        - Run mastTest.py")
    print(" leds        - Run ledTest.py")
    print(" drive       - Run driveTest.py")
    print(" wugc        - Run wugcTest.py")
    print(" usbhost     - Run usbhostTest.py")
    print(" usbrep      - Run usbreportTest.py")


# The available commands
COMMANDS = {
    "clear": clear_screen,
    "help": show_help,
    "versions": show_versions,
    "exit": lambda: print("Exiting shell.") or exit(),
    "reboot": lambda: print("Exiting shell.") or microcontroller.reset(),
    "memuse": lambda: memuse("print")
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
