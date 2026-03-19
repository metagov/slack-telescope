import threading
from logging import Logger
from dataclasses import dataclass, field

from slack_sdk import WebClient
from rid_lib.types import SlackMessage, SlackUser
from rid_lib.ext import Bundle
from koi_net.components import Effector, KobjQueue
from koi_net.components.interfaces import ThreadedComponent

from .consts import MessageStatus

from .persistent import PersistentMessage

from .orchestrator import Orchestrator
from .config import SlackTelescopeNodeConfig


@dataclass
class TelescopeBackfiller(ThreadedComponent):
    log: Logger
    slack_user_client: WebClient
    kobj_queue: KobjQueue
    effector: Effector
    orchestrator: Orchestrator
    config: SlackTelescopeNodeConfig
    
    should_exit: threading.Event = field(init=False, default_factory=threading.Event)
    
    def start(self):
        self.should_exit.clear()
        super().start()
        
    def stop(self):
        self.should_exit.set()
        super().stop()
            
    def run(self):
        self.backfill_telescopes()
        
    def process_message(self, message: dict):
        message_rid = SlackMessage(
            team_id=self.config.telescope.team_id,
            channel_id=message["channel"]["id"],
            ts=message["ts"]
        )
        
        if PersistentMessage(message_rid).status is not MessageStatus.UNSET:
            return
        
        self.log.info(f"Identified unhandled telescope message: {message_rid}")
        
        msg_bundle = self.effector.deref(message_rid)
        if not msg_bundle:
            self.log.warning("Failed to dereference telescope message")
            return
        
        author_user_id = message["user"]
        tagger_user_id = None
        for reaction in msg_bundle.contents.get("reactions", []):
            if reaction["name"] == self.config.telescope.emoji:
                tagger_user_id = reaction["users"][0]
                break
            
        if not tagger_user_id:
            self.log.warning("Failed to find telescope reaction on message")
            return
        
        author = SlackUser(self.config.telescope.team_id, author_user_id)
        tagger = SlackUser(self.config.telescope.team_id, tagger_user_id)
        
        self.orchestrator.create_request_interaction(message_rid, author, tagger)
            
    def backfill_telescopes(self):
        query_fields = [f"has::{self.config.telescope.emoji}:"]
        query_fields.extend([
            f"in:<#{channel}>" 
            for channel in self.config.telescope.allowed_channels
        ])
        query = " ".join(query_fields)
        
        self.log.info(f"Submitting query: `{query}`")
        
        max_pages = None
        curr_page = 1
        messages = []
        while (max_pages is None or curr_page <= max_pages) and (self.should_exit is not None):
            resp = self.slack_user_client.search_messages(
                query=query,
                page=curr_page,
                count=100,
                sort="timestamp",
                sort_dir="asc"
            )
            
            result = resp["messages"]
            messages.extend(result["matches"])
            
            max_pages = result["paging"]["pages"]
            curr_page += 1
            
        for message in messages:
            self.process_message(message)
            
