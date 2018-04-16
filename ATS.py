#
# ATS (Automatic Trolley Sequencer)
#
# This script has been modified to read in trolley block 
# occupancy messages and control the speed of the related
# trolleys as they move around the same track loop.
#
# This is built on a set of code which can display
# each sensor event and/or speak it for debugging purposes.
#
# It also plots a graph of the number of bytes transmitted
# on the LocoNet each second
#
# Original Author: Bill Robinson with help from Bob Jacobsen
#
# $Revision: 1.0 $  1/8/07
# $Revision: 1.1 $  11/2/10 added second SN address field
# $Revision: 1.2 $  6/3/11 added SN address range fields and second SW address field
# $Revision: 1.3 $  9/2/12 added option to print SN address if its state changed
#
# Author: Gerry Wolfson
#
# $Revision: 2.7 $ 4/07/16 added time stamp checkbox
# $Revision: 2.8 $ 4/13/16 added 25 second averaged line to stripchart
# $Revision: 2.9 $ 4/18/16 added doAvgPlot boolean to turn on/off average plotting
# $Revision: 3.0 $ 4/19/16 added doSecsPlot boolean to turn on/off seconds plotting
# Note: doAvgPlot & doSecsPlot both false turns off charting
# $Revision: 3.1 $ 4/22/16 (a) reorder plots: 30%, 45%, 60%, 80% first followed by seconds plot and then accummulated plot
#                          (b) put message to system console if message list file does not exist and exit
#                          (c) choose either logarithmic or linear vertical scale
# $Revision: 3.2 $ 4/25/16 (a) debug of long delay between spoken alerts
#                          (b) added my default startup test settings
#                          (c) pointed to latest message set V3
#                          (d) added missing globals for checkbox turn on for last state spoken after resync
# $Revision: 3.3 $ 4/28/16 added message string index display checkbox
# $Revision: 3.4 $ 5/15/16 added numeric report of message number and no text on empty strings
# $Revision: 3.5 $ 5/30/16 added JScrollPane to text area and set controls for scrolling
# $Revision: 3.6 $ 6/11/16 use sensors in JMRI instead of CSV file

# $Revision: 3.8 $ 6/08/16 added jmri.util.JmriMFrame to send gui to webserver
# $Revision: 3.8rhwX1 $ 6/20/16 rearranging MsgListener filters by moving sig head into upper group and added hack for parseMsg
# $Revision: 3.8rhwX2 $ 6/23/16 general code cleanup after hack fixed problem

# $Revision: 3.9 $ 6/12/16 added displayTxt to handle non-LocoNet msg display (no parsing)
# $Revision: 4.0 $ 6/15/16 added autoscroll CARET set command
# $Revision: 4.1 $ 6/18/16 incorporated RHW sensor comment usage features
# $Revision: 4.2 $ 8/16/16 added filtering to scanReport background task
# $Revision: 4.3 $ 8/18/16 commented out or remove unnecessary debug print traces
# $Revision: 4.4 $ 8/30/16 special handling of trolley hill hold with return from spencer loop and interchange normal
# $Revision: 4.5 $ 9/07/16 reordered logic and added delays to special handling of trolley hill hold
# $Revision: 4.6 $ 9/07/16 added repeat delay to while loop invoked when alert has been given on last loop
# $Revision: 4.7 $ 9/28/16 change to time.sleep(0.5) in MsgListener

# $Revision: 5.0 $ 1/14/17 Start of ATS coding
# $Revision: 5.1 $ 1/18/17 first debugging after run at club
# $Revision: 5.2 $ 1/23/17 change to prepLnMsg and sendLnMsg for trolley control
# $Revision: 5.3 $ 1/31/17 start of query message sending code
# $Revision: 5.4 $ 2/03/17 refactoring to put init separate from event handler code
# $Revision: 5.5 $ 2/05/17 made firstBFE7 and slotCnt globals
# $Revision: 5.6 $ 2/07/17 moved trolley setup code into msgListener
# $Revision: 5.7 $ 2/12/17 start of multiple trolley squencing code in msgListener
# $Revision: 5.8 $ 2/14/17 start of multiple trolley squencing code in msgListener
# $Revision: 5.9 $ 2/25/17 rewrite to use a trolley object oriented approach
# $Revision: 6.0 $ 2/28/17 removed trolley object oriented code since not used
# $Revision: 6.1 $ 3/02/17 reworked transition logic to allow BOD dropout and return
# $Revision: 6.2 $ 3/08/17 reduced to only ATS script (removed PAS code) and added emergency stop function
# $Revision: 6.3 $ 3/21/17 rework to ring bell after start and show proper icon as trolleys move
# $Revision: 6.4 $ 3/22/17 added check for section already occupied in case of lost track contact
# $Revision: 6.5 $ 4/04/17 changed Estop to regular Stop (drifting) going into section 106, turned lights off when exiting or all stopped, fixed allStop to leave loop so not more trolleys will start moving afterwards
# $Revision: 6.6 $ 4/05/17 added long stop, adjust sending stop msgs to only occur when running
# $Revision: 6.7 $ 4/15/17 added missing global array for sendLnMsg ARGS and completely separated ATS from LnScan
# $Revision: 6.8 $ 4/20/17 fixed 0xE7 msg filter by moving it before filling ARGS array
# $Revision: 6.9 $ 4/26/17 added sending all stop message to console
# $Revision: 7.0 $ 5/01/17 reactivate track contact bounce protection
#
# $Revision: 10.0 $ 2/15/18 Start of new series for 4 trolleys and an expanded number of BODs
apNameVersion = "Automatic Trolley Sequencer - v10.0"

import jmri
import java
####import java.util.concurrent.TimeUnit

import time

fus = jmri.util.FileUtilSupport()
trolleyAddressesFile = fus.getUserFilesPath() + "saveTaddresses.cfg"
#trolleyAddressesFile = "C:\Users\wolfsong\JMRI\My_JMRI_Railroad\saveTaddresses.cfg"
#trolleyAddressesFile = "C:\Users\NVMR\JMRI\PanelPro\saveTaddresses.cfg"
#trolleyAddressesFile = 'preference:\saveTaddresses.cfg'

# This script displays LocoNet messages.
# The frame contains JTextFields, a scroll field, check boxes and a button.
# The frame contains Panel arranged such that only the scroll field moves
# when the window is resized.
# Switch, feedback and sensor messages can be filtered.
#
# editing boolean values: True False (uppercase first letter)
#
trolleySpeed = 0x32 # default throttle set to 50

iTrace = False #turn enter (In) trace print off/on
bTrace = False #turn all (Between) enter and exit traces print off/on 
oTrace = False #turn exit (Out) trace print off/on
dTrace = True #turn limited section Debug trace print off/on
lTrace = False #turn msgListener incoming opcode print off/on
tTrace = False #turn trolley array status print off/on
sTrace = False #turn sequence view of LocoNet messages off/on
debounce = True #turn track contact loss debounce off/on

import javax.swing
aspectColor = " "
accumByteCnt = 0

#import sys
#import com.csvreader

from java.lang import Runnable
from javax.swing import SwingUtilities
from javax.swing.text import DefaultCaret
from java.awt import BasicStroke
from java.awt.geom import Ellipse2D
from java.awt import Font

from org.slf4j import Logger
from org.slf4j import LoggerFactory

log = LoggerFactory.getLogger("LnScanner")

import array

mainStartTime = "[init started]" + time.strftime('%X %x %Z')

import thread
killed = False #run background task until set true
resyncInProgress = False #go true when resync button pressed
checkRestoreDone = True
#reset after 15 seconds and restore speak checkbox values
resyncStrtTime = time.clock() #seed time at app start
####print 'seed value of resyncStrtTime = ', resyncStrtTime

#from threading import Thread
#from java.lang import InterruptedException, Runnable, Thread
#from java.beans import PropertyChangeListener
#from java.util.concurrent import ExecutionException
#from javax.swing import SwingWorker, SwingUtilities

# imports for stripchart portion
import os;
# from org.jfree.chart import ChartColor
# from org.jfree.chart import ChartFactory
# from org.jfree.chart import ChartFrame
# from org.jfree.chart import ChartPanel
# from org.jfree.chart import ChartUtilities
# from org.jfree.chart import JFreeChart
# from org.jfree.chart.axis import LogarithmicAxis
# from org.jfree.chart.axis import ValueAxis
# #from org.jfree.chart.axis import LogAxis
# from org.jfree.chart.plot import XYPlot
# from org.jfree.chart.plot import ValueMarker
# from org.jfree.chart.renderer.xy import XYLineAndShapeRenderer
# from org.jfree.chart.renderer.xy import XYItemRenderer
# from org.jfree.chart.renderer.xy import XYDotRenderer
# from org.jfree.data.time import Millisecond
# from org.jfree.data.time import TimeSeries
# from org.jfree.data.time import TimeSeriesCollection
# from org.jfree.data.xy import XYDataset
# from org.jfree.ui import ApplicationFrame
# from org.jfree.ui import RefineryUtilities
# from org.jfree.util import ShapeUtilities

