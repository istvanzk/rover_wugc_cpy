# USB Host implemenation in CircuitPython on RP2350 for PiHut Wireless USB Game Controller

## Table of contents
<!--ts-->
* [USB Host for PiHut Wireless USB Game Controller](#usb-host-for-pihut-wireless-usb-game-controller)
  * [Summary](#summary)
  * [Wirless dongle plugged into a Raspberry Pi Zero](#wirless-dongle-plugged-into-a-raspberry-pi-zero)
  * [Wirless dongle plugged into a RP2350 based board](#wirless-dongle-plugged-into-a-rp2350-based-board)
  * [USB HID Report on a RP2350 based board](#usb-hid-report-on-a-rp2350-based-board)
<!--te-->


## USB Host for PiHut Wireless USB Game Controller

On the [Challenger+ RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) the GPIO12 and GPIO13 are the TX and RX pins on the JP2 breakout.
A USB host can be instatiated on the GPIO12 (USB D+) and GPIO13 (USB D-).

| Controls   |   I/O       | RP2350 GPIO (JP1/2 pin)  | CircuitPython module |
|------------|-------------|------------------------------|-------------------|
| PiHut wireless USB dongle | USB DP, DN | 12(TX), 13(RX) | [usb_hots](https://docs.circuitpython.org/en/latest/shared-bindings/usb_host/index.html), [usb.core](https://docs.circuitpython.org/en/latest/shared-bindings/usb/core/index.html) |


### Summary

The wireless USB dongle was identified in three different ways, as described in the following sections, with the summary results as in the Table below.

|         | Vendor  | Product | Manuf.             | Product         |
|---------|---------|---------|--------------------|-----------------|
| RPiZero: input/devices | 2563    | 0526    | SHANWAN            | Android Gamepad |
| RP2350: USB Host device info | 2563    | 0575    | Nintendo Co., Ltd. | Pro Controller  |
| RP2350: USB Standard Descriptor | 2563    | 0575    | ShanWan            | XBOX 360 For Windows |


The USB HID [report descriptor(s)](#usb-hid-report-on-a-rp2350-based-board) which are useful when writting the CircuitPython code were found via trial-and-error and reverse engineering.

The detection of the wireless USB dongle by the USB host can be tested with the [usbhostTest.py](./lib/usbhostTest.py) CircuitPython script running on the Challenger+ RP2350 WiFi6/BLE5 board.

The reading/parsing of the USB HID reports from the wireless USB dongle can be tested with the [usbreportTest.py](.lib/usbreportTest.py) CircuitPython script running on the Challenger+ RP2350 WiFi6/BLE5 board.

The next sections provide a more detailed description of the USB HID reports and the way I decoded them. 

### Wirless dongle plugged into a Raspberry Pi Zero 

The on-board USB OTG port only supports USB2.0 devices, according to the [official description](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#raspberry-pi-zero-1-2-and-3).

The controller provides 3 events:

```
> sudo evemu-describe
Available devices:
/dev/input/event0:	SHANWAN Android Gamepad
/dev/input/event1:	SHANWAN Android Gamepad System Control
/dev/input/event2:	SHANWAN Android Gamepad Consumer Control
/dev/input/event3:	vc4-hdmi
Select the device event number [0-3]: 0
```

It can identified with:

```
> cat /proc/bus/input/devices | grep -A3 -B5 event0
I: Bus=0003 Vendor=2563 Product=0526 Version=0110
N: Name="SHANWAN Android Gamepad"
P: Phys=usb-20980000.usb-1/input0
S: Sysfs=/devices/platform/soc/20980000.usb/usb1/1-1/1-1:1.0/0003:2563:0526.0001/input/input0
U: Uniq=
H: Handlers=event0 js0
B: PROP=0
B: EV=1b
B: KEY=7fff0000 0 0 0 0 0 0 0 0 0
```

And the USB HID report decriptor can be read with:

``` 
> hexdump -C /sys/bus/hid/devices/0003\:2563\:0526.0001/report_descriptor
00000000  05 01 09 05 a1 01 85 07  09 01 a1 00 09 30 09 31  |.............0.1|
00000010  09 32 09 35 15 00 26 ff  00 75 08 95 04 81 02 c0  |.2.5..&..u......|
00000020  09 39 15 00 25 07 35 00  46 3b 01 65 14 75 04 95  |.9..%.5.F;.e.u..|
00000030  01 81 42 75 04 95 01 81  01 05 09 19 01 29 0f 15  |..Bu.........)..|
00000040  00 25 01 75 01 95 10 81  02 05 02 15 00 26 ff 00  |.%.u.........&..|
00000050  09 c4 09 c5 95 02 75 08  81 02 75 08 95 01 81 01  |......u...u.....|
00000060  c0                                                |.|
```

The hexdump can be further decoded with [USB Descriptor and Request Parser](https://eleccelerator.com/usbdescreqparser/) as below (with empty lines and comments added manually). This indicates a 11 bytes report to be expected from the wireless dongle.


```
0x05, 0x01,        // Usage Page (Generic Desktop Ctrls)
0x09, 0x05,        // Usage (Game Pad)
0xA1, 0x01,        // Collection (Application)
0x85, 0x07,        //   Report ID (7)

0x09, 0x01,        //   Usage (Pointer)
0xA1, 0x00,        //   Collection (Physical) -> Two joysticks: X-Y and Z-Rz
0x09, 0x30,        //     Usage (X)
0x09, 0x31,        //     Usage (Y)
0x09, 0x32,        //     Usage (Z)
0x09, 0x35,        //     Usage (Rz)
0x15, 0x00,        //     Logical Minimum (0)
0x26, 0xFF, 0x00,  //     Logical Maximum (255)
0x75, 0x08,        //     Report Size (8)
0x95, 0x04,        //     Report Count (4) -> 4 reports 8 bits each
0x81, 0x02,        //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
0xC0,              //   End Collection

0x09, 0x39,        //   Usage (Hat switch) -> Point Of View Hat switches (4 buttons)
0x15, 0x00,        //   Logical Minimum (0)
0x25, 0x07,        //   Logical Maximum (7)
0x35, 0x00,        //   Physical Minimum (0)
0x46, 0x3B, 0x01,  //   Physical Maximum (315)
0x65, 0x14,        //   Unit (Rotation in degrees [1° units] (4=System=English Rotation, 1=Rotation=Degrees))
0x75, 0x04,        //   Report Size (4)
0x95, 0x01,        //   Report Count (1) -> 1 report 4 bits
0x81, 0x42,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,Null State)

0x75, 0x04,        //   Report Size (4)
0x95, 0x01,        //   Report Count (1) -> 1 report 4 bits
0x81, 0x01,        //   Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position) -> Ignore (padding bits)

0x05, 0x09,        //   Usage Page (Button) -> 15 ON/OFF buttons ?
0x19, 0x01,        //   Usage Minimum (0x01) -> Button 1 Primary/trigger (Selector, On/Off Control, Momentary Control, or One Shot Control)
0x29, 0x0F,        //   Usage Maximum (0x0F) -> Button 15 ...
0x15, 0x00,        //   Logical Minimum (0)
0x25, 0x01,        //   Logical Maximum (1)
0x75, 0x01,        //   Report Size (1)
0x95, 0x10,        //   Report Count (16) -> 16 reports 1 bit each
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x05, 0x02,        //   Usage Page (Sim Ctrls) -> L & R paddle buttons
0x15, 0x00,        //   Logical Minimum (0)
0x26, 0xFF, 0x00,  //   Logical Maximum (255)
0x09, 0xC4,        //   Usage (Accelerator)
0x09, 0xC5,        //   Usage (Brake)
0x95, 0x02,        //   Report Count (2)
0x75, 0x08,        //   Report Size (8) -> 2 reports 8 bits each
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x75, 0x08,        //   Report Size (8)
0x95, 0x01,        //   Report Count (1) -> 1 report 8 bits
0x81, 0x01,        //   Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position) -> Ignore (padding bits)

0xC0,              // End Collection

// 97 bytes
```

### Wirless dongle plugged into a RP2350 based board

I used a setup with:

* [Challenger RP2350 WiFi6/BLE5](https://ilabs.se/product/challenger-rp2350-wifi-ble/) development board.
* [CircuitPython version en_GB-9.2.4](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/challenger_rp2350_wifi6_ble5) from Adafruit.
  * `usb_host` and `usb.core` modules

The reading/parsing of the USB HID reports from the wireless USB dongle can be tested with the [usbreportTest.py](./lib/usbreportTest.py) CircuitPython script running on the Challenger RP2350 WiFi6/BLE5 board.

The [USB Host device info](https://learn.adafruit.com/adafruit-feather-rp2040-with-usb-type-a-host/usb-host-device-info-2) script returns:

```
pid 0x575
vid 0x2563
man Nintendo Co., Ltd.
product Pro Controller
serial None
config[0]:
    value 1
    interface[0]
        class 03 subclass 00
        IN 81
        OUT 02
```

**NOTE #1**: These PID and VID values are different compared to the case when using the RaspberryPi Zero!

The USB HID report descriptor can be obtained in CircuitPython code by sending a request to the device
according to Section 7.1 in [Device Class Definition for Human Interface Devices (HID), Version 1.11](https://www.usb.org/sites/default/files/hid1_11.pdf):

```
rep = array.array("B", [0] * 146) #137
count = dev.ctrl_transfer(
    0x81, # bmRequestType = CTRL_IN | CTRL_TYPE_STANDARD | CTRL_RECIPIENT_INTERFACE = HID Class Descriptor
    0x06, # bRequest = GET_DESCRIPTOR
    0x2200, # wValue = Class Descriptor Type Report
    0x0, # wIndex = HID Interface Number
    rep, # data_or_wLength
    2000 # timeout (in ms)
)
```

**NOTE #2**: Despite the specific request, the above code returns two types of reports. 
It was impossible to deterministically obtained the USB HID Report Descriptor!
* USB Standard Descriptor
* USB HID Report Descriptor

Both descriptors can be decoded with [USB Descriptor and Request Parser](https://eleccelerator.com/usbdescreqparser/).

====== USB Standard Descriptor ======
```
12 01 00 02 FF FF FF 40 5E 04 8E 02 00 01 01 02 03 01 09 02 30 00 01 01 00 A0 FA 09 04 00 00 02 FF 5D 01 00 10 21 10 01 01 
24 81 14 03 00 03 13 02 00 03 00 07 05 81 03 20 00 04 07 05 02 03 20 00 08 04 03 09 04 10 03 53 00 68 00 61 00 6E 00 57 00 
61 00 6E 00 2A 03 58 00 42 00 4F 00 58 00 20 00 33 00 36 00 30 00 20 00 46 00 6F 00 72 00 20 00 57 00 69 00 6E 00 64 00 6F 
00 77 00 73 00 10 03 30 00 30 00 30 00 30 00 30 00 30 00 30 00 00 14
``` 

Decoded [and explanations](https://beyondlogic.org/usbnutshell/usb5.shtml) as:


```
0x12,        // bLength
0x01,        // bDescriptorType (Device)
0x00, 0x02,  // bcdUSB 2.00
0xFF,        // bDeviceClass 
0xFF,        // bDeviceSubClass 
0xFF,        // bDeviceProtocol 
0x40,        // bMaxPacketSize0 64
0x5E, 0x04,  // idVendor 0x045E
0x8E, 0x02,  // idProduct 0x028E
0x00, 0x01,  // bcdDevice 2.00
0x01,        // iManufacturer (String Index)
0x02,        // iProduct (String Index)
0x03,        // iSerialNumber (String Index)
0x01,        // bNumConfigurations 1

0x09,        // bLength
0x02,        // bDescriptorType (Configuration)
0x30, 0x00,  // wTotalLength 48
0x01,        // bNumInterfaces 1
0x01,        // bConfigurationValue
0x00,        // iConfiguration (String Index)
0xA0,        // bmAttributes Remote Wakeup
0xFA,        // bMaxPower 500mA

0x09,        // bLength
0x04,        // bDescriptorType (Interface)
0x00,        // bInterfaceNumber 0
0x00,        // bAlternateSetting
0x02,        // bNumEndpoints 2
0xFF,        // bInterfaceClass --> Vendor specific Class
0x5D,        // bInterfaceSubClass
0x01,        // bInterfaceProtocol
0x00,        // iInterface (String Index)

0x10,        // bLength
0x21,        // bDescriptorType (HID)
0x10, 0x01,  // bcdHID 1.10
0x01,        // bCountryCode
0x24,        // bNumDescriptors
0x81,        // bDescriptorType[0] (Unknown 0x81)
0x14, 0x03,  // wDescriptorLength[0] 788
0x00,        // bDescriptorType[1] (Unknown 0x00)
0x03, 0x13,  // wDescriptorLength[1] 4867
0x02,        // bDescriptorType[2] (Unknown 0x02)
0x00, 0x03,  // wDescriptorLength[2] 768
0x00,        // bDescriptorType[3] (Unknown 0x00)

0x07,        // bLength
0x05,        // bDescriptorType (Endpoint)
0x81,        // bEndpointAddress (IN/D2H)
0x03,        // bmAttributes (Interrupt)
0x20, 0x00,  // wMaxPacketSize 32
0x04,        // bInterval 4 (unit depends on device speed)

0x07,        // bLength
0x05,        // bDescriptorType (Endpoint)
0x02,        // bEndpointAddress (OUT/H2D)
0x03,        // bmAttributes (Interrupt)
0x20, 0x00,  // wMaxPacketSize 32
0x08,        // bInterval 8 (unit depends on device speed)

0x04,        // bLength
0x03,        // bDescriptorType (String)
0x09, 0x04,  // 0x0409 English - United State

0x10,        // bLength
0x03,        // bDescriptorType (String) 
0x53, 0x00, 0x68, 0x00, 0x61, 0x00, 0x6E, 0x00, 0x57, 0x00, 0x61, 0x00, 0x6E, 0x00, --> "ShanWan" 
0x2A,        // bLength
0x03,        // bDescriptorType (String)
0x58, 0x00, 0x42, 0x00, 0x4F, 0x00, 0x58, 0x00, 0x20, 0x00, 0x33, 0x00, 0x36, 0x00, 0x30, 0x00, 0x20, 0x00, 0x46, 0x00, 0x6F, 0x00, 0x72, 0x00, 0x20, 0x00, 0x57, 0x00, 0x69, 0x00, 0x6E, 0x00, 0x64, 0x00, 0x6F, 0x00, 0x77, 0x00, 0x73, 0x00, --> "XBOX 360 For Windows"
0x10,        // bLength
0x03,        // bDescriptorType (String)
0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00, 0x00, 0x00 --> "0000000"

// 146 bytes
```

**NOTE #3**: The string descriptors indicate "ShanWan" and "XBOX 360 For Windows" 

====== USB HID Report Descriptor ======
```
05 01 09 05 A1 01 15 00 25 01 35 00 45 01 75 01 95 0D 05 09 19 01 29 0D 81 02 95 03 81 01 05 01 25 07 
46 3B 01 75 04 95 01 65 14 09 39 81 42 65 00 95 01 81 01 26 FF 00 46 FF 00 09 30 09 31 09 32 09 35 75 
08 95 04 81 02 06 00 FF 09 20 09 21 09 22 09 23 09 24 09 25 09 26 09 27 09 28 09 29 09 2A 09 2B 95 0C 
81 02 0A 21 26 95 08 B1 02 0A 21 26 91 02 26 FF 03 46 FF 03 09 2C 09 2D 09 2E 09 2F 75 10 95 04 81 02 
C0
```

Decoded:

```
0x05, 0x01,        // Usage Page (Generic Desktop Ctrls)
0x09, 0x05,        // Usage (Game Pad)
0xA1, 0x01,        // Collection (Application)
0x15, 0x00,        //   Logical Minimum (0)
0x25, 0x01,        //   Logical Maximum (1)
0x35, 0x00,        //   Physical Minimum (0)
0x45, 0x01,        //   Physical Maximum (1)
0x75, 0x01,        //   Report Size (1)
0x95, 0x0D,        //   Report Count (13) --> 13 reports, 1 bit each
0x05, 0x09,        //   Usage Page (Button)
0x19, 0x01,        //   Usage Minimum (0x01)
0x29, 0x0D,        //   Usage Maximum (0x0D)
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x95, 0x03,        //   Report Count (3) --> 3 padding bits
0x81, 0x01,        //   Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x05, 0x01,        //   Usage Page (Generic Desktop Ctrls)
0x25, 0x07,        //   Logical Maximum (7)
0x46, 0x3B, 0x01,  //   Physical Maximum (315)
0x75, 0x04,        //   Report Size (4)
0x95, 0x01,        //   Report Count (1) --> 1 report 4 bits
0x65, 0x14,        //   Unit (System: English Rotation, Length: Centimeter)
0x09, 0x39,        //   Usage (Hat switch)
0x81, 0x42,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,Null State)

0x65, 0x00,        //   Unit (None)
0x95, 0x01,        //   Report Count (1) --> Padding 1 report 4 bits
0x81, 0x01,        //   Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x26, 0xFF, 0x00,  //   Logical Maximum (255)
0x46, 0xFF, 0x00,  //   Physical Maximum (255)
0x09, 0x30,        //   Usage (X)
0x09, 0x31,        //   Usage (Y)
0x09, 0x32,        //   Usage (Z)
0x09, 0x35,        //   Usage (Rz)
0x75, 0x08,        //   Report Size (8)
0x95, 0x04,        //   Report Count (4) --> 4 reports, 8 bits each
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x06, 0x00, 0xFF,  //   Usage Page (Vendor Defined 0xFF00)
0x09, 0x20,        //   Usage (0x20)
0x09, 0x21,        //   Usage (0x21)
0x09, 0x22,        //   Usage (0x22)
0x09, 0x23,        //   Usage (0x23)
0x09, 0x24,        //   Usage (0x24)
0x09, 0x25,        //   Usage (0x25)
0x09, 0x26,        //   Usage (0x26)
0x09, 0x27,        //   Usage (0x27)
0x09, 0x28,        //   Usage (0x28)
0x09, 0x29,        //   Usage (0x29)
0x09, 0x2A,        //   Usage (0x2A)
0x09, 0x2B,        //   Usage (0x2B)
0x95, 0x0C,        //   Report Count (12) --> 12 reports, 8 bits each?
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)

0x0A, 0x21, 0x26,  //   Usage (0x2621)
0x95, 0x08,        //   Report Count (8) --> 8 reports, 8 bits each?
0xB1, 0x02,        //   Feature (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile)
0x0A, 0x21, 0x26,  //   Usage (0x2621)
0x91, 0x02,        //   Output (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile)

0x26, 0xFF, 0x03,  //   Logical Maximum (1023)
0x46, 0xFF, 0x03,  //   Physical Maximum (1023)
0x09, 0x2C,        //   Usage (0x2C)
0x09, 0x2D,        //   Usage (0x2D)
0x09, 0x2E,        //   Usage (0x2E)
0x09, 0x2F,        //   Usage (0x2F)
0x75, 0x10,        //   Report Size (16)
0x95, 0x04,        //   Report Count (4) --> 4 reports, 16 bits each
0x81, 0x02,        //   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
0xC0,              // End Collection

// 137 bytes
```

**NOTE #4**: The USB HID Descriptor Report above is different compared to the case when using the RaspberryPi Zero!

### USB HID Report on a RP2350 based board

Based on the findings and notes above, see NOTE #1-#4, there was no explicit way to identify the meaning of the bits in the actual HID report using the report descriptor.

However, a simple code as below can read and display the bytes in the received report:

```
dev=usb.core.find(idVendor=0x2563, idProduct=0x0575)
dev.set_configuration()
time.sleep(0.1)

buf = array.array("B", [0] * 15)
report_count = 0
while True:
    try:
        count = dev.read(0x81, buf, timeout=1000)
    except usb.core.USBTimeoutError:
        print("USBTimeout")
        continue
    except usb.core.USBError:
        print("USBError")
        continue

    report_count += 1
    print(f"{report_count} >>> {buf}")
    time.sleep(0.01)
```

By means of trial-and-error, I identified three (3) types of different reports which are generated, depending on the operating 'mode' of the Game Pad controller.

**NOTE #5**: The PiHut Wireless USB Game Controller can be switched between 3 different operating 'modes' by using a key press combination of the Analog button and the Right Stick (see below). I was not able to identify these 'modes' in the HID Report Descriptor information directly and excplicitly (it is very likey that these are vendor specific). 

**NOTE #6** The current version of the [pihutwugc](./pihutwugc.py) implements the API only for operating mode 0.

In the description below I used the PiHut button names as listed for the [Approximate Engineering](https://approxeng.github.io/approxeng.input/simpleusage.html#standard-names) implementation.

Identified operating modes:
1) Game Pad outputs 15 bytes when in 'mode 0', activated at start-up/reset
```
    array('B', [0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    buf[0]: Dummy = 0
    buf[1]: Dummy = 20
    buf[2]: 1 = DPad Up, 2 = DPad Down, 4 = DPad Left, 8 = DPad Right, 16 = Start, 32 = Select
    buf[3]: 1 = L1 Trigger, 2 = R1 Trigger, 4 = Analog, 16 = Cross, 32 = Circle, 64 = Square, 128 = Triangle
    buf[4]: 0-255 L2 Trigger
    buf[5]: 0-255 R2 Trigger
    buf[6-9]: Left Stick : 0/255 = Center
      buf[6] = 255 when buf[7] = 127, 0 = otherwise
      buf[7] = 0 - 127 RIGHT, 255 - 128 LEFT  
      buf[8] = 255 when buf[9] = 127, 0 = otherwise
      buf[9] = 0 - 127 UP, 255 - 128 DOWN   
    buf[10-13]: Right Stick: 0/255 = Center
      Same as Left Stck
    buf[14]: Dummy = 0
```

2) Game Pad outputs 15 bytes when in 'mode 1' activated after with press on Analog + Right Stick UP x 7 times, then switching Analog OFF
```
    array('B', [0, 0, 15, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0])
    buf[0]: 1 = Right Stick Up (N) or Triangle, 2 = Right Stick Right (E) or Circle, 4 = Right Stick Down (S) or Cross, 8 = Right Stick Left (W) or Square; 
            3,6,12,9 = Right Stick NE, SE, SW, NW; 
            16 = L1 Trigger, 32 = R1 Trigger, 64 = L2 Trigger, 128 = R2 Trigger
    buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
    buf[2]: Dummy = 15
    buf[3-4]: Left Stick: 128 = Center, 0 = Left, 255 = Right, 0 = Up, 255 = Down
    buf[5-6]: Dummy = 128
    buf[7]: 0-255 = DPad Right
    buf[8]: 0-255 = DPad Left
    buf[9]: 0-255 = DPad Up
    buf[10]: 0-255 = DPad Down
    buf[11]: 0-255 = Triangle
    buf[12]: 0-255 = Circle
    buf[13]: 0-255 = Cross
    buf[14]: 0-255 = Square
```

3) Game Pad outputs 15 bytes when in 'mode 2' activated with press Analog + Right Stick UP x 7 times, then switching Analog ON
```
    array('B', [0, 0, 15, 127, 127, 127, 127, 0, 0, 0, 0, 0, 0, 0, 0])
    buf[0]: 1 = Triangle, 2 =  Circle, 4 = Cross, 8 = Square;
            16 = L1 Trigger, 32 = R1 Trigger, 64 = L2 Trigger, 128 = R2 Trigger
    buf[1]: 1 = Select, 2 = Start, 16 = Analog, 32 = Turbo
    buf[2]: 15 = No press, 0 = DPad Up, 2 = DPad Right, 4 = DPad Down, 6 = DPad Left
    buf[3-4]: Left Stick: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
    buf[5-6]: Right Stick: 127 = Center, 0-127 = Up, 127-255 = Down, 0-127 = Left, 127-255 = Right
    buf[7]: 0-255 = DPad Right 
    buf[8]: 0-255 = DPad Left 
    buf[9]: 0-255 = DPad Up 
    buf[10]: 0-255 = DPad Down 
    buf[11]: 0-255 = Triangle
    buf[12]: 0-255 = Circle
    buf[13]: 0-255 = Cross
    buf[14]: 0-255 = Square
```