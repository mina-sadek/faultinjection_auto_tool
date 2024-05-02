
import time
import serial
import os
import argparse
import electromagnetic_fault_injection as emfi
import voltage_fault_injection as vfi

# Voltage Fault Injection against nRF52833:
# python fault_injection.py -i jlink -d nrf52833 -r vdd -a vfi
# Voltage Fault Injection against nRF52840:
# python fault_injection.py -i jlink -d nrf52840 -r vdd -a vfi
# Voltage Fault Injection against LPC1343:
# python fault_injection.py -i cwLite -d lpc1434 -r rst -a vfi
# Electromagnetic Fault Injection against nRF52840:
# python fault_injection.py -i jlink -d nrf52840 -r rst -a emfi

def parse_arguments():
    """Parse command-line arguments."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Script with input parameters -i, -d, and an optional -a")
    parser.add_argument("-i", choices=['jlink', 'stlink', 'cwLite'], help="Choose between 'link', 'stlink' and 'cwLite'", required=True)
    parser.add_argument("-d", choices=['nrf52840', 'nrf52833', 'stm32', 'lpc1434'], help="Choose between 'nrf52840', 'nrf52833', 'stm32' and 'NXP lpc1434'", required=True)
    parser.add_argument("-r", choices=['vdd', 'rst'], help="Choose between 'VDD: Control Target's VDD Line' and 'RST: Control Target's RESET pin' - Default is 'vdd'")
    parser.add_argument("-a", choices=['vfi', 'emfi'], help="Choose between 'Voltage Fault Injection Glitch' and 'ElectroMagnetic Fault Injection Glitch' - Default is 'vfi'")
    # parser.add_argument("-f", choices=['dap', 'is'], help="Choose between 'Debug Access Port (DAP) protection bypass' and 'Instruction Skipping' - Default is 'dap'")
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
    # fault_option = args.f

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
    

    if attack_option == 'emfi':
        _emfi = emfi.electromagnetic_fault_injection(interface_option, device_option, reset_option, 100, 1000, 10, 100, 110, 10)
        _emfi.run()
    else:       # elif attack_option == 'vfi':
        _vfi = vfi.voltage_fault_injection(interface_option, device_option, reset_option)
        _vfi.run()

if __name__ == "__main__":
    main()