#from trolley import Trolley

trolleyLocs = [00,00,00,00,00,00,00,00,00] # filled later with slotID of each trolley
trolleyMove = [35,35,35,35,35,35,35,35,35] # 35 '#' = empty, 83 'S' = stopped, 82 'R' = running
motionState = {} #dictionary for throttle state of each trolley, value is '0' = stopped or '1' = running
#motionState = [0,0,0] #moving state of each trolley, 0 = stopped 1 = running
maxSpeed = [50,50,50] #default max speed unless replace with file values

trolleyAout = False
trolleyBout = False
initCnt = 0 #number of trolleys that have been started


trolleyCnt = 3
trolleyA = 2730 #engine 1 address
trolleyB = 4887 #engine 2 address
trolleyC = 4172 #engine 3 address
trolleyID = trolleyA # set for first trolley to leave section 106

# *******************************************************************************
# ******** global variables for passing message values between functions ********
# *******************************************************************************
ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # global args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
hiAddrByte = -1
loAddrByte = -1
BFsent = False
firstBFE7 = True        
noSlotID = True
notAlt0xE7 = True
slotCnt = 0
slotA = -1
slotB = -1
slotC = -1
slotID = -1
lastDeviceID = -1
respCnt0xE7 = 0
newMsgOpCodeHex = 0x00 #place to store latest message opcode in hex

msgA = "" #placeholder for trolley info message
msgB = "" #placeholder for trolley info message
msgC = "" #placeholder for trolley info message
        
AllTrolleysNotOut = True
Trolley1NotOut = True
Trolley2NotOut = True
Trolley3NotOut = True

suspended = False

# ****************************************************************
# ************* Section to get and set trolley state parameters. *
# ****************************************************************
class Trolley(object):

    # NORTH = 0
    # EAST = 1
    # SOUTH = 2
    # WEST = 3

    def __init__(self, cSection=-1, nSection=-1, tpriority=1, tslotID=-1, tspeed=-1):
        self.currSection = curSection
        self.nextSection = nxtSection
        self.priority = tpriority
        self.slotID = tslotID
        self.speed = tspeed
        
    def getCurrSection(self):
        return (self.currSection)
        
    def setCurrSection(self, cSection):
        self.currSection = cSection
        
    def getNextSection(self):
        return (self.nextSection)
        
    def setNextSection(self, nSection):
        self.nextSection = nSection
        
    def getPriority(self):
        return (self.priority)
        
    def setPriority(self, tpriority):
        self.priority = tpriority
        
    def getTslotID(self):
        return (self.slotID)
        
    def setTslotID(self, tslotID):
        self.slotID = tslotID
        
    def getTspeed(self):
        return (self.speed)
        
    def setTspeed(self, tspeed):
        self.speed = tspeed
    

    # def turn_right(self):
        # self.direction += 1
        # self.direction = self.direction % 4

    # def turn_left(self):
        # self.direction -= 1
        # self.direction = self.direction % 4

    # def move(self, distance):
        # if self.direction == self.NORTH:
            # self.y += distance
        # elif self.direction == self.SOUTH:
            # self.y -= distance
        # elif self.direction == self.EAST:
            # self.x += distance
        # else:
            # self.x -= distance

    # def position(self):
        # return (self.x, self.y)
		
# *****************************************************************************************
# ************* Section to Listen to all sensors, printing a line when they change state. *
# *****************************************************************************************

# ************************************************
# * Define routine to map status numbers to text *
# ************************************************
def stateName(state):
    if (state == ACTIVE):
        return "ACTIVE"
    if (state == INACTIVE):
        return "INACTIVE"
    if (state == INCONSISTENT):
        return "INCONSISTENT"
    if (state == UNKNOWN):
        return "UNKNOWN"
    return "(invalid)"
    
# ******************************************
# * Define the sensor listener: Print some *
# * information on the status change.      *
# ******************************************
class SensorListener(java.beans.PropertyChangeListener):

    def propertyChange(self, event):
        global snrStatusArr
        
        #tmsg = "event.propertyName = "+event.propertyName
        #scrollArea.setText(scrollArea.getText()+tmsg+"\n")
        #tmsg = "event.source.systemName = "+event.source.systemName
        #scrollArea.setText(scrollArea.getText()+tmsg+"\n")
        #print event.propertyName
        if (event.propertyName == "KnownState"):
            systemName = event.source.systemName
            mesg = "Sensor " + systemName
            mesg = mesg.replace(mesg[:2], '') #delete first two characters
            if (event.source.userName != None):
                mesg += " (" + event.source.userName + ")"
            mesg += " is now " + stateName(event.newValue)
            #mesg += " from "+stateName(event.oldValue)
            #mesg += " to "+stateName(event.newValue)
            # print mesg
            # display and/or speak if either range value is empty
            snrStatusArr[systemName] = event.newValue
        return
        
listener = SensorListener()

# **********************************************************************
# Define a Manager listener.  When invoked, a new                      *
# item has been added, so go through the list of items removing the    *
# old listener and adding a new one (works for both already registered *
# and new sensors)                                                     *
# **********************************************************************
class ManagerListener(java.beans.PropertyChangeListener):

    def propertyChange(self, event):
        list = event.source.getSystemNameList()
        for i in range(list.size()):
            event.source.getSensor(list.get(i)).removePropertyChangeListener(listener)
            event.source.getSensor(list.get(i)).addPropertyChangeListener(listener)
            
# Attach the sensor manager listener
sensors.addPropertyChangeListener(ManagerListener())

# ***************************
# * End of Sensor Listener section *
# ***************************

# ***************************
# * Button Pressed Services *
# ***************************

# *******************************************************
# have the text field enable the button when OK NOT used
def whenAddressChanged(event):
    if (address.text != ""): #address only changed if a value was entered
        swAddrCheckBox.setEnabled(True)
    else:
        swAddrCheckBox.setSelected(False)
        swAddrCheckBox.setEnabled(False)
    return
    
# *******************************************************
# define what button does when clicked and attach that routine to the button
def whenEnterButtonClicked(event): #not used
    return
    
# *******************************************************
def whenResyncButtonClicked(event):
    global resyncInProgress
    global resyncStrtTime
    global checkRestoreDone
    global lastSnSpkChgCbx
    global lastSigSpkChgCbx

    # get current speak checkbox states, then uncheck
    lastSnSpkChgCbx = snSpkChgCheckBox.isSelected()
    snSpkChgCheckBox.setSelected(False)
    lastSigSpkChgCbx = sigSpkChgCheckBox.isSelected()
    sigSpkChgCheckBox.setSelected(False)
    resyncInProgress = True #set flag to resync in progress now
    checkRestoreDone = False #set flag to checkRestoreDone needed
    powermanager.setPower(jmri.PowerManager.ON) # send GPON to chief which will query all decoders
    resyncStrtTime = time.clock() #set resync starting time now
    
    print 'resyncStrtTime = ', resyncStrtTime
    print 'resyncInProgress = ', resyncInProgress
    print 'lastSnSpkChgCbx = ', lastSnSpkChgCbx
    print 'lastSigSpkChgCbx = ', lastSigSpkChgCbx
    
    # wait 15 secs for queries responses to complete, then return checkboxes to their entry states
    #time.sleep(15.0)
    #snSpkChgCheckBox.setSelected(lastSnSpkChgCbx)
    #sigSpkChgCheckBox.setSelected(lastSigSpkChgCbx)
    return
    
# *******************************************************
# def whenClearButtonClicked(event): #not used
    # #print "got to here"
    # scrollArea.setText("") #clear the text area
    # return
    
# *******************************************************
def whenQuitButtonClicked(event): #not used
    return
    
# *******************************************************
def whenSaveTaddressesButtonClicked(event):
    global trolleyA,trolleyB,trolleyC
    global maxSpeed
    
    #write current trolley address fields to a new trolleyAddresses.cfg file to be read in on next launch
    trolleyA = trolleyAaddr.text
    trolleyB = trolleyBaddr.text
    trolleyC = trolleyCaddr.text
    speedA = trolleyAspeed.text
    speedB = trolleyBspeed.text
    speedC = trolleyCspeed.text
    if os.path.isfile(trolleyAddressesFile):
        os.remove(trolleyAddressesFile)
    fp=open(trolleyAddressesFile,'w')
    fp.write(str(trolleyA))
    fp.write('\n')
    fp.write(str(trolleyB))
    fp.write('\n')
    fp.write(str(trolleyC))
    fp.write('\n')
    fp.write(str(speedA))
    fp.write('\n')
    fp.write(str(speedB))
    fp.write('\n')
    fp.write(str(speedC))
    fp.write('\n')
    fp.close()
    print "T1 file value of trolleyA = " + str(trolleyA)
    print "T1 file value of maxSpeed[0] = " + str(speedA)
    print "T2 file value of trolleyB = " + str(trolleyB)
    print "T2 file value of maxSpeed[1] = " + str(speedB)
    print "T3 file value of trolleyC = " + str(trolleyC)
    print "T3 file value of maxSpeed[2] = " + str(speedC)
    
    return
    
