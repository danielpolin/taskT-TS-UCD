#!/usr/bin/env python
#Author: Daniel Polin, Craig Lage, UC Davis; 
#Date: 20220420

import numpy, time, datetime, sys, subprocess
from astropy.time import Time
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Devices.InterfaceKit import InterfaceKit

#************************************* SUBROUTINES ***********************************************

class CryostatFill(object):
    def __init__(self, master):
        self.master = master
        self.fill_log_name='/home/ccd/cryostat/Log_Files/fill_log.dat'
        self.valve = InterfaceKit()
        self.comm_status = False
        self.ov_temp = 999.0
        self.valve_state = "Closed"
        return

    def Check_Communications(self):
        '''Checks on communications status with the Cryostat Fill relay'''
        self.comm_status = False
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Cryostat valve Phidget
            self.valve.waitForAttach(10000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                self.comm_status = True
            self.valve.closePhidget()
            print("Successfully initialized CryostatFill Relay\n")
            sys.stdout.flush()
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            print("Failed to initialize CryostatFill Relay\n")
            sys.stdout.flush()
            self.valve.closePhidget()
            return

    def StartFill(self):
        '''Opens the Cryostat fill valve'''
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Cryostat valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                self.valve.setOutputState(0,True) # This opens the valve
                #self.valve.setOutputState(1,True)
                time.sleep(2.0)
                state0 = self.valve.getOutputState(0)
                #state1 = self.valve.getOutputState(1) #second relay switch
                if state0:
                    time.sleep(0.1)
                    starttime=datetime.datetime.now()
                    print("Successfully initiated Cryostat fill at "+ starttime.strftime("%Y-%m-%d-%H:%M:%S"))
                    sys.stdout.flush()
                    time.sleep(0.1)
                    return True
                else:
                    errtime=datetime.datetime.now()
                    print("Error 1 in initiating Cryostat fill at "+errtime.strftime("%Y-%m-%d-%H:%M:%S"))
                    sys.stdout.flush()
                    self.valve.closePhidget()
                    return False

        except PhidgetException as e:
            errtime=datetime.datetime.now()
            print("Error 2 in initiating Cryostat fill at "+errtime.strftime("%Y-%m-%d-%H:%M:%S"))
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return False

    def StopFill(self):
        '''Closes the Cryostat fill valve'''
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Cryostat valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                self.valve.setOutputState(0,False) # This closes the valve
                self.valve.setOutputState(1,False)
                time.sleep(1.0)
                self.valve.closePhidget()
            self.valve.openPhidget(431944) # Serial number 431944 is the Cryostat valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                state0 = self.valve.getOutputState(0)
                state1 = self.valve.getOutputState(1)
                if not state0 and not state1:
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    termtime=datetime.datetime.now()
                    print("Successfully terminated Cryostat fill at "+ termtime.strftime("%Y-%m-%d-%H:%M:%S"))
                    sys.stdout.flush()
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    time.sleep(0.1)
                    return True
                else:
                    errtime=datetime.datetime.now()
                    print("Error 1 in terminating Cryostat fill at "+ errtime.strftime("%Y-%m-%d-%H:%M:%S"))
                    sys.stdout.flush()
                    self.valve.closePhidget()
                    return False

        except PhidgetException as e:
            errtime=datetime.datetime.now()
            print("Error 2 in terminating Cryostat fill at "+ errtime.strftime("%Y-%m-%d-%H:%M:%S"))
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return False

    def MeasureOverFlowTemp(self):
        '''Measures the temperature in the overflow cup.
        returns both the valve state and the temperature'''
        try:
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                sensor = self.valve.getSensorValue(3)
                NumTries = 0
                while sensor < 0.01 and NumTries < 5:
                    time.sleep(0.1)
                    sensor = self.valve.getSensorValue(3)
                    NumTries += 1
                self.ov_temp = sensor * 0.2222 - 61.111
                state0 = self.valve.getOutputState(0)
                #state1 = self.valve.getOutputState(1)
                state = state0
                if state:
                    self.valve_state = "Open"
                if not state:
                    self.valve_state = "Closed"
                return [state, self.ov_temp]
            else:
                
                return [False, 999.0]
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return [False, 999.0]

    def LogFill(self, fill_time=0.0):
        '''Logs the Cryostat Fill'''
        date = datetime.datetime.now()
        out =date.strftime("%Y-%m-%d-%H:%M:%S")+' '+str(fill_time)+'\n'
        file = open(self.fill_log_name, 'a')
        file.write(out)
        file.close()
        time.sleep(0.1)
        return
