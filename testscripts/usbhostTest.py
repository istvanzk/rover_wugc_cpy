# USB Host Test for the PiHut Wireless USB Game Controller in CircuitPython
#
# Prints USB device information for all connected devices.
#
# Based on:
# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
# SPDX-License-Identifier: Unlicense
# https://learn.adafruit.com/adafruit-feather-rp2040-with-usb-type-a-host/usb-host-device-info-2

import time
import usb.core
import usb_host
import board

import adafruit_usb_host_descriptors

DIR_IN = 0x80

# dir(board) for Challenger+ RP2350 WiFi6/BLE5 (https://ilabs.se/product/challenger-rp2350-wifi-ble/)
#['__class__', '__name__', 'A0', 'A1', 'A2', 'A3', 
# 'ESP_BOOT', 'ESP_CS', 'ESP_DRDY', 'ESP_HS', 'ESP_MISO', 'ESP_MOSI', 'ESP_RESET', 'ESP_RX', 'ESP_SCK', 'ESP_TX', 
# 'GP0', 'GP1', 'GP10', 'GP11', 'GP12', 'GP13', 'GP14', 'GP15', 'GP16', 'GP17', 'GP18', 'GP19', 'GP2', 'GP20', 'GP21', 'GP22', 'GP23', 'GP24', 'GP25', 'GP26', 'GP27', 'GP28', 'GP29', 'GP3', 'GP4', 'GP5', 'GP6', 'GP7', 'GP8', 'GP9', 
# 'I2C', 'LED', 'MISO', 'MOSI', 'RX', 'SCK', 'SCL', 'SDA', 'SPI', 'SS', 'TX', 'UART', 
# '__dict__', 'board_id']

# Create a port to use for the USB host.
# Correspond to TX and RX on JP2 connector.
try:
    usb_host.Port(board.GP12, board.GP13)
except:
    print("USB Port already created")
time.sleep(0.1)

while True:
    print("searching for devices")   
    for device in usb.core.find(find_all=True):
        # pid 0x575
        # vid 0x2563
        # man Nintendo Co., Ltd.
        # product Pro Controller
        # serial None
        # config[0]:
        #   value 1
        #   interface[0]
        #       class 03 subclass 00
        #       IN 81
        #       OUT 02
        print("pid", hex(device.idProduct))
        print("vid", hex(device.idVendor))
        print("man", device.manufacturer)
        print("product", device.product)
        print("serial", device.serial_number)
        print("config[0]:")
        config_descriptor = adafruit_usb_host_descriptors.get_configuration_descriptor(
            device, 0
        )

        i = 0
        while i < len(config_descriptor):
            descriptor_len = config_descriptor[i]
            descriptor_type = config_descriptor[i + 1]
            if descriptor_type == adafruit_usb_host_descriptors.DESC_CONFIGURATION:
                config_value = config_descriptor[i + 5]
                print(f"  number of interfaces {config_descriptor[i + 3]:d}")
                print(f"  configuration value {config_value:d}")
            elif descriptor_type == adafruit_usb_host_descriptors.DESC_INTERFACE:
                interface_number = config_descriptor[i + 2]
                interface_class = config_descriptor[i + 5]
                interface_subclass = config_descriptor[i + 6]
                print(f"  interface[{interface_number:d}]")
                print(
                    f"    class {interface_class:02x} subclass {interface_subclass:02x}"
                )
            elif descriptor_type == adafruit_usb_host_descriptors.DESC_ENDPOINT:
                endpoint_address = config_descriptor[i + 2]
                if endpoint_address & DIR_IN:
                    print(f"    IN {endpoint_address:02x}")
                else:
                    print(f"    OUT {endpoint_address:02x}")
            i += descriptor_len
        print()
    time.sleep(5)
