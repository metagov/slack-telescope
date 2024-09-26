
def build_request_component(tagger, author):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Posted by *{author_name}*\n" + indented_text
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<#{tagged_msg.channel_id}> | Tagged by {tagger_name} | <{permalink}|Jump to message>"
                }
            ]
        },
        {
            "type": "actions",
            "block_id": "pending_message",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Request"
                    },
                    "style": "primary",
                    "action_id": "request_button",
                    "value": action_payload
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Cancel"
                    },
                    "action_id": "cancel_button",
                    "value": action_payload
                }
            ]
        }
    ]