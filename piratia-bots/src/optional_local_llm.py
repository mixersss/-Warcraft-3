"""Future local-only intent suggester interface; disabled, never called by I/O loop."""
from typing import Protocol,Optional
class OptionalLocalLLM(Protocol):
    def suggest_intent(self,channel:str,turns:tuple,allowed_intents:tuple)->Optional[str]:...
class DisabledLocalLLM:
    enabled=False
    def suggest_intent(self,*args,**kwargs):return None
