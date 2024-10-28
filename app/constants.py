class UserStatus:
    UNSET = None
    PENDING = "pending"
    OPT_IN = "opt_in"
    OPT_IN_ANON = "opt_in_anon"
    OPT_OUT = "opt_out"

class MessageStatus:
    UNSET = None
    TAGGED = "tagged"
    UNREACHABLE = "unreachable"
    REQUESTED = "requested"
    IGNORED = "ignored"
    ACCEPTED = "accepted"
    ACCEPTED_ANON = "accepted_anon"
    REJECTED = "rejected"
    RETRACTED = "retracted"
    
status_display = {
    MessageStatus.TAGGED: "Tagged :label:",
    MessageStatus.REQUESTED: "Requested :hourglass_flowing_sand:",
    MessageStatus.IGNORED: "Ignored :wave:",
    MessageStatus.ACCEPTED: "Accepted :white_check_mark:",
    MessageStatus.ACCEPTED_ANON: "Accepted :white_check_mark: (anonymously)",
    MessageStatus.REJECTED: "Rejected :x:",
    MessageStatus.RETRACTED: "Retracted :no_entry_sign:"
}
    
class ActionId:
    REQUEST = "request"
    IGNORE = "ignore"
    UNDO_IGNORE = "undo_ignore"
    OPT_IN = "opt_in"
    OPT_IN_ANON = "opt_in_anon"
    OPT_OUT = "opt_out"
    RETRACT = "retract"
    
class BlockId:
    REQUEST = "request"
    ALT_REQUEST = "alt_request"
    CONSENT = "consent"
    RETRACT = "retract"