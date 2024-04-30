import sys
import binascii

import time
import logging
import os
from collections import namedtuple
import numpy as np
import chipwhisperer as cw
from tqdm.notebook import trange

import external.nxpprog as nxpprog
import time

class CWDevice(nxpprog.NXPSerialDevice):
    def __init__(self, scope, target, print_debug=False):
        '''Add connection to ChipWhisperer'''
        self.scope = scope
        self.target = target
        self.debug = print_debug
        
    def isp_mode(self):
        '''Enter ISP Mode by reseting + pulling pin'''
        self.scope.io.nrst = 'low'
        time.sleep(0.01)
        self.scope.io.nrst = 'high'
        self.target.ser.flush()

    def write(self, data):
        '''Write data to serial port'''
        if self.debug:
            print("Write: " + str(data))
        self.target.ser.write(data)
        time.sleep(0.05) #work-around for CW serial port buffer on TX problem

    def readline(self, timeout=None):
        '''Read line from serial port, trying for timeout seconds'''
        if timeout is None:
            timeout = 5000
        else:
            timeout = int(timeout * 1000)

        line = ''
        while True:
            c = self.target.ser.read(1, timeout)
            if not c:
                break
            if c[0] == '\r':
                if not line:
                    continue
                else:
                    break
            if c[0] == '\n':
                if not line:
                    continue
                else:
                    break
            line += c
        
        if self.debug:
            print("Read: " + str(line))
        return line

def set_crp(nxpp, value, image=None):
    """
    Set CRP value - requires the first 4096 bytes of FLASH due to
    page size!
    """
    
    if image is None:
        f = open(r"external/lpc1114_first4096.bin", "rb")
        image = f.read()
        f.close()
    
    image = list(image)
    image[0x2fc] = (value >> 0)  & 0xff
    image[0x2fd] = (value >> 8)  & 0xff
    image[0x2fe] = (value >> 16) & 0xff
    image[0x2ff] = (value >> 24) & 0xff

    print("Programming flash...")
    nxpp.prog_image(bytes(image), 0)
    print("Done!")


def capture_crp(nxpdev, value, num_tries=1000, bypass_oserror=True):
    """
    Capture an average power trace for a given CRP level.
    """
    ref_list = []
    nxpdev.isp_mode()
    nxpp = nxpprog.NXP_Programmer("lpc1114", nxpdev, 12000)    
    try:
        set_crp(nxpp, value)
    except IOError as e:
        print("IOError - assumed CRP enabled. Error: " + str(e))
    scope.io.target_pwr = False
    time.sleep(0.2)
    scope.io.target_pwr = True
    time.sleep(0.2)

    print("Performing DPA capture for %04x"%value)
    for i in range(0, num_tries):
        scope.io.nrst = 'low'
        scope.arm()
        scope.io.nrst = 'high'

        scope.capture()

        ref_list.append(scope.get_last_trace())
        
    return np.mean(ref_list, axis=0) 