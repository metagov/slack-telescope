from app.rid_types import Telescoped
from app.core import effector
from app.slack_interface.components import *
from .retract import create_retract_interaction
from .broadcast import create_broadcast


def accept_and_process(message):
    create_retract_interaction(message)
    create_broadcast(message)
    effector.dereference(Telescoped(message), refresh=True)
    