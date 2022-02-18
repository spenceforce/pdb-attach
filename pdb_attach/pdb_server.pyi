import pdb
from types import FrameType
from typing import Any, Optional, Union

class PdbServer(pdb.Pdb):
    def __init__(self, port: Union[int, str], *args: Any, **kwargs: Any) -> None: ...
    def set_trace(self, frame: Optional[FrameType] = ...) -> None: ...
    def close(self) -> None: ...
