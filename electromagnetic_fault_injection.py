import time
import os

# Define the initial minimum, maximum, and step values
offset_min  = 100
offset_max  = 10000
offset_step = 10
width_min   = 100
width_max   = 10000
width_step  = 10

class electromagnetic_fault_injection():
    def __init__(self, _interface_option, _device_option, _reset_option, _off_min = offset_min, _off_max = offset_max, _off_step = offset_step, _wid_min = width_min, _wid_max = width_max, _wid_step = width_step):
        self.interface_option = _interface_option
        self.device_option = _device_option
        self.reset_option = _reset_option
        self.offset_min  = _off_min
        self.offset_max  = _off_max
        self.offset_step = _off_step
        self.width_min   = _wid_min
        self.width_max   = _wid_max
        self.width_step  = _wid_step

    ## Function to reboot the Target MCU
    def reboot_flush(self, _reset_option):
        if _reset_option == 'vdd':
            emfi.target_pwr = False # Switch off the device
            # Wait for the capacitors to be discharged
            # Delay Before Powering up the Target
            time.sleep(0.1)
            emfi.arm()
            emfi.target_pwr = True # Switch on the device
        elif _reset_option == 'rst':
            emfi.nrst = 'low'
            time.sleep(0.1)
            emfi.arm()
            emfi.nrst = 'high_z'

    def run(self):
        print('electromagnetic_fault_injection_run')

        # Create the lists using list comprehensions
        self.offset = [self.offset_min + i * self.offset_step for i in range((self.offset_max - self.offset_min) // self.offset_step + 1)]
        self.width = [self.width_min + i * self.width_step for i in range((self.width_max - self.width_min) // self.width_step + 1)]

        # # Combine the lists into a dictionary
        # self.glitch_settings = {'offset': self.offset, 'width': self.width}
        # print(self.glitch_settings)

        fulllog_fn = 'logs/log-' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
        for self.glitch_setting_offset in self.offset:
            for self.glitch_setting_width in self.width:
                print('offset: ' + str(self.glitch_setting_offset) + ' | width: ' + str(self.glitch_setting_width))
                timestr = time.strftime("%Y%m%d-%H%M%S")
                dumpfilename = 'logs/' + self.device_option + '_flashDump' + timestr + '.bin'
                openocd_str = 'openocd -f ./openocd/' + self.device_option + '_' + self.interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x0 0x80000;exit"'
                print('dumpfilename: ' + dumpfilename)
                print('openocd_str: ' + openocd_str)
            
                # Reboot the Target & arm the PicoEMP
                self.reboot_flush(self.reset_option)
                time.sleep(self.glitch_setting_offset)
                exit_status = os.system(openocd_str)
                fulllog = open(fulllog_fn, 'a')
                fulllog.write(openocd_str + "\n")
                print(f"ext_offset: {self.scope.glitch.ext_offset}, repeat: {self.scope.glitch.repeat}")
                print("exit_status: " + str(exit_status))
                print("*-----------------------------------*")
                if exit_status == 0:
                    print("SUCCESS")
                    filename = 'log-' + timestr + '.txt'
                    f = open(filename, 'a')
                    f.write(f"SUCCESS Paramters: width: {self.glitch_setting_width}, offset: {self.glitch_setting_offset}\n")
                    f.close()
                    fulllog.write(f"SUCCESS Paramters: width: {self.glitch_setting_width}, offset: {self.glitch_setting_offset}\n")
                    fulllog.close()
                    break
                else:
                    os.system('rm ' + dumpfilename)
                # Reset the glitching module. Things break if you don't do this.
                time.sleep(0.05)
                self.vglitch_reset(self.scope)




