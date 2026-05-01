from typing import List, Optional, TypedDict


class AgentState(TypedDict):
    query: str
    route: Optional[str]
    rag_context: Optional[str]
    serp_context: Optional[str]
    context: Optional[str]
    no_context: bool
    answer: Optional[str]
    sources: List[str]