# *******************************************************
def whenTgoButtonClicked(event) :
    global slotID
    
    slotID = slotA
    startTrolley()
    msg1t = "Start Running button pressed, slot " + str(slotID) + " trolley started"
    print msg1t
    print
    scrollArea.setText(scrollArea.getText() + msg1t + "\n\n")
    
    return
    
# *******************************************************
def whenTstopAllButtonClicked(event) :
    global slotID
    global suspended
    
    stopAllTrolleys()
    suspended = True
    return
    
# *****************************************
# * End of Button Presed Services section *
# *****************************************

# *************************************************************************
# WindowListener is a interface class and therefore all of it's           *
# methods should be implemented even if not used to avoid AttributeErrors *
# *************************************************************************
class WinListener(java.awt.event.WindowListener):

    def windowClosing(self, event):
        global killed
        
        #print "window closing"
        killed = True #this will signal scanReporter thread to exit
        time.sleep(2.0) #give it a chance to happen before going on
        jmri.jmrix.loconet.LnTrafficController.instance().removeLocoNetListener(0xFF, lnListen)
        list = sensors.getSystemNameList()
        
        for i in range(list.size()):    #remove each of the sensor listeners that were added
        
            sensors.getSensor(list.get(i)).removePropertyChangeListener(listener)
            # print "remove"
            
        fr.dispose()         #close the pane (window)
        return
        
    def windowActivated(self, event):
        return
        
    def windowDeactivated(self, event):
        return
        
    def windowOpened(self, event):
        return
        
    def windowClosed(self, event):
        stopAllTrolleys()
        freeSlot(slotA)
        freeSlot(slotB)
        freeSlot(slotC)
        time.sleep(3.0) #wait 3 seconds before moving on to allow last free to complete
        print 'slots freed and ' + apNameVersion + ' exited'
        print
        return
        
    def windowIconified(self, event):
        return
        
    def windowDeiconified(self, event):
        return
        
# *************************************
#create a Llnmon to parse the message *
# *************************************
parseMsg = jmri.jmrix.loconet.locomon.Llnmon()
#workarounds for jython not knowing jmri sensor, turnout, or reporter objects
parseMsg.setLocoNetSensorManager(sensors)
parseMsg.setLocoNetTurnoutManager(turnouts)
parseMsg.setLocoNetReporterManager(reporters)

# ************************
# Emergency stop trolley *
# ************************
def eStopTrolley() :
    global slotID
    global ARGS
    
    msgLength = 4
    opcode = 0xA0 #OPC_LOCO_SPD
    ARGS[1] = slotID
    ARGS[2] = 0x01
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Estop " + str(hex(opcode))
    return

# **********************
# Move or stop trolley *
# **********************
def setTrolleySpeed(speed) :
    global slotID
    global ARGS
    
    msgLength = 4
    opcode = 0xA0 #OPC_LOCO_SPD
    ARGS[1] = slotID
    ARGS[2] = speed
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Set Speed " + str(hex(opcode))
    return

# *******************************************************
def stopTrolley():
    global slotID
    
    setTrolleySpeed(0x1E) #set speed to 30
    time.sleep(0.5) #wait 500 milliseconds
    setTrolleySpeed(0x0F) #set speed to 15
    time.sleep(0.5) #wait 500 milliseconds
    eStopTrolley() #hard stop now
    time.sleep(0.5) #wait half a second after after stop, then ring bell
    ringBell()
    if tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(slotID) + " trolley stopped\n")
    return
    
# *******************************************************
def lstopTrolley():
    global slotID
    
    setTrolleySpeed(0x1E) #set speed to 30
    time.sleep(1.0) #wait 1 second
    setTrolleySpeed(0x0F) #set speed to 15
    time.sleep(1.0) #wait 1 second
    eStopTrolley() #hard stop now
    time.sleep(0.5) #wait half a second after after stop, then ring bell
    ringBell()
    if tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(slotID) + " trolley stopped\n")
    return
    
# *******************************************************
def stopAllTrolleys():
    global slotID
    
    slotID = slotA
    eStopTrolley() #hard stop now
    lightOff()
    slotID = slotB
    eStopTrolley() #hard stop now
    lightOff()
    slotID = slotC
    eStopTrolley() #hard stop now
    lightOff()
    print 'all trolleys stopped'
    scrollArea.setText(scrollArea.getText() + " all trolleys stopped\n")
    return
    
# *********************************************
# Ring the trolley bell before start and stop *
# *********************************************
def ringBell() :
    global slotID
    global ARGS
    
    #ringBell 1st time by setting F1 = ON
    msgLength = 4
    opcode = 0xA1 #OPC_LOCO_DIRF
    ARGS[1] = slotID
    ARGS[2] = 0x11 #ON with direction forward and light ON
    sendLnMsg(msgLength,opcode,ARGS)
    
    time.sleep(1) #wait 1 sec before toggling other way
    
    #ringBell 2nd time by setting F1 = OFF
    msgLength = 4
    opcode = 0xA1 #OPC_LOCO_DIRF
    ARGS[1] = slotID
    ARGS[2] = 0x10 #OFF with direction forward and light ON
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent ring bell " + str(hex(opcode))
    
    #time.sleep(3) #wait 3 sec before returning
    return

# **************************
# Turn light OFF *
# **************************
def lightOff() :
    global slotID
    global ARGS

    msgLength = 4
    opcode = 0xA1 #OPC_LOCO_DIRF
    ARGS[1] = slotID
    ARGS[2] = 0x00 #light OFF, direction forward
    time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent light OFF " + str(hex(opcode))
    time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
    
    return
    
# **************************
# Blink light and leave ON *
# **************************
def blinkOn() :
    global slotID
    global ARGS
    
    count = 5
    
    while (count > 0) :
        count -= 1
        
        time.sleep(0.5) #wait half sec before toggling

        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS[1] = slotID
        ARGS[2] = 0x00 #light OFF, direction forward
        sendLnMsg(msgLength,opcode,ARGS)

        time.sleep(0.5) #wait half sec before toggling

        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS[1] = slotID
        ARGS[2] = 0x10 #light ON, direction forward
        sendLnMsg(msgLength,opcode,ARGS)
        if sTrace : print "sent light ON/OFF " + str(hex(opcode))

    return
    
# ****************
# Set Slot INUSE *
# ****************
def setSlotInuse() :
    global slotID
    global ARGS
    
    msgLength = 4
    opcode = 0xBA #OPC_MOVE_SLOTS
    ARGS[1] = slotID
    ARGS[2] = slotID
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Slot INUSE " + str(hex(opcode))
    noSlotID = False
    return
    
# ****************
# Write Slot Data *
# ****************
def writeSlotData() :
    global slotID
    global ARGS
    
    msgLength = 14
    opcode = 0xEF #OPC_WR_SL_DATA
    
    #### ARGS[1] =0x0E #part of OPC
    #### ARGS[2] = slotID taken from last 0xE7 response
    ARGS[3] = 0x33 #change from 0x03 to refresh INUSE
    #use rest of ARGS from last 0xE7 response
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Slot Data Update " + str(hex(opcode))
    return
    
# *******************
# Update Slot STAT1 *
# *******************
def updateSlot() :
    global slotID
    global ARGS
    
    msgLength = 4
    opcode = 0xB5 #OPC_SLOT_STAT1
    ARGS[1] = slotID
    ARGS[2] = 0x03
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Slot Stat1 Update " + str(hex(opcode))
    return
    
# ***************************************
# Free Trolley Slot (Dispatch Trolleys) *
# ***************************************
def freeSlot(slotNum) :
    global ARGS
    global slotID
    
    slotID = slotNum #set global for use elsewhere
    setTrolleySpeed(0x00) #stop trolley

    msgLength = 4
    opcode = 0xB5 #OPC_SLOT_STAT1
    ARGS[1] = slotNum
    ARGS[2] = 0x13 #update status to Not Consisted, Common slot
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Slot Not Consisted & Common " + str(hex(opcode))
    
    msgLength = 4
    opcode = 0xBA #OPC_MOVE_SLOTS
    ARGS[1] = slotNum
    ARGS[2] = 0x00 #mark slot as DISPATCHED
    sendLnMsg(msgLength,opcode,ARGS)
    if sTrace : print "sent Slot Dispatch " + str(hex(opcode))
    
    updateSlot() #sets slot to being FREE

    return
                
