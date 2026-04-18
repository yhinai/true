from .identity import build_identity_contracts
from .non_contradiction import build_non_contradiction_contracts
from .referential_integrity import build_referential_integrity_contracts
from .totality import build_totality_contracts

__all__ = [
    "build_identity_contracts",
    "build_non_contradiction_contracts",
    "build_referential_integrity_contracts",
    "build_totality_contracts",
]
