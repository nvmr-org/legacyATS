#####################
# BodRptSim-v6.3.py #
#####################
#
#This script will issue a sequence of ten reports three times simulating
#BOD reports which stimulates trolley movement for testing the ATS
#
# Created by Gerald Wolfson copyright 2017

import java

import jmri
import javax.swing

import time

sndTrace = False

killed = False

# *************************************************************************
# WindowListener is a interface class and therefore all of it's           *
# methods should be implemented even if not used to avoid AttributeErrors *
# *************************************************************************
class WinListener(java.awt.event.WindowListener):

    def windowClosing(self, event):
        global killed
        
        #print "window closing"
        killed = True #this will signal everything that exiting is in progress
        time.sleep(2.0) #give it a chance to happen before going on         
        fr.dispose()         #close the pane (window)
        return
        
    def windowActivated(self, event):
        return
        
    def windowDeactivated(self, event):
        return
        
    def windowOpened(self, event):
        return
        
    def windowClosed(self, event):
        #print 'window closed'
        return
        
    def windowIconified(self, event):
        return
        
    def windowDeiconified(self, event):
        return
        
# *************************
# Prepare LocoNet Message *
# *************************  
def prepLnAddr(lnAddress) :
    global hiAddrByte
    global loAddrByte
    
    if iTrace : print "==>>entering prepLnAddr"
    #translate address into digitrax msb and lsb values
    dtxAddress = int(lnAddress)    # get address from entry field for LocoNet
    hiAddrByte = dtxAddress - ((dtxAddress / 128) * 128) #most significant address byte
    loAddrByte = dtxAddress / 128 #least significant address byte
    if bTrace : print "hiAddrByte = "  + hex(hiAddrByte)
    if bTrace : print "loAddrByte = " + hex(loAddrByte)
    
    if oTrace : print "<<==exiting prepLnAddr"
    return

# ************************
# * send a sensor report *
# ************************
def sendSnrRptMsg(sensorID):
    
    snrAddr = sensorID -1
    in1 = (snrAddr & 0x7F) >> 1 # lower 7 address bits left shifted once
    b2I = (snrAddr % 2) << 5 # remainder odd/even
    b2XL = 0x50 # X = 1 and L = 1
    b2XIL = b2I | b2XL
    in2 = b2XIL + (snrAddr >> 7) # XIL plus upper 4 address bits
    #print "b2I = " + hex(b2I)
    #print "b2XL = " + hex(b2XL)
    #print "b2XIL = " + hex(b2XIL)
    #print "in1 = " + hex(in1)
    #print "in2 = " + hex(in2)
    
    m = jmri.jmrix.loconet.LocoNetMessage(4)
    m.setOpCode(0xB2)
    m.setElement(1,in1)
    m.setElement(2,in2)
    jmri.jmrix.loconet.LnTrafficController.instance().sendLocoNetMessage(m)
    if sndTrace: print "sent sensor rpt msg " + str(sensorID)
    
    return
    
# ******************************************
# * send a simulated sensor report message *
# ******************************************
def simSnrRptMsg(sensorID):
    global killed
    
    delayAfter = 5.0 # 5 second delay
    
    if not killed:
        sendSnrRptMsg(sensorID)
        time.sleep(delayAfter)
    return # report sensor 105 active then delay before next
    
# *******************************************************************
# * simulate trolley sensor report as BOD triggered in each section *
# *******************************************************************
class SimSensorReport(jmri.jmrit.automat.AbstractAutomaton) :

    # handle() will only execute once here, to run a single test
    def handle(self):
        sndTrace = True
        
        print
        print "Starting BOD Reporting Simulation"
        # Reports as seen from BODs 100 thru 107 three times
        simSnrRptMsg(105)
        simSnrRptMsg(106)        
        simSnrRptMsg(100)        
        simSnrRptMsg(101)        
        simSnrRptMsg(100)        
        simSnrRptMsg(102)        
        simSnrRptMsg(107)        
        simSnrRptMsg(104)        
        simSnrRptMsg(103)        
        simSnrRptMsg(107)        
        simSnrRptMsg(102)        
        simSnrRptMsg(105)        
        simSnrRptMsg(106)        
        simSnrRptMsg(100)        
        simSnrRptMsg(101)        
        simSnrRptMsg(102)        
        simSnrRptMsg(107)        
        simSnrRptMsg(104)        
        simSnrRptMsg(103)        
        simSnrRptMsg(107)        
        simSnrRptMsg(102)        
        simSnrRptMsg(105)        
        simSnrRptMsg(106)        
        simSnrRptMsg(100)        
        simSnrRptMsg(101)        
        simSnrRptMsg(102)        
        simSnrRptMsg(107)        
        simSnrRptMsg(104)        
        simSnrRptMsg(103)        
        simSnrRptMsg(107)        
        simSnrRptMsg(102)        
        simSnrRptMsg(105)
        simSnrRptMsg(106)        
        
        if sndTrace: print "Simulated BOD Reporting Completed or Stopped"

        fr.dispose()         #close the pane (window)
        return

# create the button, and add an action routine to it
b = javax.swing.JButton("Quit")
def whenMyButtonClicked(event) :
    global killed
    
    killed = True
    print "stopping sim & exiting!"
    return
    
b.actionPerformed = whenMyButtonClicked

# ----------------------------------------------------------------
# create a window listener. This is used mainly to exit the app
# when the window is closed by clicking on the window close button
# ----------------------------------------------------------------
w = WinListener()

# create a frame to hold the button, put button in it, and display
fr = javax.swing.JFrame("BOD Report Simulator")
fr.contentPane.add(b)
fr.addWindowListener(w)
fr.pack()
fr.show()

SimSensorReport().start()