# **********************
# Send LocoNet Message *
# **********************
def sendLnMsg(msgLength,opcode,ARGS) :
     # format and send the specific LocoNet message
     # send up to 16 bytes in the message - includes checksum
     if iTrace : print "==>>entering sendLnMsg -->"
     packet = jmri.jmrix.loconet.LocoNetMessage(msgLength)
     if msgLength == 4 :
        packet.setElement(0, opcode)
        packet.setElement(1, ARGS[1])
        packet.setElement(2, ARGS[2])
     else :
        packet.setElement(0, opcode)
        packet.setElement(1, ARGS[1])
        packet.setElement(2, ARGS[2])
        packet.setElement(3, ARGS[3])
        packet.setElement(4, ARGS[4])
        packet.setElement(5, ARGS[5])
        packet.setElement(6, ARGS[6])
        packet.setElement(7, ARGS[7])
        packet.setElement(8, ARGS[8])
        packet.setElement(9, ARGS[9])
        packet.setElement(10, ARGS[10])
        packet.setElement(11, ARGS[11])
        packet.setElement(12, ARGS[12])
        packet.setElement(13, ARGS[13])
      
     jmri.jmrix.loconet.LnTrafficController.instance().sendLocoNetMessage(packet)
     if iTrace : print "Packet ==>> ", packet           # print packet to Script Output window
     ##prevMsg.setText(str(packet))     # put packet in hex in field
     if oTrace : print "<<==exiting sendLnMsg"
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

# *******************************************************
# ************* Automated Trolley Sequencer *************
# *******************************************************
# Initial state is with all trolleys on the Townside Dual line track (section 106)
# Block 1 contains sections 2,7,4, and 3 then 7 and 2 again in that order
#
bitToChg = 0
bitStateToSet = 0

trolley1SecIdx = 1 # all three trolleys in section 101 (Aisle Side Town Main)
trolley2SecIdx = 1
trolley3SecIdx = 1

# *******************************************************
def requestSlot(deviceID) : #sends 0xBF with loco address
    global ARGS
    global hiAddrByte
    global loAddrByte
    global BFsent
    global noSlotID
    global lastDeviceID
    
    if iTrace : print "==>>entering requestSlot"
    if bTrace : print "requested slot = " + str(deviceID)
    noSlotID = True
    lastDeviceID = deviceID
    prepLnAddr(deviceID)
    if bTrace : print "prep return = " +hex(hiAddrByte) + " " + hex(loAddrByte)
    #request Loco data slot
    msgLength = 4
    opcode = 0xBF #OPC_LOCO_ADR request current slot assigned, if not create slot
    ARGS[1] = loAddrByte
    ARGS[2] = hiAddrByte
    sendLnMsg(msgLength,opcode,ARGS)
    BFsent = True #turn on to allow E7 response to be read for slotID (flag set must be after send!)
    if sTrace : print "sent Slot Request " + str(hex(opcode))
    if oTrace : print "<<==exiting requestSlot"
    return
        
# *******************************************************
def setSlotID(deviceID):
    global noSlotID
    global slotID
    global lastDeviceID
    
    passedID = -1
    
    if iTrace : print "==>>entering setSlotID"
    ##noSlotID = True
    passedID = deviceID
    deviceID = slotID # populate slot(letter) with reponse value
    if bTrace : print "deviceID = " + str(lastDeviceID) + " " + str(passedID) + " = " + str(slotID)
    if oTrace : print "<<==exiting setSlotID"
    return deviceID

# *******************************************************
def doTrolleySequence():
    global slotID
    
    ####ringBell() #bell should only ring when about to move
    setTrolleySpeed(0x00) #set speed to 0
    time.sleep(10.0) #wait 10 secs before doing slowdown sequence
    ringBell()
    time.sleep(3.0) #wait 3 secs after ringing bell and then go
    setTrolleySpeed(trolleySpeed) #set speed to 50
    return
    
# *******************************************************
def startTrolley():
    global slotID
    
    setTrolleySpeed(trolleySpeed) #set speed to 50
    ####time.sleep(3.0) #wait 3 secs after ringing bell and then go
    ringBell()
    if tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(slotID) + " trolley running\n")
    return
    
# *******************************************************
def checkSectionState(eventAddr) :
    global trolleyLocs
    
    if eventAddr == 106 :
        if trolleyLocs[0] > 0 : # greater means occupied
            return True
    elif eventAddr == 100 :
        if trolleyLocs[1] > 0 : # greater means occupied
            return True
    elif eventAddr == 101 :
        if trolleyLocs[2] > 0 : # greater means occupied
            return True
    elif eventAddr == 102 :
        if trolleyLocs[3] > 0 : # greater means occupied
            return True
    elif eventAddr == 107 :
        if trolleyLocs[4] > 0 : # greater means occupied
            return True
    elif eventAddr == 104 :
        if trolleyLocs[5] > 0 : # greater means occupied
            return True
    elif eventAddr == 103 :
        if trolleyLocs[6] > 0 : # greater means occupied
            return True
    elif eventAddr == 107 :
        if trolleyLocs[7] > 0 : # greater means occupied
            return True
    elif eventAddr == 102 :
        if trolleyLocs[8] > 0 : # greater means occupied
            return True
    else :
        return False

# **************************************************
# * Updates Trolley Status Array with position of  *
# * slotIDs and displays result in square brackets *
# **************************************************
def doTrolleyStatusUpdate(eventID):
    global slotID
    global trolleyLocs
    global trolleyMove
    global motionState
    global trolleyAout
    global trolleyBout
    global initCnt
    global suspended
    
    if suspended :
        if tTrace: print "suspended"
        scrollArea.setText(scrollArea.getText() + "suspended 1\n")
        return
        
    #*****************************************************************************
    if sTrace : print ">>rcvd " + str(eventID)
    if initCnt < 3 : # init process to spread out trolleys in separate sections
        print ">>init eventID = " + str(eventID)
        if (eventID <> 105) and (eventID <> 106) :
            initCnt += 1 #bump count up by one
            #****************************************
            if initCnt == 1 : #trolley A should enter section 100
                trolleyLocs[1] = slotA #trolleyA on the move so do not have to set speed
                trolleyMove[1] = 82 #R
                motionState[str(slotA)] = '1'
                if sTrace : print ">>initCnt = " + str(initCnt)
                
            elif initCnt == 2 : #trolley A should enter section 101
                trolleyLocs[2] = trolleyLocs[1]
                trolleyMove[2] = 82 # R done only during init since backward walkthru is not yet running 
                trolleyLocs[1] = 0  # empty
                trolleyMove[1] = 35 # '#' 
                motionState[str(slotB)] = '1'
                slotID = slotB #get trolley B moving, set trolleyB speed to 50
                startTrolley()
                if sTrace : print ">>initCnt = " + str(initCnt)
                
            elif initCnt == 3 : #trolley B should enter section 100
                trolleyLocs[1] = slotB
                trolleyMove[1] = 82 #R
                motionState[str(slotB)] = '1'
                trolleyLocs[0] = slotC
                trolleyMove[0] = 83 #S trolleyC now stopped in section 106 all by itself
                motionState[str(slotC)] = '0'
                if sTrace : print ">>initCnt = " + str(initCnt)
                ####eventID = 101 #change to force first real sweep back from location of trolleyA
                
            else:
                print "Error: initCnt went too far!"
                
    #********************************************************************************************
    else: #regular sequence, 1st pass - updates only one trolley location (rest done in 2nd pass)
        if eventID == 100:
            if trolleyLocs[0] > 0:
                trolleyLocs[1] = trolleyLocs[0]
                trolleyLocs[0] = 0
                trolleyMove[0] = 35
        elif eventID == 101:
            if trolleyLocs[1] > 0:
                trolleyLocs[2] = trolleyLocs[1]
                trolleyLocs[1] = 0
                trolleyMove[1] = 35
        elif eventID == 102:
            if trolleyLocs[7] > 0:
                trolleyLocs[8] = trolleyLocs[7]
                trolleyLocs[7] = 0
                trolleyMove[7] = 35
            elif trolleyLocs[2] > 0:
                trolleyLocs[3] = trolleyLocs[2]
                trolleyLocs[2] = 0
                trolleyMove[2] = 35
        elif eventID == 107:
            if trolleyLocs[3] > 0:
                trolleyLocs[4] = trolleyLocs[3]
                trolleyLocs[3] = 0
                trolleyMove[3] = 35
            elif trolleyLocs[6] > 0:
                trolleyLocs[7] = trolleyLocs[6]
                trolleyLocs[6] = 0
                trolleyMove[6] = 35
        elif eventID == 104:
            if trolleyLocs[4] > 0:
                trolleyLocs[5] = trolleyLocs[4]
                trolleyLocs[4] = 0
                trolleyMove[4] = 35
        elif eventID == 103:
            if trolleyLocs[5] > 0:
                trolleyLocs[6] = trolleyLocs[5]
                trolleyLocs[5] = 0
                trolleyMove[5] = 35
        elif eventID == 106:
            if trolleyLocs[8] > 0:
                trolleyLocs[0] = trolleyLocs[8]
                trolleyLocs[8] = 0
                trolleyMove[8] = 35
        else:
            print "WARNING: unused in range eventID " + str(eventID) + " reported "
        
    if eventID <> 105 :
        if tTrace: print "trolleyAout is " + str(trolleyAout)
        if tTrace: print "trolleyBout is " + str(trolleyBout)
        ####if tTrace: print trolleyLocs
        ####scrollArea.setText(scrollArea.getText() + str(trolleyLocs) + " BOD " + str(eventID) + "\n")
        tL0 = str(trolleyLocs[0]).zfill(2).rjust(3)
        tL1 = str(trolleyLocs[1]).zfill(2).rjust(3)
        tL2 = str(trolleyLocs[2]).zfill(2).rjust(3)
        tL3 = str(trolleyLocs[3]).zfill(2).rjust(3)
        tL4 = str(trolleyLocs[4]).zfill(2).rjust(3)
        tL5 = str(trolleyLocs[5]).zfill(2).rjust(3)
        tL6 = str(trolleyLocs[6]).zfill(2).rjust(3)
        tL7 = str(trolleyLocs[7]).zfill(2).rjust(3)
        tL8 = str(trolleyLocs[8]).zfill(2).rjust(3)
        trolleyPosition = "[" + tL0 + tL1 + tL2 + tL3 + tL4 + tL5 + tL6 + tL7 + tL8 + "  ] BOD " + str(eventID)
        if tTrace: print trolleyPosition
        scrollArea.setText(scrollArea.getText() + trolleyPosition + "\n")
        
        doTrolleyThrottleUpdates(eventID)

    return
    
