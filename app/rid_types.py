from rid_lib.core import ORN, RID
from rid_lib.types import SlackMessage

class Telescoped(ORN):
    namespace = "telescoped"
    
    def __init__(self, slack_message: SlackMessage):
        self.slack_message = slack_message
        
    @property
    def reference(self):
        return str(self.slack_message)
    
    @classmethod
    def from_reference(cls, reference):
        return cls(cls.from_string(reference))