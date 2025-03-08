# M.A.R.S. Rover Smart RGB LEDs Test in CircuitPython.
# Press Ctrl-C to stop
#
import time

# The custom drive functions library
from drivefunc import init_rover, cleanup_rover, set_rlfb_led, seq_all_leds, flash_led, flash_all_leds, LED_GREEN, LED_BLUE, LED_BLACK
init_rover(0.5)

print ("Test LEDs animations on the M.A.R.S. Rover.")
print ("Press Ctrl-C to end.\n")

try:
    while True:
        set_rlfb_led(True, 30)
        time.sleep(3)
        set_rlfb_led(False, -20)
        time.sleep(3)
        seq_all_leds(3, 0.3, LED_GREEN)
        time.sleep(1)
        flash_all_leds(3, 0.5, LED_BLUE)
        time.sleep(1)
        flash_led(0, 3, 0.5, LED_BLUE, LED_GREEN)
        time.sleep(1)
        flash_led(3, 3, 0.5, LED_GREEN, LED_BLUE)
        time.sleep(1)

except KeyboardInterrupt:
    seq_all_leds(1, 0.1, LED_BLACK)
    print("Interrupted by user. Bye.")
    pass

except Exception as e:
    print (e)
    pass

finally:
    cleanup_rover()
