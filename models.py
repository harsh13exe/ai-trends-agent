from dataclasses import dataclass, field


@dataclass
class Candidate:
    name: str
    url: str
    source: str            # hackernews | github | huggingface
    signal: float = 0.0    # popularity / velocity number from the source
    description: str = ""
    discussion: str = ""   # e.g. HN thread link
    meta: dict = field(default_factory=dict)   # facts straight from APIs
    sources: list = field(default_factory=list)  # every source that mentioned it
    score: float = 0.0
    key: str = ""
