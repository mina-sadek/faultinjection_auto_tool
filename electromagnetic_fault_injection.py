import time
import os

class electromagnetic_fault_injection():
    def __init__(self, _interface_option, _device_option, _reset_option):
        self.interface_option = _interface_option
        self.device_option = _device_option
        self.reset_option = _reset_option

    def run(self):
        print('electromagnetic_fault_injection_run')

