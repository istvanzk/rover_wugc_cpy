# M.A.R.S. Rover Pan&Tilt Test in CircuitPython.
# Press Ctrl-C to stop
#
import sys

# The base library
from rover_cpy import RoverClass

# Define variables for servo and degrees
pan_servo = 'MastPan'
tilt_servo = 'MastTilt'
pan_degrees = 0 # Current horizontal angle of servo. 0 degrees is centre (-90 to +90)
tilt_degrees = 0 # Current vertical angle of servo. 0 degrees is centre (-90 to +90)

#======================================================================
# Reading single character

def readchar():
    ch = sys.stdin.read(1)
    if ch == '0x03':
        raise KeyboardInterrupt
    return ch

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)

# End of single character reading
#======================================================================

print ("Tests the Pan & Tilt servos on the M.A.R.S. Rover.")
print ("Press 'w' or 'z' to tilt mast up or down.")
print ("Press right or left arrow to pan mast left or right.")
print ("Press space bar to stop both servos.")
print ("Press 'x' to realigned to zero degree both servo.")
print ("Press Ctrl-C to end.\n")

try:
    rover = RoverClass()
    rover.init()

    while True:
        key = readkey()
        if key == 'x':
            pan_degrees = 0
            tilt_degrees = 0
            rover.setServoMastPan(pan_degrees)
            rover.setServoMastTilt(tilt_degrees)
            print (f"Servos: {pan_servo} and {tilt_servo}: Centre")

        if key == ' ':
            rover.stopServos()
            print (f"Servos: {pan_servo} and {tilt_servo}: Stop")

        elif key == 'w': #or ord(key) == 16:
            tilt_degrees += 5
            if (tilt_degrees > 90):
                tilt_degrees = 90
            rover.setServoMastTilt(tilt_degrees)
            print (f"Servo: {tilt_servo}, Value: {tilt_degrees}")

        elif key == 'z': #or ord(key) == 17:
            tilt_degrees -= 5
            if (tilt_degrees < -90):
                tilt_degrees = -90
            rover.setServoMastTilt(tilt_degrees)  
            print (f"Servo: {tilt_servo}, Value: {tilt_degrees}")

        elif ord(key) == 19:
            pan_degrees -= 5
            if (pan_degrees < -90):
                pan_degrees = -90
            rover.setServoMastPan(pan_degrees)
            print (f"Servo: {pan_servo}, Value: {pan_degrees}")

        elif ord(key) == 18:
            pan_degrees += 5
            if (pan_degrees > 90):
                pan_degrees = 90
            rover.setServoMastPan(pan_degrees)
            print (f"Servo: {pan_servo}, Value: {pan_degrees}")

        elif ord(key) == 3:
            break

except KeyboardInterrupt:
    print("Interrupted by user. Bye.")
    pass

except Exception as e:
    print (e)
    pass

finally:
    rover.cleanup()
