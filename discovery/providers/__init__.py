"""Provider registry for report discovery."""

from .bis import BISProvider
from .mckinsey import McKinseyProvider
from .deloitte import DeloitteProvider
from .bcg import BCGProvider
from .pwc import PwCProvider

ALL_PROVIDERS = [
    BISProvider(),
    McKinseyProvider(),
    DeloitteProvider(),
    BCGProvider(),
    PwCProvider(),
]
