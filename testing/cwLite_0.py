# Main source: https://www.synacktiv.com/en/publications/how-to-voltage-fault-injection#secure_boot

import chipwhisperer as cw
import time

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

# Time Delays & initialization before glitch attack
time.sleep(0.05)
scope.default_setup()
print("CW_Lite Default Configuration applied.")
print("-------------------")
# m1
# ------------------------------

# We adjust the clock to fit with the ATMega 328p frequency.
scope.clock.clkgen_freq = 0.01E6 
# scope.clock.clkgen_freq = 16E6 # Arduino NANO uses 16 MHz clock

reboot_flush(scope)
scope.arm()
# scope.capture()



# scope.dis()
# mmmmmmm
# Set clock to internal chipwhisperer clock
scope.glitch.clk_src = "clkgen" # set glitch input clock

#"enable_only" - insert a glitch for an entire clock cycle based on the clock of the CW (here at 8MHz so 0,125 micro seconds)
scope.glitch.output = "enable_only"
# scope.glitch.output = "glitch_only" # glitch_out = clk ^ glitch
# scope.glitch.trigger_src = "ext_single" # glitch only after scope.arm() called

# Enable Low power and High power transistors.
if PLATFORM == "CWLITEXMEGA":
    scope.io.glitch_lp = True
    scope.io.glitch_hp = True
# LP provides a faster response, so sharper glitches. HP can provide better results for targets that have strong power supplies or decoupling capacitors that ca not be removed.

# scope.io.vglitch_reset() #it simply sets scope.io.glitch_hp/lp to False, waits delay seconds, then returns to their original settings. In short, reset the glitching module.
vglitch_reset(scope)

# How many times the glitch is repeated
# scope.glitch.repeat = 4

# Send the glitch
# scope.glitch.manual_trigger()


# How many times the glitch is repeated
scope.glitch.repeat = 10

# Send the glitch
scope.glitch.manual_trigger()

scope.dis()
print("Disconnect from CW_Lite .. Exiting")
exit()

# for i in range(380):
for i in range(50):
    # scope.io.vglitch_reset(0.5)
    vglitch_reset(scope, 0.5)
    scope.glitch.repeat = i+1
    scope.glitch.manual_trigger()

scope.dis()