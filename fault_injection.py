
import time
import serial
import os
import argparse
# import electromagnetic_fault_injection as emfi
import emfi2 as emfi
import voltage_fault_injection as vfi

import tkinter as tk
from tkinter import ttk
# from fault_injection import fault_injection
import sys
import io
import threading
import queue
import time
import signal
import multiprocessing

# Voltage Fault Injection against nRF52833:
# python fault_injection.py -i jlink -d nrf52833 -r vdd -a vfi
# Voltage Fault Injection against nRF52840:
# python fault_injection.py -i jlink -d nrf52840 -r vdd -a vfi
# Voltage Fault Injection against LPC1343:
# python fault_injection.py -i cwLite -d lpc1343 -r rst -a vfi
# Electromagnetic Fault Injection against lpc1343:
# python fault_injection.py -i cwLite -d lpc1343 -r rst -a emfi

# For locking the lpc1343 Device:
# python fault_injection.py -i cwLite -d lpc1343 -a lck

# STM32F1xx Voltage Fault Injection
# https://habr.com/ru/companies/ntc-vulkan/articles/483732/

# Sample items for the dropdown menus
interfaces = ['cwLite', 'jlink', 'stlink']
devices = ['lpc1343', 'nrf52840', 'nrf52833', 'stm32']
resets = ['rst', 'vdd']
attacks = ['vfi', 'emfi', 'lck']


def parse_arguments():
    """Parse command-line arguments."""
    # Create argument parser
    parser = argparse.ArgumentParser(description="Script with input parameters -i, -d, and an optional -a")
    parser.add_argument("-i", choices=interfaces, help="Choose between 'link', 'stlink' and 'cwLite'", required=True)
    parser.add_argument("-d", choices=devices, help="Choose between 'nrf52840', 'nrf52833', 'stm32' and 'NXP lpc1343'", required=True)
    parser.add_argument("-r", choices=resets, help="Choose between 'VDD: Control Target's VDD Line' and 'RST: Control Target's RESET pin' - Default is 'vdd'")
    parser.add_argument("-a", choices=attacks, help="Choose between 'Voltage Fault Injection Glitch' and 'ElectroMagnetic Fault Injection Glitch' or 'Lock attacked lpc1343 chip' - Default is 'vfi'")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    # parser.add_argument("-f", choices=['dap', 'is'], help="Choose between 'Debug Access Port (DAP) protection bypass' and 'Instruction Skipping' - Default is 'dap'")
    # Parse the arguments & return
    return parser.parse_args()

def main_cli():
    # Pare input arguments & Prepare required links
    args = parse_arguments()

    # Access the arguments
    interface_option = args.i
    device_option = args.d
    reset_option = args.r
    attack_option = args.a
    # fault_option = args.f
    verbose_option = args.verbose

    # Check if both options are provided
    if interface_option is None or device_option is None:
        print("Both -i and -d parameters are required.")
        return

    # Print chosen options
    # print("Chosen interface option:", interface_option)
    # print("Chosen target option:", device_option)
    if not reset_option:
        reset_option = 'vdd'
        print("Default reset type:", reset_option)
    # else:
    #     print("Chosen reset type:", reset_option)
    if not attack_option:
        attack_option = 'vfi'
        print("Default attack type:", attack_option)
    # else:
    #     print("Chosen attack type:", attack_option)
    
    if not (verbose_option):
        verbose_option = False

    fault_injection(interface_option, device_option, reset_option, attack_option, verbose_option)

