from dataclasses import dataclass

@dataclass
class Chapter:
    title: str = ""
    content: str = ""
    url: str = ""
    is_has_capcha_block: bool = False
    is_get_failed: bool = False