###############
# setThrottle #
###############
#sets throttle to actual state
#
def setThrottle():
    global thisID
    global frwID
    global slotID
    global trolleyLocs
    global trolleyMove
    global motionState
    
    if thisID == 2 :
        if trolleyLocs[thisID] > 0: #check if section 101 is occupied, checking multiple sections if headed into 102
            slotID = trolleyLocs[thisID]
            sSlotID = str(slotID)
            if (trolleyLocs[3] > 0) or (trolleyLocs[4] > 0) or (trolleyLocs[5] > 0) or (trolleyLocs[6] > 0) or (trolleyLocs[7] > 0) or (trolleyLocs[8] > 0):
                if motionState[sSlotID] <> '0': #only do if not already stopped
                    motionState[sSlotID] = '0'
                    lstopTrolley() #section 102,107,104,or 103 is occupied so long drift stop to clear fouling and insulation points
                trolleyMove[thisID] = 83 #S
            else:
                if motionState[sSlotID] <> '1': #only do if not already running
                    motionState[sSlotID] = '1'
                    startTrolley() #set trolley speed to GO
                trolleyMove[thisID] = 82 #R
    elif (thisID == 0) or (thisID == 1) :
        if trolleyLocs[thisID] > 0: #check if section 106 or 100 is occupied
            slotID = trolleyLocs[thisID]
            sSlotID = str(slotID)
            if trolleyLocs[frwID] > 0: #is next section ahead occupied
                if motionState[sSlotID] <> '0': #only do if not already stopped
                    motionState[sSlotID] = '0'
                    lstopTrolley() #set trolley speed to STOP
                trolleyMove[thisID] = 83 #S
            else:
                if motionState[sSlotID] <> '1': #only do if not already running
                    motionState[sSlotID] = '1'
                    startTrolley() #set trolley speed to GO
                trolleyMove[thisID] = 82 #R
    else:
        if trolleyLocs[thisID] > 0: #check if any section other than 106,100, or 101 is occupied
            slotID = trolleyLocs[thisID]
            sSlotID = str(slotID)
            if trolleyLocs[frwID] > 0: #next section ahead 102 is occupied
                if motionState[sSlotID] <> '0': #only do if not already stopped
                    motionState[sSlotID] = '0'
                    stopTrolley() #set trolley speed to STOP
                trolleyMove[thisID] = 83 #S
            else:
                if motionState[sSlotID] <> '1': #only do if not already running
                    motionState[sSlotID] = '1'
                    startTrolley() #set trolley speed to GO
                trolleyMove[thisID] = 82 #R

    return

# *****************************************************************
# * Updates Trolley Throttle Settings Array and displays result   *
# * using the following characters to show trolley status in each *
# * section: 35 '#' = empty, 83 'S' = stopped, 82 'R' = running   *
# *****************************************************************
def doTrolleyThrottleUpdates(eventID):
    global thisID
    global frwID
    global slotID
    global trolleyAout
    global trolleyBout
    global trolleyLocs
    global trolleyMove
    global motionState
    global suspended
    
    print "motionStateList = " + str(motionState.values()) + " BOD " + str(eventID)
    if initCnt == 3 :
        # both trolleys must be started before entering this state machine
        #second pass - set all trolley throttles according to next sections occupancy
        #work backwards from entry point event
        
        if sTrace : print "eventID = " + str(eventID)
        # +----------------------------------------------------+
        # |106 | 100 | 101 | 102 | 107 | 104 | 103 | 107 | 102 |
        # +----+-----+-----+-----+-----+-----+-----+-----+-----+
        # | 0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |
        # +----------------------------------------------------+
        
        walkCnt = 9 #number of throttle adjustments to go thru from entry point
        
        # *******************************************************
        #select entry point for reverse section walkthru
        if eventID == 106 :
            nextID = 0
        elif eventID == 102 :
            if trolleyMove[7] == 82: # is 107 an R
                nextID = 8
            else :
                nextID = 3
        elif eventID == 107 :
            if trolleyMove[6] == 82: # is 103 an R
                nextID = 7
            else :
                nextID = 4
        elif eventID == 103 :
            nextID = 6
        elif eventID == 104 :
            nextID = 5
        elif eventID == 101 :
            nextID = 2
        elif eventID == 100 :
            nextID = 1
        else :
            # don't service, unused for trolley BOD
            print "WARNING: sent address " + str(eventID) + " is unused for trolley BOD!"
            walkCnt = 0 #skip throttle adjustment part
        
        # ***********************************************************************
        # throttle adjustment going eight steps backward from eventID entry point
        while walkCnt > 0 : #start eight step backwards process at eventID entry point
            if suspended :
                if tTrace: print "suspended"
                scrollArea.setText(scrollArea.getText() + "suspended 2\n")
                break
            walkCnt -= 1 #decrement by one each time until zero
            if nextID == 0 : #section 106
                thisID = nextID
                nextID = 8 # set next ID back one section to do on next loop
                frwID = 1
                setThrottle()
                continue
            elif nextID == 8 : #section 102
                thisID = nextID
                nextID = 7 # set next ID back one section to do on next loop
                frwID = 0
                setThrottle()
                continue
            elif nextID == 7 : #section 107
                thisID = nextID
                nextID = 6 # set next ID back one section to do on next loop
                frwID = 8
                setThrottle()
                continue
            elif nextID == 6 : #section 103
                thisID = nextID
                nextID = 5 # set next ID back one section to do on next loop
                frwID = 7
                setThrottle()
                continue
            elif nextID == 5 : #section 104
                thisID = nextID
                nextID = 4 # set next ID back one section to do on next loop
                frwID = 6
                setThrottle()
                continue
            elif nextID == 4 : #section 107
                thisID = nextID
                nextID = 3 # set next ID back one section to do on next loop
                frwID = 5
                setThrottle()
                continue
            elif nextID == 3 : #section 102
                thisID = nextID
                nextID = 2 # set next ID back one section to do on next loop
                frwID = 4
                setThrottle()
                continue
            elif nextID == 2 : #section 101
                thisID = nextID
                nextID = 1 # set next ID back one section to do on next loop
                frwID = 3
                setThrottle()
                continue
            elif nextID == 1 : #section 100
                thisID = nextID
                nextID = 0 # set next ID back one section to do on next loop
                frwID = 2
                setThrottle()
                continue
            else :
                print "Error: major coding problem, should never get here!"
                
    throttleCondition = "   " + \
                        chr(trolleyMove[0]) + ", " + \
                        chr(trolleyMove[1]) + ", " + \
                        chr(trolleyMove[2]) + ", " + \
                        chr(trolleyMove[3]) + ", " + \
                        chr(trolleyMove[4]) + ", " + \
                        chr(trolleyMove[5]) + ", " + \
                        chr(trolleyMove[6]) + ", " + \
                        chr(trolleyMove[7]) + ", " + \
                        chr(trolleyMove[8]) + "   "
    if tTrace: print throttleCondition
    scrollArea.setText(scrollArea.getText() + throttleCondition + "\n\n")

    return
    
