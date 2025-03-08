# M.A.R.S. Rover Servo Motors calibration in CircuitPython.
# Press Ctrl-C to exit without saving
# 
import sys

# The base library and the custom drive functions library
from rover_cpy import RoverClass, SERVO_FL, SERVO_RL, SERVO_FR, SERVO_RR, SERVO_MP, SERVO_MT

LED_RED    = (255,0,0)
LED_GREEN  = (0,255,0)
LED_BLUE   = (0,0,255)
LED_CYAN   = (0,255,255)

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

print ("Calibrate the servos on the M.A.R.S. Rover.")
print ("Select Servo to calibrate with '1' for FL, '2' for RL, '3' for FR, '4' for RR, '5' for MP or '6' for MT.")
print ("Use the left and right arrow keys to straighten the servo - zero offset.")
print ("Press 's' to save the calibration data in the EEROM.")
print ("Press Ctrl-C to exit without saving.\n")

try:
    rover = RoverClass()
    rover.init(0.4)
    
    print ('Existing servo offsets:')
    print (f"#1  {SERVO_FL}(SERVO_FL):{rover.offsets[SERVO_FL]}")
    print (f"#2  {SERVO_RL}(SERVO_RL):{rover.offsets[SERVO_RL]}")
    print (f"#3  {SERVO_FR}(SERVO_FR):{rover.offsets[SERVO_FR]}")
    print (f"#4  {SERVO_RR}(SERVO_RR):{rover.offsets[SERVO_RR]}")
    print (f"#5  {SERVO_MP}(SERVO_MP):{rover.offsets[SERVO_MP]}")
    print (f"#6  {SERVO_MT}(SERVO_MT):{rover.offsets[SERVO_MT]}\n")

    rover.setColor(LED_RED)
    while True:
        key = readkey()
        if key == '1':
            servo = SERVO_FL
            print (f"Servo: Front Left: Offset: {rover.offsets[SERVO_FL]}")
            rover.setColor(LED_RED)
            rover.setPixel(1, LED_GREEN)
            rover.show()
        elif key == '2':
            servo = SERVO_RL
            print (f"Servo: Rear Left: Offset: {rover.offsets[SERVO_RL]}")
            rover.setColor(LED_RED)
            rover.setPixel(0, LED_GREEN)
            rover.show()
        elif key == '3':
            servo = SERVO_FR
            print (f"Servo: Front Right: Offset: {rover.offsets[SERVO_FR]}")
            rover.setColor(LED_RED)
            rover.setPixel(2, LED_GREEN)
            rover.show()
        elif key == '4':
            servo = SERVO_RR
            print (f"Servo: Rear Right: Offset: {rover.offsets[SERVO_RR]}")
            rover.setColor(LED_RED)
            rover.setPixel(3, LED_GREEN)
            rover.show()
        elif key == '5':
            servo = SERVO_MP
            print (f"Servo: Mast Pan: Offset: {rover.offsets[SERVO_MP]}")
            rover.setColor(LED_RED)
            rover.setPixel(1, LED_BLUE)
            rover.setPixel(2, LED_BLUE)
            rover.show()
        elif key == '6':
            servo = SERVO_MT
            print (f"Servo: Mast Tilt: Offset: {rover.offsets[SERVO_MT]}")
            rover.setColor(LED_RED)
            rover.setPixel(1, LED_CYAN)
            rover.setPixel(2, LED_CYAN)
            rover.show()
        elif key == 'x' :
            rover.stopServos()
            print ("Stop all servos")
        elif ord(key) == 19:
            rover.EEPROM_OffsetValues[servo] -= 1
            rover.setServo(servo, rover.EEPROM_OffsetValues[servo])
            print (f"  Offset: {rover.EEPROM_OffsetValues[servo]}")
        elif ord(key) == 18:
            rover.EEPROM_OffsetValues[servo] += 1
            rover.setServo(servo, rover.EEPROM_OffsetValues[servo])
            print (f"  Offset: {rover.EEPROM_OffsetValues[servo]}")
        elif key == 's':
            print ("Saving servo offsets")
            rover.saveOffsets()
            break
        elif ord(key) == 3:
            break

except KeyboardInterrupt:
    print("Interrupted by user. Bye.")
    pass

finally:
    rover.setColor(LED_GREEN)
    print ("Final servo offsets:")
    print (f"#1  {SERVO_FL}(SERVO_FL)::{rover.offsets[SERVO_FL]}")
    print (f"#2  {SERVO_RL}(SERVO_RL)::{rover.offsets[SERVO_RL]}")
    print (f"#3  {SERVO_FR}(SERVO_FR)::{rover.offsets[SERVO_FR]}")
    print (f"#4  {SERVO_RR}(SERVO_RR)::{rover.offsets[SERVO_RR]}")
    print (f"#5  {SERVO_MP}(SERVO_MP)::{rover.offsets[SERVO_MP]}")
    print (f"#6  {SERVO_MT}(SERVO_MT)::{rover.offsets[SERVO_MT]}\n")
    rover.cleanup()
