def text_obj(text, type="plain_text"):
    return {
        "type": type,
        "text": text
    }

def section_block(text_obj):
    return {
        "type": "section",
        "text": text_obj
    }

def context_block(elements: list):
    return {
        "type": "context",
        "elements": elements
    }
    
def action_block(block_id, elements: list):
    return {
        "type": "actions",
        "block_id": block_id,
        "elements": elements
    }
    
def button_block(action_id, text_obj, value, style=None):
    return {
        "type": "button",
        "action_id": action_id,
        "value": value,
        "text": text_obj,
        **({"style": style} if style else {}),
    }