def fault_injection(interface_option, device_option, reset_option, attack_option, verbose_option):
    # Your existing logic goes here
    print("Selected Runtime Parameters:")
    print(f"Interface: {interface_option}")
    print(f"Device: {device_option}")
    print(f"Reset: {reset_option}")
    print(f"Attack: {attack_option}")
    print(f"Verbose: {verbose_option}")
    # Simulate some processing
    # for i in range(5):
    #     print(f"Processing item {i+1}...")
    #     # Replace this with your actual logic

    if attack_option == 'emfi':
        # _emfi = emfi.electromagnetic_fault_injection(interface_option, device_option, reset_option, 100, 1000, 10, 100, 110, 10)
        # _emfi = emfi.electromagnetic_fault_injection(interface_option, device_option, reset_option, 4500, 5500, 1, 100, 101, 1) # No width control
        # _emfi = emfi.electromagnetic_fault_injection(interface_option, device_option, reset_option, 4880, 4910, 1, 100, 101, 1) # No width control
        # _emfi = emfi.electromagnetic_fault_injection(interface_option, device_option, reset_option, 4800, 5000, 1, 100, 101, 1) # No width control
        # Timings are in nanoseconds
        _emfi = emfi.emfi(interface_option, device_option, reset_option, verbose_option, (48900-1100), (49000-1100), 10, (1000+200), (2000+200), 10) # No width control
        _emfi.run()
    elif attack_option == 'vfi':
        _vfi = vfi.voltage_fault_injection(interface_option, device_option, reset_option, verbose_option)
        _vfi.run()
    elif attack_option == 'lck':
        _vfi = vfi.voltage_fault_injection(interface_option, device_option, reset_option, verbose_option)
        _vfi.target_lock()

class RedirectStdout(io.StringIO):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def write(self, text):
        super().write(text)
        self.queue.put(text)

