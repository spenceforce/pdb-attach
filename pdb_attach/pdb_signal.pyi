from pdb_attach.detach import PdbDetach
from pdb_attach.pdb_socket import PdbClient, PdbServer
from types import FrameType
from typing import Any, Callable, Union

class PdbSignal(PdbServer, PdbDetach):
    def __init__(
        self,
        old_handler: Callable[[int, FrameType], None],
        port: Union[int, str],
        *args: Any,
        **kwargs: Any
    ) -> None: ...
    def __call__(self, signum: int, frame: FrameType) -> None: ...
    @classmethod
    def listen(cls, port: Union[int, str], *args: Any, **kwargs: Any) -> None: ...
    @classmethod
    def unlisten(cls) -> None: ...

class PdbSignaler(PdbClient):
    def __init__(self, pid: int, port: Union[int, str]) -> None: ...
    def connect(self) -> None: ...
