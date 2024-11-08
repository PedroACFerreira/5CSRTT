# 5CSRTT
Code for controlling an Open-Source Operant Chamber designed for the 5-Choice Serial Reaction Time Task test in mice.
This is currently a work in progress.

## Features

Software:
- GUI for easy operation
- Integrated excel-like tables to easily keep track of different experiments and cohorts
- Tab to set up input/outputs for GPIO devices
- Select specific animals to run and automatically have all relevant data registered accordingly
- Currently set up to work with MicroPython boards, but any GPIO device with enough ports can work

Operant Chamber hardware:
- Shift registers to control up to 12 light sources independently with few dedicated outputs
- Infrared sensors to trigger on nose pokes
- Circuit for linear actuator for reward delivery
- Lickometer
- Fish-eye/nightvision camera for animal tracking
- Easy integration of optogenetics/photometry equipment

## Operation

The GUI is coded using the Tkinter package, with some modifications to existing widgets. 
Circuitry operation will be done using MicroPython and a PyBoard. Requires external power supply.
Multiprocessing/threading cannot be easily used for behavior test execution due to USB ownership issues while using Windows OS. Migration to Linux might be necessary for more complex workflows.
Tables inside the interface are created using an adaptation of the tkintertables package.

## To Do

- Code specific behavioral tests using MicroPython for GPIO interfacing
- Add export to .xlsx functionality to GUI tables
- Add context menus for interface
- Polish aesthetics
- Fully comment code