# **************************************************
#class to handle a listener event loconet messages *
#                                                  *
# OpCode values: 131 = 0x83 = OPC_GPON             *
#                229 = 0xE5 = OPC_PEER_XFER        *
#                                                  *
#                176 = 0xB0 = OPC_SW_REQ           *
#                177 = 0xB1 = OPC_SW_REP           *
#                178 = 0xB2 = OPC_INPUT_REP        *
#                231 = 0xE7 = OPC_SL_RD_DATA       *
#                237 = 0xED = OPC_IMM_PACKET       *
#                                                  *
# **************************************************
class MsgListener(jmri.jmrix.loconet.LocoNetListener):

    def message(self, msg):
        global aspectColor
        global accumByteCnt
        global address
        global address2
        global fbAddress
        global fbAddress2
        global command
        global command2
        
        ##global opcode
        global newMsgOpCodeHex,ARGS
        global BFsent
        global hiAddrByte
        global loAddrByte
        global firstBFE7
        global noSlotID
        
        global trolleyCnt
        global trolleyA,trolleyB,trolleyC
        global slotA,slotB,slotC
        global slotID
        global slotCnt
        global respCnt0xE7
        global notAlt0xE7
        global motionState
        
        global msgA
        global msgB
        global msgC
        
        if iTrace :
            print
        if iTrace :
            print "==>>entering MsgListener <--"
        newMsgOpCodeHex = msg.getOpCodeHex()
        newMsgLength = msg.getNumDataElements()
        accumByteCnt += newMsgLength
        # Note: accumByteCnt background task will read and be reset to zero and plotted every 1 second
        
        if lTrace : print "rcvd " + str(newMsgOpCodeHex)
        if sTrace : print "rcvd " + str(newMsgOpCodeHex)
        if bTrace : print "len = ",str(newMsgLength) + " msg = " + str(msg)

        ######################################################################################
        ## only listen for OPC_INPUT_REP message from trolley BODs (0xB2) going active (hi) ##
        ######################################################################################
        if (msg.getOpCode() == 178) and ((msg.getElement(2) & 0x10) == 0x10) :
            eventAddr = msg.sensorAddr() + 1
            if sTrace : print "== eventAddr = " + str(eventAddr)
            if eventAddr >= 100 and eventAddr <= 107 :
                if bTrace : print "eventAddr Rcvd = " + str(eventAddr) #gaw-debug
                if debounce :
                    sectionOccupied = checkSectionState(eventAddr)
                    if not sectionOccupied : #ignore if block is already occupied, signal must be due to contact bounce
                        doTrolleyStatusUpdate(eventAddr)
                else :
                    doTrolleyStatusUpdate(eventAddr) #direct call, no track contact bounce
                #autoTrolleySequencer(eventAddr)
                
                    
        #############################################################
        ## only listen for slot data response message (opcode 231) ##
        ## triggered by throttle requests 0xBF #OPC_LOCO_ADR       ##
        #############################################################
        if (msg.getOpCode() == 0xE7) and BFsent and (msg.getElement(4) == hiAddrByte) and (msg.getElement(9) == loAddrByte) : 
        ####if msg.getOpCode() == 0xE7 :
        ####if BFsent and (hiAddrByte == ARGS[4]) and (loAddrByte == ARGS[9]) :
            opcode = msg.getOpCode()
            if bTrace :
                print "opcode = " + hex(opcode)
            if sTrace : print "opcode = " + hex(opcode)
            ARGS[1] = msg.getElement(1)
            ARGS[2] = msg.getElement(2)
            ARGS[3] = msg.getElement(3)
            ARGS[4] = msg.getElement(4)
            ARGS[5] = msg.getElement(5)
            ARGS[6] = msg.getElement(6)
            ARGS[7] = msg.getElement(7)
            ARGS[8] = msg.getElement(8)
            ARGS[9] = msg.getElement(9)
            ARGS[10] = msg.getElement(10)
            ARGS[11] = msg.getElement(11)
            ARGS[12] = msg.getElement(12)
            #print "2 = " + str(ARGS[2])
            #print "4 = " + str(hex(ARGS[4]))
            #print "9 = " + str(hex(ARGS[9]))
            # check for E7 (opcode 231) response message after sending a BF query message (opcode 191)
            ####if BFsent and (hiAddrByte == ARGS[4]) and (loAddrByte == ARGS[9]) :
            if bTrace :
                print "BFsent4 = " + str(BFsent)
            slotID = ARGS[2] #set for later use
            if sTrace : print ">>slotID from ARGS[2] = " + str(ARGS[2])
            if firstBFE7 :
                firstBFE7 = False #only printed on first BFE7 pair
                if bTrace : print "2nd-trolleyA = " + str(trolleyA) + " and maps to slot " + str(slotA)
                if bTrace : print "2nd-trolleyB = " + str(trolleyB) + " and maps to slot " + str(slotB)
                if bTrace : print "2nd-trolleyC = " + str(trolleyC) + " and maps to slot " + str(slotC)
                if bTrace : print "E7slotID = " + hex(slotID)
                
        ####################################################
        ## prepare for automatic trolley sequencing if on ##
        ####################################################
        ####if BFsent :
            if respCnt0xE7 != -1 :
                respCnt0xE7 += 1
                if bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                
                if respCnt0xE7 == 1 :
                    if bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotA #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    slotA = slotID #store slotA value for later use
                    msgA = "trolleyA = " + str(trolleyA) + " and maps to slot " + str(slotA)
                    setSlotInuse() #got response to 0xBF request, now send 0xBA to set slot INUSE
                elif respCnt0xE7 == 2 :
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    if sTrace : print "BFsent is now False"
                    writeSlotData() #got response to 0xBA request, now send 0xEF to set  INUSE slot data
                    print msgA
                    scrollArea.setText(scrollArea.getText() + msgA + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before listening for next 0xE7
                    requestSlot(trolleyB) #get slot for next trolley address 
                elif respCnt0xE7 == 3 :
                    if bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotB #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    setSlotInuse()  #response to 0xBF request, follow by sending 0xBA to set slot INUSE
                    slotB = slotID #store slotB value for later use
                    msgB = "trolleyB = " + str(trolleyB) + " and maps to slot " + str(slotB)
                elif respCnt0xE7 == 4 :
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    if sTrace : print "BFsent is now False"
                    writeSlotData()
                    print msgB
                    scrollArea.setText(scrollArea.getText() + msgB + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before listening for next 0xE7
                    requestSlot(trolleyC)
                elif respCnt0xE7 == 5 :
                    if bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotC #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    setSlotInuse()  #response to 0xBF request, follow by sending 0xBA to set slot INUSE
                    slotC =  slotID #store slotC value for later use
                    msgC = "trolleyC = " + str(trolleyC) + " and maps to slot " + str(slotC)
                else : # can only be respCnt0xE7 == 6
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    ####print "Last 0xBF done, no more will be sent"
                    #ignore 0xE7 response to 0xBA request, follow by sending 0xEF to set INUSE slot data
                    writeSlotData()
                    print msgC
                    scrollArea.setText(scrollArea.getText() + msgC + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before announcing done
                    respCnt0xE7 = -1 #all done setting slots
                    
                    ATSmsg = "The Automatic Trolley Sequencer is now running."
                    print ATSmsg
                    scrollArea.setText(scrollArea.getText() + ATSmsg + "\n")
                    # this is where you select the voice synthesizer (speak, espeak, or nircmd)
                    if snSpkChgCheckBox.isSelected():
                        #pid = java.lang.Runtime.getRuntime().exec(["speak", msg])
                        # #pid = java.lang.Runtime.getRuntime().exec(["C:\Program Files (x86)\eSpeak\command_line\espeak", msg])
                        pid = java.lang.Runtime.getRuntime().exec('nircmd speak text "' + ATSmsg + '" -2 100')
                        pid.waitFor()
                        
        if oTrace : print "<<==exiting MsgListener"
        inE7 = False
        return

# *************************************************************************
# Add the next Loconet messsage to the scroll area text                   *
# If the raw box is checked add the HEX message value in front of message *
# *************************************************************************
def displayMsg(msg):
    log.info("sensors is {}", sensors)
    log.info("msg is {}", msg)
    #scrollArea.setText(scrollArea.getText()+"got to displayMsg\n") #displayMessage adds a carriage return
    if timeCheckBox.isSelected():
        scrollArea.setText(scrollArea.getText() + time.strftime('%X:') + " ")
    if rawCheckBox.isSelected():
        #scrollArea.setText(scrollArea.getText() + "[" + msg.encode("utf-8") + "] ")
        scrollArea.setText(scrollArea.getText() + "[" + msg.toString() + "] ")
    scrollArea.setText(scrollArea.getText() + parseMsg.displayMessage(msg)) #displayMessage adds a carriage return
    #[replace with none parseMsg version if line above is commented and line below is uncommented]
    #scrollArea.setText(scrollArea.getText()+msg+"\n") #displayMessage adds a carriage return
    return
    
# *************************************************************************
# Add the next Loconet messsage translation to the scroll area text       *
# If the raw box is checked add the HEX message value in front of message *
# *************************************************************************
def displayTxt(msg) :
    #scrollArea.setText(scrollArea.getText()+"got to displayTxt\n") #displayMessage adds a carriage return
    if timeCheckBox.isSelected() :
        scrollArea.setText(scrollArea.getText()+time.strftime('%X:')+" ")           
    if rawCheckBox.isSelected() :
        #scrollArea.setText(scrollArea.getText()+"["+msg.toString()+"] ")
        #scrollArea.setText(scrollArea.getText()+"["+msg.encode("utf-8").toString()+"] ")
        scrollArea.setText(scrollArea.getText() + "[" + msg.encode("utf-8") + "] ")
    #scrollArea.setText(scrollArea.getText()+parseMsg.displayMessage(msg)) #displayMessage adds a carriage return
    #[replace with none parseMsg version if line above is commented and line below is uncommented]
    scrollArea.setText(scrollArea.getText() + msg + "\n") #displayMessage adds a carriage return
    #time.sleep(0.03) #sleep for a 30 ms to allow foreground to run
    
    return
    
# ##########################################################################
# ************* Start of Main Setup
# ##########################################################################

# *************************************
# start to initialise the display GUI *
# *************************************

# =================================
# create buttons and define action
# =================================
enterButton = javax.swing.JButton("Start the Run")
enterButton.setEnabled(False)           #button starts as grayed out (disabled)
enterButton.actionPerformed = whenEnterButtonClicked

resyncButton = javax.swing.JButton("Resync")
resyncButton.actionPerformed = whenResyncButtonClicked

saveTaddrsButton = javax.swing.JButton("SaveTaddresses")
saveTaddrsButton.actionPerformed = whenSaveTaddressesButtonClicked

#clearButton = javax.swing.JButton("Clear")
#clearButton.actionPerformed = whenClearButtonClicked

quitButton = javax.swing.JButton("Quit")
quitButton.actionPerformed = whenQuitButtonClicked

tgoButton = javax.swing.JButton("Start Running")
tgoButton.actionPerformed = whenTgoButtonClicked

tstopButton = javax.swing.JButton("AllTstop")
tstopButton.actionPerformed = whenTstopAllButtonClicked

# ====================================
# create checkboxes and define action
# ====================================
swAddrCheckBox = javax.swing.JCheckBox("Filter Sw address")
swAddrCheckBox.setToolTipText("Display all switch messages or with the address")
#swAddrCheckBox.setEnabled(False)           #button starts as grayed out (disabled)

snAddrCheckBox = javax.swing.JCheckBox("Filter Sn address")
snAddrCheckBox.setToolTipText("Display all sensor messages or with the address")
#snAddrCheckBox.setEnabled(False)           #button starts as grayed out (disabled)

fbAddrCheckBox = javax.swing.JCheckBox("Filter Fb address")
fbAddrCheckBox.setToolTipText("Display all feedback messages or with the address")

filterCheckBox = javax.swing.JCheckBox("Filter SW, FB & SN")
filterCheckBox.setToolTipText("Display switch, feedback or sensor messages")

rawCheckBox = javax.swing.JCheckBox("Show raw data")

timeCheckBox = javax.swing.JCheckBox("Show time stamp")

indexCheckBox = javax.swing.JCheckBox("Show msg string index")

snChgCheckBox = javax.swing.JCheckBox("Show Sn Change")
snChgCheckBox.setToolTipText("Display when a sensor state changes")

snSpkChgCheckBox = javax.swing.JCheckBox("Speak Sn Change")
snSpkChgCheckBox.setToolTipText("Speak when a sensor state changes")

sigChgCheckBox = javax.swing.JCheckBox("Show Signal Decode Only")
sigChgCheckBox.setToolTipText("Display when a Signal state changes")

sigSpkChgCheckBox = javax.swing.JCheckBox("Speak Signal Change")
sigSpkChgCheckBox.setToolTipText("Speak when a signal aspect changes")

# =====================================
# create text fields and define action
# =====================================
address = javax.swing.JTextField(5)    #sized to hold 5 characters, initially empty
#address.actionPerformed = whenAddressChanged   #if user hit return or enter
#address.focusLost = whenAddressChanged         #if user tabs away
address2 = javax.swing.JTextField(5)    #sized to hold 5 characters, initially empty

fbAddress = javax.swing.JTextField(5)
fbAddress2 = javax.swing.JTextField(5)

# create the another text field similarly
command = javax.swing.JTextField(5)    #sized to hold 5 characters
command.setToolTipText("Number from 1 to 2010")
#command.actionPerformed = whenCommandChanged
#command.focusLost = whenCommandChanged

# create the another text field
# before this text field works there must be a number in the command field
command2 = javax.swing.JTextField(5)    #sized to hold 5 characters
command2.setToolTipText("Number from 1 to 2010")
#command2.actionPerformed = whenCommandChanged
#command2.focusLost = whenCommandChanged

# create another text field for a range address
rangeAdd1 = javax.swing.JTextField(5)    #sized to hold 5 characters
rangeAdd1.setToolTipText("Start address")

# create another text field for a trolleyB
rangeAdd2 = javax.swing.JTextField(5)    #sized to hold 5 characters
rangeAdd2.setToolTipText("End address")

# create another text field for a trolleyA
trolleyAaddr = javax.swing.JTextField(5)    #sized to hold 5 characters
trolleyAaddr.setToolTipText("1st Trolley Address")

# create another text field for a trolleyB
trolleyBaddr = javax.swing.JTextField(5)    #sized to hold 5 characters
trolleyBaddr.setToolTipText("2nd Trolley Address")

# create another text field for a trolleyC
trolleyCaddr = javax.swing.JTextField(5)    #sized to hold 5 characters
trolleyCaddr.setToolTipText("3rd Trolley Address")

# create another text field for a trolleyA
trolleyAspeed = javax.swing.JTextField(3)    #sized to hold 3 characters
trolleyAspeed.setToolTipText("1st Trolley Speed")

# create another text field for a trolleyB
trolleyBspeed = javax.swing.JTextField(3)    #sized to hold 3 characters
trolleyBspeed.setToolTipText("2nd Trolley Speed")

# create another text field for a trolleyC
trolleyCspeed = javax.swing.JTextField(3)    #sized to hold 3 characters
trolleyCspeed.setToolTipText("3rd Trolley Speed")

# create a text area
scrollArea = javax.swing.JTextArea(10, 45)    #define a text area with it's size
scrollArea.getCaret().setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE); # automatically scroll to last message
scrollArea.font=Font("monospaced", Font.PLAIN, 14)
# scrollArea.setText("Put any init text here\n")
scrollField = javax.swing.JScrollPane(scrollArea) #put text area in scroll field
scrollField.setHorizontalScrollBarPolicy(javax.swing.JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
scrollField.setVerticalScrollBarPolicy(javax.swing.JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)

# ---------------------------------------------------------------------------------
# create a panel to put the scroll area in
# a borderlayout causes the scroll area to fill the space as the window is resized
# ---------------------------------------------------------------------------------
midPanel = javax.swing.JPanel()
# midPanel.setBorder(javax.swing.BorderFactory.createMatteBorder(1,8,1,8, java.awt.Color.white))
midPanel.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 8, 1, 8))
midPanel.setLayout(java.awt.BorderLayout())
midPanel.add(scrollField)

# ------------------------------------------------------------------------------------------
# create a frame to hold the buttons and fields
# also create a window listener. This is used mainly to remove the property change listener
# when the window is closed by clicking on the window close button
# ------------------------------------------------------------------------------------------
w = WinListener()
#fr = javax.swing.JFrame(apNameVersion)       #argument is the frames title
fr = jmri.util.JmriJFrame(apNameVersion) #use this in order to get it to appear on webserver
fr.contentPane.setLayout(javax.swing.BoxLayout(fr.contentPane, javax.swing.BoxLayout.Y_AXIS))
fr.addWindowListener(w)

# -------------------------------------------------
# put the text field on a line preceded by a label
# -------------------------------------------------
addressPanel = javax.swing.JPanel()
addressPanel.setLayout(java.awt.FlowLayout(2))    #2 is right align for FlowLayout
addressPanel.add(javax.swing.JLabel("Sw Addresses"))
addressPanel.add(address)
addressPanel.add(javax.swing.JLabel("or"))
addressPanel.add(address2)

# ---------------------------------------------------------------------------------------
fbAddressPanel = javax.swing.JPanel()
fbAddressPanel.setLayout(java.awt.FlowLayout(2))    #2 is right align for FlowLayout
fbAddressPanel.add(javax.swing.JLabel("Fb Addresses"))
fbAddressPanel.add(fbAddress)
fbAddressPanel.add(javax.swing.JLabel("or"))
fbAddressPanel.add(fbAddress2)

# ---------------------------------------------------------------------------------------
commandPanel = javax.swing.JPanel()
commandPanel.setLayout(java.awt.FlowLayout(2))    #2 is right align for FlowLayout
commandPanel.add(javax.swing.JLabel("Sn Addresses"))
commandPanel.add(command)
commandPanel.add(javax.swing.JLabel("or"))
commandPanel.add(command2)

# ---------------------------------------------------------------------------------------
rangePanel = javax.swing.JPanel()
rangePanel.setLayout(java.awt.FlowLayout(2))    #2 is right align for FlowLayout
rangePanel.add(javax.swing.JLabel("Sn Addr Range"))
rangePanel.add(rangeAdd1)
rangePanel.add(javax.swing.JLabel("to"))
rangePanel.add(rangeAdd2)

# ---------------------------------------------------------------------------------------
temppanel1 = javax.swing.JPanel()
temppanel1.setLayout(javax.swing.BoxLayout(temppanel1, javax.swing.BoxLayout.PAGE_AXIS))
temppanel1.add(addressPanel)
temppanel1.add(fbAddressPanel)
temppanel1.add(commandPanel)
temppanel1.add(rangePanel)

# ---------------------------------------------------------------------------------------
ckBoxPanel = javax.swing.JPanel()
ckBoxPanel.setLayout(javax.swing.BoxLayout(ckBoxPanel, javax.swing.BoxLayout.PAGE_AXIS))
ckBoxPanel.add(filterCheckBox)
ckBoxPanel.add(swAddrCheckBox)
ckBoxPanel.add(fbAddrCheckBox)
ckBoxPanel.add(snAddrCheckBox)
ckBoxPanel.add(rawCheckBox)
ckBoxPanel.add(timeCheckBox)
ckBoxPanel.add(indexCheckBox)
ckBoxPanel.add(snChgCheckBox)
ckBoxPanel.add(snSpkChgCheckBox)
ckBoxPanel.add(sigChgCheckBox)
ckBoxPanel.add(sigSpkChgCheckBox)

# ---------------------------------------------------------------------------------------
butPanel = javax.swing.JPanel()
####butPanel.setLayout(java.awt.FlowLayout(2))    #2 is right align for FlowLayout
butPanel.setLayout(javax.swing.BoxLayout(butPanel, javax.swing.BoxLayout.PAGE_AXIS))
####butPanel.add(resyncButton)
####butPanel.add(javax.swing.Box.createVerticalStrut(20)) #empty vertical space between buttons
#butPanel.add(clearButton) #currently inoperative and appears to be no longer needed

#butPanel.add(javax.swing.Box.createVerticalStrut(20)) #empty vertical space between buttons
butPanel.add(saveTaddrsButton)
butPanel.add(javax.swing.Box.createVerticalStrut(10)) #empty vertical space between buttons
butPanel.add(javax.swing.JLabel("T1 Address"))
butPanel.add(trolleyAaddr)
butPanel.add(javax.swing.JLabel("Speed"))
butPanel.add(trolleyAspeed)
butPanel.add(javax.swing.Box.createVerticalStrut(10)) #empty vertical space between buttons
butPanel.add(javax.swing.JLabel("T2 Address"))
butPanel.add(trolleyBaddr)
butPanel.add(javax.swing.JLabel("Speed"))
butPanel.add(trolleyBspeed)
butPanel.add(javax.swing.Box.createVerticalStrut(10)) #empty vertical space between buttons
butPanel.add(javax.swing.JLabel("T3 Address"))
butPanel.add(trolleyCaddr)
butPanel.add(javax.swing.JLabel("Speed"))
butPanel.add(trolleyCspeed)
butPanel.add(javax.swing.Box.createVerticalStrut(10)) #empty vertical space between buttons
butPanel.add(tgoButton)
butPanel.add(javax.swing.Box.createVerticalStrut(20)) #empty vertical space between buttons
butPanel.add(tstopButton)

# ---------------------------------------------------------------------------------------
buttonPanel = javax.swing.JPanel()
buttonPanel.add(butPanel)

# ---------------------------------------------------------------------------------------
blankPanel = javax.swing.JPanel()
blankPanel.setLayout(java.awt.BorderLayout())

entryPanel = javax.swing.JPanel()
entryPanel.setLayout(javax.swing.BoxLayout(entryPanel, javax.swing.BoxLayout.LINE_AXIS))
####entryPanel.add(temppanel1)
####entryPanel.add(ckBoxPanel)
entryPanel.add(buttonPanel)
entryPanel.add(blankPanel)

# ---------------------------------------------------------------------------------------
# create the top panel
# it is a 1,1 GridLayout used to keep all controls stationary when the window is resized
# ---------------------------------------------------------------------------------------
topPanel = javax.swing.JPanel()
topPanel.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 8, 8, 8))
topPanel.setLayout(java.awt.GridLayout(1, 1))
topPanel.add(entryPanel)

