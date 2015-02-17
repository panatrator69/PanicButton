# Import required libraries
import RPi.GPIO as GPIO
import time
import os
import pjsua as pj
import sys
import smtplib
from email.mime.text import MIMEText



###############################################
## CALL BACK FUNCTIONS AND CLASSES FOR PJSUA ##
###############################################

# define a function to print out call back logs to the terminal
def log_cb(level,str,len):
    print str

# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        print "Call is ", self.call.info().state_text,
        print "last code =", self.call.info().last_code,
        print "(" + self.call.info().last_reason + ")"

    # Notification when call's media state has changed.
    def on_media_state(self):
        # Connect egress and regress channels to each other
        global lib
        global wav_player

        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Set the media player to play at the beginning of the file
            lib.player_set_pos(wav_player,0)

            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            lib.conf_connect(wav_slot,call_slot)

# Define AccountCallback Class for Registrations
class MyAccountCallback(pj.AccountCallback):
    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    # On incoming calls to defined acct, display message to terminal
    def on_incoming_call(self, call):
        call.hangup(501, "Sorry, not ready to accept calls yet")

    # Output the registration status on register status change
    def on_reg_state(self):
        print "Registration status=", self.account.info().reg_status, \
        "(" + self.account.info().reg_reason + ")"


########################
## GPIO INITIAL SETUP ##
########################

# Static Variables. The Pin used for reading button presses
pinIn = 7

# Set GPIO Pin Mode to Board (Rasp Pi Convention)
GPIO.setmode(GPIO.BOARD)

# Enable Pin 7 as an input, If the button is pressed,
# the pin will read false(low)
GPIO.setup(pinIn,GPIO.IN,pull_up_down = GPIO.PUD_UP)

# Store the state of pin 7 into input variable
reading = not GPIO.input(pinIn)

# Bool to indicate if the button has been reset to off position
# After being depressed
buttonReset = True

########################
## SMTP LIBRARY SETUP ##
########################

# Create a SMTP server instance
# 587 is the default SMTP port
server = smtplib.SMTP("your.smtp.server.com",587)

# Open the text file fo reading in ASCII format. Store in msg
# and add all the relevant details to the msg variable with its
# members
email="email.txt"
fp = open(email,"rb")
msg = MIMEText(fp.read())
fp.close()

sender = "panic@shanepan.com"
recipients = ["r1@shanepan.com","r2@shanepan.com","r3@shanepan.com"]

msg["Subject"] = "The Panic button has been pressed"
msg["From"] = sender
msg["To"] = ", ".join(recipients)



#########################
## PJSUA LIBRARY SETUP ##
#########################

# Create library instance
lib = pj.Lib()

# Init library with verbose level 3 and callback log function from mcb module
# Verbosity goes from level 1 (lowest) to 7 (highest)
lib.init(log_cfg = pj.LogConfig(level=3, callback=mcb.log_cb))

# Set the library to not send audio through any physical devices
# (No sound input from microphone)
lib.set_null_snd_dev()

# Create UDP transport which listens to any available port
transport = lib.create_transport(pj.TransportType.UDP)

# Start the library
lib.start()

# Instantiate the WAV Player with the WAV file playing
wav_player = lib.create_player("/root/Panic/playback.wav",loop=True)
wav_slot = lib.player_get_slot(wav_player)

# Asterisk PBX Server IP stored in a string
pbxIP= "10.10.10.10"

# Create local/user-less account
acc_cfg = pj.AccountConfig()
acc_cfg.id = "sip:100@" + pbxIP
acc_cb = mcb.MyAccountCallback()
acc = lib.create_account(acc_cfg, cb=acc_cb)

# Edit the callDestExt Array to change which extensions to dial. They"re strings!
# Call Destinations
callDestExt = ["101","102","103"]
callDestURI = []
callInstances = {}

# Store the destination URI"s in a list and create
# a dictionary with null members for the call instances that we will make later
for ext in callDestExt:
    callDestURI.append("sip:"+ext+pbxIP)
    callInstances[ext] = None

#Event Loop
while True:
    #take a reading
    reading = not GPIO.input(pinIn)
    
    #If the switch is depressed to on position and the button has been reset before
    if reading is True and buttonReset:
        print("Button pressed")

        # The button has now been depressed so it has not been reset yet.
        # Put this statment here so that there is not an infinite loop if
        # either the email or call fail.
        buttonReset = False
                
        # Send the email 
        print("Sending email via SMTP")
        try:
            server.sendmail(sender,recipients,msg.as_string())
            print("Emailing out finished")
        except SMTPException:
            print("error in sending out the email: ",SMTPException)
        except:
            print("major error occured in sending out the email")

        # Trying to call out
        print("Trying to call out")
        try:
            # Create call instances in the callInstances dictionary corresponding to the extension key for the dict
            for uri in callDestURI:
                extension=uri.split(":")[1].split("@")[0]
                callInstances[extension] = acc.make_call(uri,mcb.MyCallCallback())
            print("Callout done")
        except pj.Error:
            print("Error making outgoing call:",pj.Error)
        except:
            print("Major error in making the SIP call")


    
    # Whenever the button becomes depressed and has not been reset
    # change the buttonReset variable to true so it can wait
    # for another button press
    if reading is not False and not buttonReset:
        print("The button has been reset")
        buttonReset = True

        # Hangup all cals if the button is depressed after being pressed
        lib.hangup_all()    

    # Take a reading every 5 miliseconds        
    time.sleep(0.05)



