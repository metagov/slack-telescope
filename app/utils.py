from .config import TEXT_PREVIEW_CHAR_LIMIT


def truncate_text(string: str):
    if len(string) > TEXT_PREVIEW_CHAR_LIMIT:
        return string[:TEXT_PREVIEW_CHAR_LIMIT] + "..."
    else:
        return string

def indent_text(string: str):
    return "\n".join(["> " + line for line in string.splitlines()])