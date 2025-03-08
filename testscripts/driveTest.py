# M.A.R.S. Rover Drive Test in CircuitPython. 
# Emulates commands received from the PiHut Wireless USB Game Controller.
# Press Ctrl-C to stop
#
import sys
from math import sqrt

# The custom drive functions library
from drivefunc import init_rover, drive_rover, stop_rover, brake_rover, cleanup_rover, seq_all_leds, LED_BLACK
init_rover(0.5)

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

print ("Test custom driving functions for the M.A.R.S. Rover.")
print ("Emulates commands received from the PiHut Wireless USB Game Controller.")
print ("Use the 'w' and 'z' keys to throttle speed up and down.")
print ("Use the left and right arrow keys to turn left and right.")
print ("Press 'x' to brake quickly.")
print ("Press space bar to coast stop.")
print ("Press Ctrl-C to end.\n")

try:
    throttle = 0.0
    left_right = 0.0
    front_back = 0.3

    while True:
        key = readkey()
        if key == ' ':
            stop_rover()
            print ('Coast to stop')
        elif key == 'x':
            brake_rover()
            print ('Brake quickly')

        elif key == 'w': #or ord(key) == 16:
            throttle += 0.3
            if throttle > 1:
                throttle = 1
            drive_rover(
                yaw = 0.0,
                throttle = throttle,
                l_r = left_right,
                f_b = front_back
            )
            print (f'Throttle up {throttle}')

        elif key == 'z': #or ord(key) == 17:
            throttle -= 0.3
            if throttle < -1:
                throttle = -1
            drive_rover(
                yaw = 0.0,
                throttle = throttle,
                l_r = left_right,
                f_b = front_back
            )
            print (f'Throttle down {throttle}')

        elif ord(key) == 19:
            left_right -= 0.1
            if (left_right < -1):
                left_right = -1
            front_back = sqrt(1 - left_right*left_right)
            if (front_back < 0):
                front_back = 0
            drive_rover(
                yaw = 0.0,
                throttle = throttle,
                l_r = left_right,
                f_b = front_back
            )
            print (f'Turn left {left_right}')

        elif ord(key) == 18:
            left_right += 0.1
            if (left_right > 1):
                left_right = 1
            front_back = sqrt(1 - left_right*left_right)
            if (front_back < 0):
                front_back = 0
            drive_rover(
                yaw = 0.0,
                throttle = throttle,
                l_r = left_right,
                f_b = front_back
            )
            print (f'Turn right {left_right}')

        elif ord(key) == 3:
            break

except KeyboardInterrupt:
    seq_all_leds(1, 0.1, LED_BLACK)
    print("Interrupted by user. Bye.")
    pass

except Exception as e:
    print (e)
    pass

finally:
    cleanup_rover()
