# A very basic class to interact with the ChipShouter PicoEMP

import time
import serial

class ChipShouterPicoEMP:
    def __init__(self, port='/dev/ttyACM1'):
        self.pico = serial.Serial(port, 115200)
        
        self.pico.write(b'\r\n')
        time.sleep(0.1)
        ret = self.pico.read(self.pico.in_waiting)
        
        if b'PicoEMP Commands' in ret:
            print('Connected to ChipSHOUTER PicoEMP!')
        else:
            raise OSError('Could not connect to ChipShouter PicoEMP :(')
        

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
