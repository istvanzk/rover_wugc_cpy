# M.A.R.S. Rover Servo Motors Test in CircuitPython.
# Press Ctrl-C to stop
#
import sys

# The base library
from rover_cpy import RoverClass

# Define variables for servo and degrees
servo = 0 # currently active servo (0 to 15)
degrees = 0 # Current angle of servo. 0 degrees is centre (-90 to +90)

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

print ("Test all the servos on the M.A.R.S. Rover.")
print ("Select Servo to test with 'w' and 'z'.")
print ("Use the left and right arrow keys to move the servo, with a 5 degree step.")
print ("Press 'x' to realigned to zero degree.")
print ("Press space bar to stop servos.")
print ("Press Ctrl-C to end.\n")

try:
    rover = RoverClass()
    rover.init()

    servo = 0
    while True:
        key = readkey()
        if key == 'x':
            degrees = 0
            rover.setServo(servo, degrees)
            print ('Servo ', servo, ': Centre',sep='')
            
        elif key == ' ':
            rover.stopServos()
            print ('Servo ', servo, ': Stop',sep='')

        elif key == 'w': #or ord(key) == 16:
            servo += 1
            servo %= 16
            print ('Servo ', servo, ': Selected',sep='')

        elif key == 'z': #or ord(key) == 17:
            servo -= 1
            servo %= 16
            print ('Servo ', servo, ': Selected',sep='')

        elif ord(key) == 19:
            degrees -= 5
            if (degrees < -85):
                degrees = -85
            rover.setServo(servo, degrees)
            print ('Servo ', servo, ': Value:', degrees, sep='')

        elif ord(key) == 18:
            degrees += 5
            if (degrees > 90):
                degrees = 90
            rover.setServo(servo, degrees)
            print ('Servo ', servo, ': Value:', degrees, sep='')

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
