'''
A library that allows simple access to 74HC595 shift registers on a Raspberry Pi using any digital I/O pins.
'''
from board import *
from digitalio import *

# Define MODES
ALL  = -1
HIGH = 1
LOW  = 0


# is used to store states of all pins
_registers = list()

#How many of the shift registers - you can change them with shiftRegisters method
_number_of_shiftregisters = 2


def pinsSetup(**kwargs):
    '''
    Allows the user to define custom pins
    '''
    global _SER_pin, _RCLK_pin, _SRCLK_pin
    global SER, RCLK, SRCLK
    # Define pins
    _SER_pin = 0  # pin 14 on the 75HC595
    _RCLK_pin = 0  # pin 12 on the 75HC595
    _SRCLK_pin = 0  # pin 11 on the 75HC595

    if len(kwargs) >0:

        _SER_pin = kwargs.get('ser', _SER_pin)
        _RCLK_pin = kwargs.get('rclk', _RCLK_pin)
        _SRCLK_pin = kwargs.get('srclk', _SRCLK_pin)

    SER = DigitalInOut(_SER_pin)
    SER.direction = Direction.OUTPUT
    RCLK = DigitalInOut(_RCLK_pin)
    RCLK.direction = Direction.OUTPUT
    SRCLK = DigitalInOut(_SRCLK_pin)
    SRCLK.direction = Direction.OUTPUT


def startupMode(mode, execute = False):
    '''
    Allows the user to change the default state of the shift registers outputs
    '''
    if isinstance(mode, int):
        if mode is HIGH or mode is LOW:
            _all(mode, execute)
        else:
            raise ValueError("The mode can be only HIGH or LOW or Dictionary with specific pins and modes")
    elif isinstance(mode, dict):
        for pin, mode in mode.iteritems():
            _setPin(pin, mode)
        if execute:
            _execute()
    else:
        raise ValueError("The mode can be only HIGH or LOW or Dictionary with specific pins and modes")


def shiftRegisters(num):
    '''
    Allows the user to define the number of shift registers are connected
    '''
    global _number_of_shiftregisters
    _number_of_shiftregisters = num
    _all(LOW)

def digitalWrite(pin, mode):
    '''
    Allows the user to set the state of a pin on the shift register
    '''
    if pin == ALL:
        _all(mode)
    else:
        if len(_registers) == 0:
            _all(LOW)

        _setPin(pin, mode)
    _execute()

def delay(millis):
    '''
    Used for creating a delay between commands
    '''
    millis_to_seconds = float(millis)/1000
    return sleep(millis_to_seconds)

def _all_pins():
    return _number_of_shiftregisters * 8

def _all(mode, execute = True):
    all_shr = _all_pins()

    for pin in range(0, all_shr):
        _setPin(pin, mode)
    if execute:
        _execute()

    return _registers

def _setPin(pin, mode):
    try:
        _registers[pin] = mode
    except IndexError:
        _registers.insert(pin, mode)

def _execute():
    global SER, RCLK, SRCLK


    all_pins = _all_pins()
    RCLK.value = 0

    for pin in range(all_pins -1, -1, -1):
        SRCLK.value = 0

        pin_mode = _registers[pin]
        SER.value = pin_mode
        SRCLK.value = 1

    RCLK.value = 1

if __name__ == "__main__" or __name__ == "FCSRTT_FT235H.py":
    from board import *
    from digitalio import *
    from time import sleep

    pinsSetup(**{"ser": C2, "rclk": C1 , "srclk": C0})
    shiftRegisters(2)
    digitalWrite(ALL,1)
    sleep(0.5)
    digitalWrite(ALL,0)
    # for i in range(16):
    #     digitalWrite(i+1, 1)
    #     sleep(0.1)
    # for i in range(16):
    #     digitalWrite(i+1, 1)
    #     sleep(0.05)
    #     digitalWrite(i+1, 0)
    #     digitalWrite(i+1, 1)
    #     sleep(0.05)
    #     digitalWrite(i+1, 0)
    # digitalWrite(ALL,1)
    # sleep(0.5)
    # digitalWrite(ALL,0)
    # sleep(0.5)
    # digitalWrite(ALL,1)
    # sleep(0.5)
    # digitalWrite(ALL,0)

