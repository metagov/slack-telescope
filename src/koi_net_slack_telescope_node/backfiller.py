import threading
import asyncio
from logging import Logger
from dataclasses import dataclass, field

from slack_bolt import App
from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackMessage, SlackUser
from rid_lib.ext import Bundle
from koi_net.components import Effector, KobjQueue
from koi_net.components.interfaces import ThreadedComponent

from .orchestrator import Orchestrator
from .config import SlackTelescopeNodeConfig


@dataclass
class TelescopeBackfiller(ThreadedComponent):
    log: Logger
    async_slack_app: AsyncApp
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
        asyncio.run(self.backfill_telescopes())
        
    def process_message(self, channel_id: str, message: dict):
        found_telescope = False
        tagger_user_id = None
        for reaction in message.get("reactions", []):
            if reaction["name"] == self.config.telescope.emoji:
                found_telescope = True
                tagger_user_id = reaction["users"][0]
                break
        
        author_user_id = message.get("user")
        
        if not found_telescope:
            return
        
        message_rid = SlackMessage(
            team_id=self.config.telescope.team_id,
            channel_id=channel_id,
            ts=message["ts"]
        )
        
        self.log.info(f"Found telescoped message: {message_rid}")
        
        message_bundle = Bundle.generate(message_rid, message)
        self.kobj_queue.push(bundle=message_bundle)
        
        author = SlackUser(self.config.telescope.team_id, author_user_id)
        tagger = SlackUser(self.config.telescope.team_id, tagger_user_id)
        
        self.orchestrator.create_request_interaction(message_rid, author, tagger)
            
    async def auto_retry(self, func, **kwargs):
        try:
            return await func(**kwargs)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                retry_after = int(e.response.headers["Retry-After"])
                self.log.info(f"timed out, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
                return await func(**kwargs)
            
            elif e.response["error"] == "not_in_channel":
                self.log.info(f"not in channel {kwargs['channel']}, attempting to join")
                await self.async_slack_app.client.conversations_join(channel=kwargs["channel"])
                return await func(**kwargs)

            else:
                self.log.warning(f"Unknown error during backfill: {str(e)}")
    
    async def backfill_telescopes(self):
        self.log.info("Beginning Telescope backfill...")

        # get list of channels
        channel_cursor = None
        channels = [{"id": channel_id for channel_id in self.config.telescope.allowed_channels}]
        while (not channels or channel_cursor) and not self.should_exit.is_set():
            resp = await self.async_slack_app.client.conversations_list(cursor=channel_cursor)
            result = resp.data
            channels.extend(result["channels"])
            self.log.info(f"Found {len(channels)} channels")
            channel_cursor = result.get("response_metadata", {}).get("next_cursor")
        
        self.log.info(f"Found {len(channels)} channels")
        for channel in channels:
            channel_id = channel["id"]
            
            if channel.get("is_archived"):
                self.log.debug(f"Skipping archived channel {channel['name']}")
                continue
            
            # get list of messages in channel
            message_cursor = None
            messages: list[dict] = []
            while (not messages or message_cursor) and not self.should_exit.is_set():
                result = await self.auto_retry(
                    func=self.async_slack_app.client.conversations_history,
                    channel=channel_id,
                    limit=500,
                    cursor=message_cursor,
                    oldest=self.config.telescope.last_processed_ts
                )
                
                messages.extend(result["messages"])
                if result["has_more"]:
                    message_cursor = result["response_metadata"]["next_cursor"]
                else:
                    message_cursor = None

            self.log.info(f"Found {len(messages)} messages in {channel_id}")
            messages.sort(key=lambda msg: msg["ts"])
            for message in messages:
                if self.should_exit.is_set():
                    return
                
                thread_ts = message.get("thread_ts")
                
                # ignore threaded messages sent to channel
                if thread_ts and (thread_ts != message["ts"]):
                    continue
                
                self.process_message(channel_id, message)
                
                if thread_ts:
                    threaded_message_cursor = None
                    threaded_messages = []
                    while not threaded_messages or threaded_message_cursor:
                        result = await self.auto_retry(
                            func=self.async_slack_app.client.conversations_replies,
                            channel=channel_id,
                            ts=thread_ts,
                            limit=500,
                            cursor=threaded_message_cursor,
                            oldest=self.config.telescope.last_processed_ts
                        )
                        
                        threaded_messages.extend(result["messages"])
                        
                        if result["has_more"]:
                            threaded_message_cursor = result["response_metadata"]["next_cursor"]
                        else:
                            threaded_message_cursor = None
                    
                    
                    for threaded_message in threaded_messages[1:]:
                        self.process_message(channel_id, threaded_message)