# -------------------------------------------------------------------
# create a bottom panel to give some space under the scrolling field
# -------------------------------------------------------------------
bottomPanel = javax.swing.JPanel()
# bottomPanel.setBorder(javax.swing.BorderFactory.createEmptyBorder(1,8,1,8))

# ------------------------------------
# create a time series charting panel
# ------------------------------------
# ----------------------------------
# Put contents in frame and display
# ----------------------------------
fr.contentPane.add(topPanel)
fr.contentPane.add(midPanel)
fr.contentPane.add(bottomPanel)
fr.pack()
#fr.show() #depreciated
fr.setVisible(True)

# ---------------------------------
# create and start LocoNet listener
# ---------------------------------
lnListen = MsgListener() #create and start LocoNet listener
jmri.jmrix.loconet.LnTrafficController.instance().addLocoNetListener(0xFF, lnListen)

# --------------------------------------------------------------------------------
# force first three points to min and max of plot range to set range (not needed)
# --------------------------------------------------------------------------------
#series.add(Millisecond(), 0.0)    #set first point to min scale range value
#time.sleep(0.1) # sleep for tenth of a second
#series.add(Millisecond(), 2000.0) #set second point to max scale range value
#time.sleep(0.1) # sleep for tenth of a second
#series.add(Millisecond(), 0.0)    #set third point to min scale range value

