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
        ######################################################
        # CONNECT EGRESS AND INGRESS CHANNELS ON CALL PICKUP #
        ######################################################
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
