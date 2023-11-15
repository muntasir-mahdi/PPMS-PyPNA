import time
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa
import MultiPyVu
import sys
import math

from MultiPyVu import MultiVuServer as mvs
from MultiPyVu import MultiVuClient as mvc
from MultiVuDataFile import MultiVuDataFile as mvd

rm = visa.ResourceManager() # Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries. 
myPna = rm.open_resource("GPIB1::16::INSTR")

host = "127.0.0.1"
port = 5000

def save_temp_field_chamber():
    T, sT = client.get_temperature()
    F, sF = client.get_field()
    C = client.get_chamber()
    print(f'{T:{7}.{3}f} {sT:{10}} {F:{7}} {sF:{20}} {C:{15}}')
# ========================================================= #

myPna.write("SYST:PRES; *OPC?")     # Preset the PNA and wait for preset completion via use of *OPC?
myPna.read()

myPna.write("*CLS")     # Clear the event status registers and empty the error queue

myPna.write("*IDN?")    # Query identification string *IDN?
print(myPna.read())

myPna.write("SYST:ERR?")    # Check the error queue
print(myPna.read())

# Start the server.
with mvs.MultiVuServer() as server:

    # start the client
    with mvc.MultiVuClient(host, port) as client:
        # Allow the connection to complete initialization
        time.sleep(5)
        
        #-------------Temp Status---------------------
        temperature, status = client.get_temperature()
        tempUnits = client.temperature.units
        print(f'\nTemperature = {temperature} {tempUnits}')
        
        #------------Field Status----------------------
        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')
        
        #------------Purge/Seal------------------------
        if temperature == 300 and field == 0:
            #Purge/Seal the chamber; wait to continue
            print('Change the chamber state to Purge/Seal')
            client.set_chamber(client.chamber.mode.purge_seal)
            client.wait_for(10, 0, client.subsystem.chamber)
        
        #---------------print a header----------------
        print('')
        hdr = '______ T ______     __________ H __________\t______ Chamber Status ______'
        print(hdr)

        #----------------------- Set Temperature-------------------------------------
        CurrentTemp, sT = client.get_temperature()
        #points = 10
        
        setpoint = 1.7 #1.7 K Setpoint
        rate = 50
        
        wait = abs(CurrentTemp-setpoint)/rate*60
        message = f'Set the temperature {setpoint} K at {rate} K rate '
        message += f'wait {wait} seconds'
        print('')
        print(message)
        print('')
        client.set_temperature(setpoint,
                               rate,
                               client.temperature.approach_mode.fast_settle) #fast_settle/no_overshoot
        #for t in range(points):
        save_temp_field_chamber()
        #time.sleep(wait)
        client.wait_for(wait,
                        0,
                        client.subsystem.temperature)
        save_temp_field_chamber()

        #------------------------ Set Field ------------------------------------------------
        CurrentField = 0.0
        MaxField = 20000 #Oe
        i = 0
        rate = 220

        client.set_field(CurrentField,
                         rate,
                         client.field.approach_mode.linear,
                         client.field.driven_mode.driven)

        print('')
        print(f'Waiting for {CurrentField} Oe Field')
        print('')
        client.wait_for(15,
                        0,
                        client.subsystem.field)
        save_temp_field_chamber()

        while (CurrentField <= MaxField):
            #CurrentField, sF = client.get_field()
            deltaH = 100.0
            Fieldsetpoint = CurrentField + deltaH 
            rate = 220
            wait = abs(CurrentField-Fieldsetpoint)/rate
            message = f'Set the field to {Fieldsetpoint} Oe and then collect data '
            print('')
            print(message)
            print('')
            client.set_field(Fieldsetpoint,
                            rate,
                            client.field.approach_mode.linear,
                            client.field.driven_mode.driven)

            # Wait for 10 seconds after temperature and field are stable
            print('')
            print(f'Waiting for {Fieldsetpoint} Oe Field')
            print('')
            client.wait_for(15,
                            None,
                            client.subsystem.field)
            
            #----------------------------- Measure S Parameters-------------------
            import PNA_MM_v2
            PNA_MM_v2.PNA_Func(Fieldsetpoint)
            #----------------------------- Measure S Parameters-------------------
            
            #for t in range(10):
            save_temp_field_chamber()
            #time.sleep(wait)

            CurrentField = Fieldsetpoint
            
        
        client.set_field(0.0,
                         220,
                         client.field.approach_mode.linear,
                         client.field.driven_mode.driven)
        print('Waiting for Zero Field')
        client.wait_for(10,
                        0,
                        client.subsystem.field)

        temperature, status = client.get_temperature()
        print(f'Temperature = {temperature} {tempUnits}')
        
        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')
        
    #client.close_client()
#client.close_server()

myPna.write("SYST:ERR?")    # Check the error queue. Initially *CLS asserted in the beginning of the program.
print(myPna.read())
myPna.close()   # Close the VISA connection