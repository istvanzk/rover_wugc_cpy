# M.A.R.S. Rover DC Motors Test in CircuitPython.
# Moves: Forward, Reverse, turn Right, turn Left, Stop 
# Press Ctrl-C to stop
#
# To check wiring is correct ensure the order of movement as above is correct
#
import sys

# The base library
from rover_cpy import RoverClass

# Define variables 
speed = 60

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

print ("Tests the motors on the M.A.R.S. Rover.")
print ("Use , or < to slow down.")
print ("Use . or > to speed up.")
print ("Speed changes take effect when the next arrow key is pressed.")
print ("Press 'w' or 'z' to move rover forward or reverse.")
print ("Press right or left arrow to spin rover left or right.")
print ("Press space bar to coast to stop.")
print ("Press b to brake and stop quickly.")
print ("Press Ctrl-C to end.\n")

try:
    rover = RoverClass()
    rover.init()

    while True:
        keyp = readkey()
        if keyp == 'w': #or ord(keyp) == 16:
            rover.forward(speed)
            print ('Forward', speed)
        elif keyp == 'z': #or ord(keyp) == 17:
            rover.reverse(speed)
            print ('Reverse', speed)
        elif ord(keyp) == 18:
            rover.spinRight(speed)
            print ('Spin Right', speed)
        elif ord(keyp) == 19:
            rover.spinLeft(speed)
            print ('Spin Left', speed)
        elif keyp == '.' or keyp == '>':
            speed = min(100, speed+10)
            print ('Speed+', speed)
        elif keyp == ',' or keyp == '<':
            speed = max (0, speed-10)
            print ('Speed-', speed)
        elif keyp == ' ':
            rover.stop()
            print ('Stop')
        elif keyp == 'b':
            rover.brake()
            print ('Brake')
        elif ord(keyp) == 3:
            break

except KeyboardInterrupt:
    print("Interrupted by user. Bye.")
    pass

except Exception as e:
    print (e)
    pass

finally:
    rover.cleanup()
    
