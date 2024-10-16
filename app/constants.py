class UserStatus:
    UNSET = None
    PENDING = "pending"
    OPT_IN = "opt_in"
    OPT_IN_ANON = "opt_in_anon"
    OPT_OUT = "opt_out"

class MessageStatus:
    UNSET = None
    TAGGED = "tagged"
    REQUESTED = "requested"
    IGNORED = "ignored"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RETRACTED = "retracted"
    
status_emojis = {
    MessageStatus.TAGGED: ":label:",
    MessageStatus.REQUESTED: ":hourglass_flowing_sand:",
    MessageStatus.IGNORED: ":wave:",
    MessageStatus.ACCEPTED: ":white_check_mark:",
    MessageStatus.REJECTED: ":x:",
    MessageStatus.RETRACTED: ":no_entry_sign:"
}
    
class ActionId:
    REQUEST = "request"
    IGNORE = "ignore"
    OPT_IN = "opt_in"
    OPT_IN_ANON = "opt_in_anon"
    OPT_OUT = "opt_out"
    RETRACT = "retract"
    
class BlockId:
    REQUEST = "request"
    CONSENT = "consent"
    RETRACT = "retract"