def PNA_Func(Fieldsetpoint):
    import pyvisa as visa
    import time
    import csv
    import matplotlib.pyplot as plt
    import math
    import pandas as pd
    import numpy as np

    # Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries. 
    rm = visa.ResourceManager()

    # Based on the resource manager, open a sesion to a specific VISA resource string as provided via
    #   Keysight Connection Expert
    # ALTER LINE BELOW - Updated VISA resource string to match your specific configuration
    myPna = rm.open_resource("GPIB1::16::INSTR")

    # ========================================================= #

    myPna.timeout = 10000   # Set Timeout - 10 seconds

    start_freq = 0.1e9  # 1 GHz   # Set the start and stop frequencies (in Hz)
    stop_freq = 30e9   # 5 GHz
    power_dBm = -10 #dBm

    myPna.write("SYST:PRES; *OPC?")     # Preset the PNA and wait for preset completion via use of *OPC?
    myPna.read()

    myPna.write("*CLS")     # Clear the event status registers and empty the error queue

    myPna.write("*IDN?")    # Query identification string *IDN?
    print(myPna.read())

    myPna.write("SYST:ERR?")    # Check the error queue
    print(myPna.read())

    # Select the default measurement name as assigned on preset. To catalog the measurement names,
    # by channel number, use the 'CALCulate[n]:PARameter:CATalog?' command where [n] is the channel
    # number. The channel number, n, defaults to "1" and is optional.
    # Measurement name is case sensitive.
    myPna.write("CALC:PAR:SEL 'CH1_S11_1'")

    myPna.write("FORM:DATA ASCII")  # Set data transfer format to ASCII
    #myPna.write("FORM:REAL,32")
    myPna.write("FORMat:BORDER NORMal")

    myPna.write("CALC:PAR:MOD S21") # Alter measure from S11 to S21

    # ========================================================= #

    # Loop to control the number of trace points
    myTraceData = []
    i = 0
    #numPointsList = [201, 401, 801, 1601, 3201, 6401, 12801, 20001, 32001, 100001]
    numPointsList = [32001]

    #while i < len(numPointsList): #Ends at i+=1 [Use while loop if you use more than one from numPointsList]
    numPoints = numPointsList[i]
    myPna.write(f"SENS:SWE:POIN {numPoints};*OPC?")
    myPna.read()

    # Set the start and stop frequencies
    #myPna.write(f"SOUR:FREQ:STAR {start_freq}Hz")
    #myPna.write(f"SOUR:FREQ:STOP {stop_freq}Hz")
    myPna.write(f"SENS:FREQ:STAR {start_freq}")
    myPna.write(f"SENS:FREQ:STOP {stop_freq}")

    myPna.write(f'SOUR:POW {power_dBm}') # Set micrwave power

    startTime = time.perf_counter()
    myPna.write("SENS:SWE:MODE SING;*OPC?") # Trigger assertion with hold-off for trigger complete via *OPC?
    myPna.read()
    stopTime = time.perf_counter() - startTime

    # The SDATA assertion queries underlying real and imaginary pair data
    myPna.write("CALC:DATA? FDATA")
    myTraceData = myPna.read()

    data_list = [float(x) for x in myTraceData.split(",")]  # Convert the data to a list of numbers
    frequencies = np.linspace(start_freq, stop_freq, numPoints-1)   # Create a frequency list (assuming equidistant frequencies)

    # Create a CSV file for each measurement (S11 and S21)
    filename = f"S21_data_{Fieldsetpoint} Oe_{power_dBm} dBm_{numPoints}_points_{start_freq} Hz to {stop_freq} Hz.csv"
    with open(filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Frequency (Hz)', 'S21 (Real)', 'S21 (Imaginary)'])
        for j, f in enumerate(frequencies):
            # Modify the indexing based on your data structure
            s21_data = data_list[j]  # Assuming the data is a complex number
            s21_real = s21_data.real
            s21_imaginary = s21_data.imag
            csv_writer.writerow([f, s21_real, s21_imaginary])
        print(f"Data saved to {filename}")
    i += 1
    #While loop ends
    # ========================================================= #

    myPna.write("SYST:ERR?")    # Check the error queue. Initially *CLS asserted in the beginning of the program.
    print(myPna.read())

    myPna.close()   # Close the VISA connection