if bTrace : scrollArea.setText(scrollArea.getText() + mainStartTime + "\n")
else : scrollArea.setText(scrollArea.getText() + "Init started\n")
if bTrace : scrollArea.setText(scrollArea.getText() + "[1]" + time.strftime('%X %x %Z') + "\n")

# #############################################
# # ************* Start of Main ************* #
# #############################################
print apNameVersion + ' now running'

# **************************************************************
# populate PropertyChangeListener with Sensor Message pointers *
# **************************************************************
snrStatusArr = {} # dictionary of sensor systemNames and status
for systemName in sensors.getSystemNameList():
    sensor = sensors.getSensor(systemName)
    userName = sensor.userName
    # add sensors with a userName starting with userNamePrefix to snrStatusArr
    # and set the initial state for that sensor
    # (test that userName is not null first)
    if userName and userName.startswith(userNamePrefix):
        snrStatusArr[systemName] = sensor.knownState
        sensor.addPropertyChangeListener(listener)

scrollArea.setText(scrollArea.getText() + str(len(snrStatusArr)) + " short detectors\n")

if bTrace : scrollArea.setText(scrollArea.getText() + "[2]" + time.strftime('%X %x %Z') + "\n")
if bTrace : scrollArea.setText(scrollArea.getText() + "[3]" + time.strftime('%X %x %Z') + "\n")
if bTrace : scrollArea.setText(scrollArea.getText() + "[4]" + time.strftime('%X %x %Z') + "\n")
if bTrace : scrollArea.setText(scrollArea.getText() + "[5]" + time.strftime('%X %x %Z') + "\n")

scanPntr = 0 # set starting value of scanning pointer to point to first entry
if bTrace : scrollArea.setText(scrollArea.getText() + "[6]" + time.strftime('%X %x %Z') + "\n")

# ******************************************************
# * readin new trolley addresses if config file exists *
# ******************************************************
print "attempting to read in trolley addresses read in from " + trolleyAddressesFile
if os.path.isfile(trolleyAddressesFile):
    fp=open(trolleyAddressesFile,'r')
    trolleyA=int(fp.readline())
    print "read trolleyA as "+ str(trolleyA)
    trolleyB=int(fp.readline())
    print "read trolleyB as "+ str(trolleyB)
    trolleyC=int(fp.readline())
    print "read trolleyC as "+ str(trolleyC)
    maxSpeed[0] = int(fp.readline())
    print "read maxSpeed[0] as "+ str(maxSpeed[0])
    maxSpeed[1] = int(fp.readline())
    print "read maxSpeed[1] as "+ str(maxSpeed[1])
    maxSpeed[2] = int(fp.readline())
    print "read maxSpeed[2] as "+ str(maxSpeed[2])
    fp.close()
    print "trolley addresses and speeds read in from " + trolleyAddressesFile
else:
    print "saveTaddresses.cfg file did not exist, using defaults"
trolleyAaddr.text = str(trolleyA)
trolleyBaddr.text = str(trolleyB)
trolleyCaddr.text = str(trolleyC)
trolleyAspeed.text = str(maxSpeed[0])
trolleyBspeed.text = str(maxSpeed[1])
trolleyCspeed.text = str(maxSpeed[2])

# init done
if bTrace : scrollArea.setText(scrollArea.getText()+"[init ended]"+time.strftime('%X %x %Z')+"\n")
else : scrollArea.setText(scrollArea.getText()+"Init done\n")
print 'init done'

# ##########################################
# # my default startup test settings - gaw #
# ##########################################
rangeAdd1.text = '3000' #lower address boundary 3000
rangeAdd2.text = '4080' #upper address boundary 4080
snChgCheckBox.setSelected(True) #sensor change message display on
snSpkChgCheckBox.setSelected(True) #sensor change message spoken on

# #########################################################################
# ************* Start of Background Tasks from Main and other final steps #
# #########################################################################
#send 1st 0xBF (ask for a slot)
requestSlot(trolleyA)
if bTrace : print "BFsent-A = " + str(BFsent)
    
# ###########################################
# # ************* End of Main ************* #
# ###########################################
