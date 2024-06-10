# A very basic class to interact with the ChipShouter PicoEMP

import time
import serial
from serial.tools import list_ports

class ChipShouterPicoEMP:
    # def __init__(self, port='/dev/ttyACM1'):
    #     self.pico = serial.Serial(port, 115200)
        
    #     self.pico.write(b'\r\n')
    #     time.sleep(0.1)
    #     ret = self.pico.read(self.pico.in_waiting)
        
    #     if b'PicoEMP Commands' in ret:
    #         print('Connected to ChipSHOUTER PicoEMP!')
    #     else:
    #         raise OSError('Could not connect to ChipShouter PicoEMP :(')
        
    def __init__(self, port=None):
        is_picoemp_reset = 0
        port = self.find_serial_port()
        # Initial connection to the found serial port
        self.ser = serial.Serial(port, 115200)
        # Send a reset request
        if (is_picoemp_reset == 0):
            self.pico_emp_reset(self.ser)
            is_picoemp_reset = 1

        # Find the PicoEMP serial port after reset
        port = self.find_serial_port()
        self.pico = serial.Serial(port, 115200)
        # Making sure the connected device is PicoEMP        
        self.pico.write(b'\r\n')
        time.sleep(0.1)
        ret = self.pico.read(self.pico.in_waiting)
        
        if b'PicoEMP Commands' in ret:
            # print('Connected to ChipSHOUTER PicoEMP!')
            print('INFO: Found ChipSHOUTER PicoEMP 😍')
        else:
            raise OSError('Could not connect to ChipShouter PicoEMP :(')

    def pico_emp_reset(self, port):
        # Reset the connected PicoEMP
        port.write(('r' + '\r\n').encode())

        port.flush()
        time.sleep(0.1)
        port.close()
        port = None
        time.sleep(2)

    def find_serial_port(self):
        # Reconnecting to the PicoEMP after reset
        print('Searching for a connected Serial Port')
        serial_found = 0
        # Check for a connected serial port for 1 second
        for i in range(0, 1000):
            serial_port = self.find_serial_port_basic()
            if serial_port:
                serial_found = 1
                print(f"Found serial port: {serial_port}")
                return serial_port
            else:
                i = i + 1
                time.sleep(0.001)
                continue
        if (serial_found == 0):
            print("picoEMP is not connected.\nNo serial ports found.\nPLEASE CONNECT THE picoEMP TO THE SERIAL PORT AND TRY AGAIN.")
            exit()

    def find_serial_port_basic(self):
        """Find an available serial port."""
        ports = list_ports.comports()
        for port in ports:
            if port.device.startswith('/dev/ttyUSB') or port.device.startswith('/dev/ttyS')  or port.device.startswith('/dev/ttyACM'):
                return port.device
        return None

    def disable_timeout(self):
        self.pico.write(b'disable_timeout\r\n')
        time.sleep(1)
        assert b'Timeout disabled!' in self.pico.read(self.pico.in_waiting)

        
    def arm(self):
        self.pico.write(b'arm\r\n')
        time.sleep(1)
        assert b'Device armed' in self.pico.read(self.pico.in_waiting)

        
    def disarm(self):
        self.pico.write(b'disarm\r\n')
        time.sleep(1)
        assert b'Device disarmed!' in self.pico.read(self.pico.in_waiting)

        
    def external_hvp(self):
        self.pico.write(b'external_hvp\r\n')
        time.sleep(1)
        assert b'External HVP mode active' in self.pico.read(self.pico.in_waiting)

        
    def print_status(self):
        self.pico.write(b'status\r\n')
        time.sleep(1)
        print(self.pico.read(self.pico.in_waiting).decode('utf-8'))
        
    
    def setup_external_control(self):
        self.disable_timeout()
        self.external_hvp()
        self.print_status()
