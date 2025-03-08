# PiHut Wireless USB Game Controller Test in CircuitPython. 
# Press Ctrl-C to stop
#
import sys
from time import sleep
from traceback import print_exception

# The wireless USB Game Controller library
from pihutwugc import PiHutWUSBGameController

print ("Test the PiHut Wireless USB Game Controller circuitPython API used on the M.A.R.S. Rover.")
print ("Receives wireless commands from the PiHut Wireless USB Game Controller.")
print ("Press the START button on the WUGC to start the test.")
print ("Press Ctrl-C to end.\n")

try:
    # Init the USB controller
    pihutwugc = PiHutWUSBGameController()

    started = False
    while pihutwugc.connected:
        try:
            # Read the controller keys
            if pihutwugc.read_keys():

                # Wait START key press
                if not started and pihutwugc['start'] == 0:
                    continue
                started = True

                # Joysticks/axes
                lx_axis = pihutwugc['ls_x'] 
                ly_axis = pihutwugc['ls_y']
                rx_axis = pihutwugc['rs_x']
                ry_axis = pihutwugc['rs_y']
                print(f"LX: {lx_axis:04.2f}, LY: {ly_axis:04.2f}, RX: {rx_axis:04.2f}, RY: {ry_axis:04.2f}")

                # DPad keys
                dpad_left  = pihutwugc['dleft']
                dpad_right = pihutwugc['dright']
                dpad_up    = pihutwugc['dup']
                dpad_down  = pihutwugc['ddown']
                print(f"DPadL: {dpad_left:1.0f}, DPadR: {dpad_right:1.0f}, DPadU: {dpad_up:1.0f}, DPadD: {dpad_down:1.0f}")

                # Throttle and Trigger keys
                throttle_left  = pihutwugc['l2']
                throttle_right = pihutwugc['r2']
                trigger_left   = pihutwugc['l1']
                trigger_right  = pihutwugc['r1']
                print(f"ThrL: {throttle_left:04.2f}, ThrR: {throttle_right:04.2f}, TrigL: {trigger_left:1.0f}, TrigR: {trigger_right:1.0f}")
                                
                # Action and other keys
                circle   = pihutwugc['circle']
                square   = pihutwugc['square']
                triangle = pihutwugc['triangle']
                cross    = pihutwugc['cross']
                print(f"Circle: {circle:1.0f}, Square: {square:1.0f}, Triangle: {triangle:1.0f}, Cross :{cross:1.0f}")

                select   = pihutwugc['select']
                analog   = pihutwugc['analog'] # Analog/Mode selection key
                start    = pihutwugc['start']
                print(f"Select: {select:1.0f}, Analog: {analog:1.0f}, Start: {start:1.0f}")

            # Wait a short time before reading the controller again
            sleep(0.1)

        except ValueError as exc:
            print_exception(exc)
            # Re-initialize the USB controller?

            # Re-try after a short delay
            sleep(1.0)
            pass

except Exception as exc:  
    print_exception(exc)
    pass
finally:
    sleep(1.0)