def main_gui():
    def GUI_start_function():
        global process
        global output_queue
        output_queue = multiprocessing.Queue()

        global stop_execution
        stop_execution = False
        # Disable the start button to prevent multiple clicks
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)

        # Retrieve values from dropdowns
        selected_values = [var.get() for var in dropdown_vars]
        verbose = verbose_var.get()

        output_text.delete(1.0, tk.END)  # Clear previous output
        # threading.Thread(target=GUI_fault_injection_run, args=(selected_values, verbose)).start()

        # # Create a queue to communicate with the GUI thread
        # output_queue = queue.Queue()
        # # Start the fault_injection in a new thread
        # threading.Thread(target=GUI_fault_injection_run, args=(selected_values, verbose, output_queue)).start()

        # Start the fault_injection in a new process
        process = multiprocessing.Process(target=GUI_fault_injection_run, args=(selected_values, verbose, output_queue))
        process.start()

        # Start the process to update the text widget periodically
        root.after(100, GUI_update_output, output_queue)
    
    def stop_function():
        global stop_execution
        stop_execution = True
        stop_button.config(state=tk.DISABLED)
        # # Simulate a Ctrl+C interrupt
        # os.kill(os.getpid(), signal.SIGINT)

        if process.is_alive():
            process.terminate()
            process.join()
            output_queue.put("Execution stopped by user.\n")
            # Re-enable the start button after stopping
            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)
        
    def exit_function():
        if process.is_alive():
            process.terminate()
            process.join()
        root.quit()

    def GUI_fault_injection_run(selected_values, verbose, output_queue):
        # Redirect stdout to capture the function output
        redirect_stdout = RedirectStdout(output_queue)
        old_stdout = sys.stdout
        sys.stdout = redirect_stdout
        try:
            # Call the fault_injection function with selected values
            fault_injection(*selected_values, verbose)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Reset stdout
            sys.stdout = old_stdout
            # Signal that the function is done
            output_queue.put(None)

    def GUI_update_output(output_queue):
        try:
            while True:
                line = output_queue.get_nowait()
                if line is None:
                    # Re-enable the start button after function execution
                    start_button.config(state=tk.NORMAL)
                    stop_button.config(state=tk.DISABLED)
                    return
                output_text.insert(tk.END, line)
                output_text.see(tk.END)  # Auto-scroll to the end
        except queue.Empty:
            pass
        # Check the queue again after 100 ms
        root.after(100, GUI_update_output, output_queue)

    # def GUI_update_output(output_queue):
    #     while not output_queue.empty():
    #         line = output_queue.get_nowait()
    #         if line is None:
    #             # Re-enable the start button after function execution
    #             start_button.config(state=tk.NORMAL)
    #             return
    #         output_text.insert(tk.END, line + "\n")
    #         output_text.see(tk.END)  # Auto-scroll to the end

    #     # Check the queue again after 100 ms
    #     root.after(100, GUI_update_output, output_queue)

    def GUI_append_text(output):
        output_text.insert(tk.END, output)
        output_text.see(tk.END)  # Auto-scroll to the end

    # Create the main window
    root = tk.Tk()
    root.title("Fault Injection Automation Tool | EG|CERT - R&T Solutions Dept.")
    root.geometry("3000x2000")  # Set the window size

    # Create variables for the dropdown menus
    dropdown_vars = [
        tk.StringVar(value=interfaces[0]),
        tk.StringVar(value=devices[0]),
        tk.StringVar(value=resets[0]),
        tk.StringVar(value=attacks[0])
    ]

    # Style configuration
    style = ttk.Style()
    style.configure('TLabel', font=('Helvetica', 14))
    style.configure('TButton', font=('Helvetica', 14))
    style.configure('TCombobox', font=('Helvetica', 14))
    style.configure('TCheckbutton', font=('Helvetica', 14))

    # Create dropdown menus
    ttk.Label(root, text="Interface:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ttk.Combobox(root, textvariable=dropdown_vars[0], values=interfaces, state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    ttk.Label(root, text="Target Device:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ttk.Combobox(root, textvariable=dropdown_vars[1], values=devices, state="readonly").grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    ttk.Label(root, text="Reset Option:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ttk.Combobox(root, textvariable=dropdown_vars[2], values=resets, state="readonly").grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    ttk.Label(root, text="Attack Type:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    ttk.Combobox(root, textvariable=dropdown_vars[3], values=attacks, state="readonly").grid(row=3, column=1, padx=10, pady=10, sticky="ew")

    # Add a checkbox for verbose mode
    verbose_var = tk.BooleanVar()
    # ttk.Checkbutton(root, text="Verbose?", variable=verbose_var).grid(row=4, column=0, padx=10, pady=10, sticky="e")
    ttk.Checkbutton(root, text="Verbose?", variable=verbose_var).grid(row=4, columnspan=2, padx=10, pady=10, sticky="w")


    # # Create dropdown menus
    # ttk.Label(root, text="Interface:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    # ttk.Combobox(root, textvariable=dropdown_vars[0], values=interfaces).grid(row=0, column=1, padx=10, pady=5)
    # ttk.Label(root, text="Device:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    # ttk.Combobox(root, textvariable=dropdown_vars[1], values=devices).grid(row=1, column=1, padx=10, pady=5)
    # ttk.Label(root, text="Reset:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    # ttk.Combobox(root, textvariable=dropdown_vars[2], values=resets).grid(row=2, column=1, padx=10, pady=5)
    # ttk.Label(root, text="Attack:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    # ttk.Combobox(root, textvariable=dropdown_vars[3], values=attacks).grid(row=3, column=1, padx=10, pady=5)

    # # Add a checkbox for verbose mode
    # verbose_var = tk.BooleanVar()
    # ttk.Checkbutton(root, text="Verbose", variable=verbose_var).grid(row=4, columnspan=2, padx=10, pady=5)

    # Create and place the buttons
    # start_button = tk.Button(root, text="Start Fault Injection Attack", command=GUI_start_function)
    # # start_button.grid(row=5, columnspan=2, padx=10, pady=10)
    # start_button.grid(row=5, columnspan=2, padx=10, pady=20)

    # Create and place the buttons
    start_button = ttk.Button(root, text="Start Fault Injection Attack", command=GUI_start_function)
    start_button.grid(row=5, columnspan=2, padx=10, pady=20)

    stop_button = ttk.Button(root, text="Stop Execution", command=stop_function, state=tk.DISABLED)
    stop_button.grid(row=6, columnspan=2, padx=10, pady=20)

    exit_button = ttk.Button(root, text="Exit", command=exit_function)
    exit_button.grid(row=7, columnspan=2, padx=10, pady=20)

    # Create and place the text widget for displaying terminal output
    output_text = tk.Text(root, height=20, width=80, wrap=tk.WORD, font=("Helvetica", 12))
    output_text.grid(row=8, columnspan=2, padx=10, pady=10, sticky="nsew")

    # Configure grid to make the text widget expandable
    root.grid_rowconfigure(8, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # # Create and place the text widget for displaying terminal output
    # output_text = tk.Text(root, height=20, width=80, wrap=tk.WORD, font=("Helvetica", 12))
    # output_text.grid(row=6, columnspan=2, padx=10, pady=10, sticky="nsew")

    # # Configure grid to make the text widget expandable
    # root.grid_rowconfigure(6, weight=1)
    # root.grid_columnconfigure(1, weight=1)

    # # Create and place the text widget for displaying terminal output
    # output_text = tk.Text(root, height=20, width=80, wrap=tk.WORD, font=("Helvetica", 14))
    # output_text.grid(row=6, columnspan=2, padx=10, pady=10, sticky="nsew")
    # # # Create and place the text widget for displaying terminal output
    # # output_text = tk.Text(root, height=10, width=50)
    # # output_text.grid(row=6, columnspan=2, padx=10, pady=10)

    # # Configure grid to make the text widget expandable
    # root.grid_rowconfigure(6, weight=1)
    # root.grid_columnconfigure(1, weight=1)

    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    # main()
    # if len(sys.argv) == 1:
    if len(sys.argv) < 2:
        main_gui()
    else:
        main_cli()




# def start_function():
#     # Retrieve values from dropdowns
#     selected_values = [var.get() for var in dropdown_vars]
#     verbose = verbose_var.get()

#     # Redirect stdout to capture the function output
#     old_stdout = sys.stdout
#     sys.stdout = mystdout = io.StringIO()

#     # Call the fault_injection function with selected values
#     # fault_injection(*selected_values, verbose)
#     for i in range(1, 100000000):
#         print("hellooooooo")

#     # Reset stdout
#     sys.stdout = old_stdout

#     # Display function output in the text widget
#     output_text.delete(1.0, tk.END)
#     output_text.insert(tk.END, mystdout.getvalue())
#     output_text.see(tk.END)  # Auto-scroll to the end


# # Create the main window
# root = tk.Tk()
# root.title("Python GUI with Dropdowns and Terminal Output")

# # Create variables for the dropdown menus
# dropdown_vars = [tk.StringVar(value=interfaces[0]), tk.StringVar(value=devices[0]), 
#                  tk.StringVar(value=resets[0]), tk.StringVar(value=attacks[0])]

# # Create dropdown menus
# ttk.Label(root, text="Interface:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
# ttk.Combobox(root, textvariable=dropdown_vars[0], values=interfaces).grid(row=0, column=1, padx=10, pady=5)
# ttk.Label(root, text="Device:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
# ttk.Combobox(root, textvariable=dropdown_vars[1], values=devices).grid(row=1, column=1, padx=10, pady=5)
# ttk.Label(root, text="Reset:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
# ttk.Combobox(root, textvariable=dropdown_vars[2], values=resets).grid(row=2, column=1, padx=10, pady=5)
# ttk.Label(root, text="Attack:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
# ttk.Combobox(root, textvariable=dropdown_vars[3], values=attacks).grid(row=3, column=1, padx=10, pady=5)

# # Add a checkbox for verbose mode
# verbose_var = tk.BooleanVar()
# ttk.Checkbutton(root, text="Verbose", variable=verbose_var).grid(row=4, columnspan=2, padx=10, pady=5)

# # Create and place the text widget for displaying terminal output
# output_text = tk.Text(root, height=10, width=50)
# output_text.grid(row=6, columnspan=2, padx=10, pady=10)

# # Create and place the button
# start_button = tk.Button(root, text="Start Function", command=start_function)
# start_button.grid(row=5, columnspan=2, padx=10, pady=10)

# # Start the main event loop
# root.mainloop()