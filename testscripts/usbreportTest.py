# USB HID Report Test for the PiHut Wireless USB Game Controller in CircuitPython 
#
# Prints USB device information, the USB HID report descriptor and the USB HID reports.

import usb.core
import array
import time
import board
import usb_host
from traceback import print_exception

READ_REPORT = True

CTRL_IN = 0x80
CTRL_TYPE_STANDARD = (0 << 5)
CTRL_RECIPIENT_INTERFACE = 1
USB_CLASS_wValue_GET_HID_REPORT_DESCRIPTOR = (0x22) << 8 # Report Descriptor

# Correspond to TX and RX on JP2 connector.
try:
    usb_host.Port(board.GP12, board.GP13)
except:
    print("USB Port already created")
time.sleep(0.1)

# HID-Compliant USB Game Controller
# (VID_2563, PID_0523 or PID_0575)
# (VID_045e, PID_028e)
dev=usb.core.find(idVendor=0x2563, idProduct=0x0575)
if True:
#for dev in usb.core.find(find_all=True):
    if dev is None:
        print("USB Device VID=0x2563, PID=0x0575 is not connected!?")
        print("USB Device(s) found:")
        for device in usb.core.find(find_all=True):
            print("  pid", hex(device.idProduct))
            print("  vid", hex(device.idVendor))
        raise ValueError("Target USB device is not connected")


    print(f"PID: {hex(dev.idProduct)}")
    print(f"VID: {hex(dev.idVendor)}")

    # Test to see if the kernel is using the device and detach it.
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
    
    # From https://github.com/amardhruva/shanwan-controller-fix/blob/main/fix-controller
    #foo = array.array("B", [0] * 20) #137
    #dev.ctrl_transfer(0xc1, 0x01, 0x0100, 0x00, foo, 1000)
    #print(f"foo: {foo}")

    # Get Report Descriptor (Class Descriptor Type Report) - DOES NOT ALWAYS WORK, AND RETURNS STANDARD DESCRIPTOR INSTEAD!
    # Section 7.1.1 in https://www.usb.org/sites/default/files/hid1_11.pdf
    # - The wValue field specifies the Descriptor Type in the high byte and the Descriptor Index in the low byte
    # - The low byte is the Descriptor Index used to specify the set for Physical Descriptors, and is reset to zero for other HID class descriptors
    rep = array.array("B", [0] * 146) #137
    count = dev.ctrl_transfer(
        0x81, # bmRequestType = CTRL_IN | CTRL_TYPE_STANDARD | CTRL_RECIPIENT_INTERFACE = HID Class Descriptor
        0x06, # bRequest = GET_DESCRIPTOR
        0x2200, # wValue = Class Descriptor Type Report
        0x0, # wIndex = HID Interface Number
        rep, # data_or_wLength
        2000 # timeout (in ms)
    )
    time.sleep(0.1)
    print(f"Report descriptor 0 {count} bytes:")
    for _i in range(count):
        print(f"{rep[_i]:02X} ", end="")

    print()
    input("Press Enter to continue...")

    # Set the active configuration. With no arguments, the first
    # configuration will be the active one
    dev.set_configuration()
    time.sleep(0.1)
    #print(dev)

    # The first subscript [0] accesses the first configuration, the second subscript [0,0] selects the first interface (with the first alternate setting) and the third subscript [0] selects the first endpoint.
    #endpoint = dev[0][(0,0)][0]
    #print(endpoint)
    
    # Game Pad outputs 15 bytes when in mode 1 (start-up, initial mode)
    # array('B', [0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    # buf[0]: Dummy = 0
    # buf[1]: Dummy = 20
    # buf[2]: 1 = HatUp, 2 = HatDown, 4 = HatLeft, 8 = HatRight, 16 = Start, 32 = Select
    # buf[3]: 1 = PaddleLeft, 2 = PaddleRight, 4 = Analog, 16 = Cross, 32 = Circle, 64 = Square, 128 = Triangle
    # buf[4]: 0-255 PaddleThrottleLeft
    # buf[5]: 0-255 PaddleThrottleRight
    # buf[6-9]: Left Stick X-Y : 0/255 = Center
    #   buf[6] = 255 when buf[7] = 127, 0 = otherwise
    #   buf[7] = 0 - 127 RIGHT, 255 - 128 LEFT  
    #   buf[8] = 255 when buf[9] = 127, 0 = otherwise
    #   buf[9] = 0 - 127 UP, 255 - 128 DOWN   
    # buf[10-13]: Right Stick Z-Rz: 0/255 = Center
    #   Same as Left Stck
    # buf[14]: Dummy = 0

    # Game Pad outputs 15 bytes when in mode 2a (after switching with press on Analog + Right Stick UP x 7) with Analog OFF 
    # array('B', [0, 0, 15, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0])
    # buf[0]: 1 = Right Stick Up (N) or Triangle, 2 = Right Stick Right (E) or Circle, 4 = Right Stick Down (S) or Cross, 8 = Right Stick Left (W) or Square; 
    #         3,6,12,9 = Right Stick NE, SE, SW, NW; 
    #         16 = PaddleLeft, 32 = PaddleRight, 64 = PaddleThrottleLeft, 128 = PaddleThrottleRight
    # buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
    # buf[2]: Dummy = 15
    # buf[3-4]: Left Stick X-Y: 128 = Center, 0 = Left, 255 = Right, 0 = Up, 255 = Down
    # buf[5-6]: Dummy = 128
    # buf[7]: 0-255 = HatRight
    # buf[8]: 0-255 = HatLeft
    # buf[9]: 0-255 = HatUp
    # buf[10]: 0-255 = HatDown
    # buf[11]: 0-255 = Triangle
    # buf[12]: 0-255 = Circle
    # buf[13]: 0-255 = Cross
    # buf[14]: 0-255 = Square

    # Game Pad outputs 15 bytes when in mode 2b (after switching with press Analog + Right Stick UP x 7) with Analog ON
    # array('B', [0, 0, 15, 127, 127, 127, 127, 0, 0, 0, 0, 0, 0, 0, 0])
    # buf[0]: 1 = Triangle, 2 =  Circle, 4 = Cross, 8 = Square;
    #         16 = PaddleLeft, 32 = PaddleRight, 64 = PaddleThrottleLeft, 128 = PaddleThrottleRight
    # buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
    # buf[2]: 15 = No press, 0 = HatUp, 2 = HatRight, 4 = HatDown, 6 = HatLeft
    # buf[3-4]: Left Stick X-Y: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
    # buf[5-6]: Right Stick X-Y: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
    # buf[7]: 0-255 = HatRight 
    # buf[8]: 0-255 = HatLeft 
    # buf[9]: 0-255 = HatUp 
    # buf[10]: 0-255 = HatDown 
    # buf[11]: 0-255 = Triangle
    # buf[12]: 0-255 = Circle
    # buf[13]: 0-255 = Cross
    # buf[14]: 0-255 = Square


    buf = array.array("B", [0] * 15)
    report_count = 0
    while READ_REPORT:
        try:
            count = dev.read(0x81, buf, timeout=1000)
        except usb.core.USBTimeoutError as exc:
            print_exception(exc)
            pass
        except usb.core.USBError as exc:
            print_exception(exc)
            pass

        report_count += 1
        print(f"{report_count} >>> {buf}")
        time.sleep(0.01)

