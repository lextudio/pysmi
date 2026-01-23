"""Per-MIB implicit imports workarounds.

Populate this mapping only when necessary. Keep entries minimal and
document why each entry exists (vendor, MIB, date).
"""

from typing import Dict, List, Tuple

IMPLICIT_IMPORTS: Dict[str, List[Tuple[str, str]]] = {
    # Example vendor MIB workarounds (keep minimal and documented):
    # JUNIPER-SMI: latest revision missed importing Opaque for Integer64 TC
    # 'JUNIPER-SMI': [('SNMPv2-SMI', 'Opaque')],
    # A3COM/Huawei MIBs that omitted Counter64 / NOTIFICATION-TYPE imports
    # 'A3COM-HUAWEI-LswINF-MIB': [('SNMPv2-SMI', 'Counter64')],
    # 'A3COM-HUAWEI-DHCPSNOOP-MIB': [('SNMPv2-SMI', 'NOTIFICATION-TYPE')],
    # DSA-MIB (example IETF MIB) omitted Counter32 import
    # 'DSA-MIB': [('SNMPv2-SMI', 'Counter32')],
    # 'DSA-MIB': [('SNMPv2-SMI', 'Gauge32')],
}


def apply_implicit_imports(imports_map, module_name: str):
    """Mutate ``imports_map`` by adding any implicit imports for ``module_name``.

    The function is defensive about the incoming mapping shape: it will
    try to coerce the mapping to a dict and ensure each module's value is a
    mutable list before appending.
    """
    if not isinstance(imports_map, dict):
        try:
            imports_map = dict(imports_map)
        except Exception:
            return imports_map

    # make sure value containers are lists
    for m in list(imports_map):
        if not isinstance(imports_map[m], list):
            try:
                imports_map[m] = list(imports_map[m])
            except Exception:
                imports_map[m] = [imports_map[m]]

    exceptions = IMPLICIT_IMPORTS.get(module_name)
    if not exceptions:
        return imports_map

    for new_module, new_symbol in exceptions:
        if new_module in imports_map:
            imports_map[new_module].append(new_symbol)
        else:
            imports_map[new_module] = [new_symbol]

    return imports_map


def add_import(imports_map, module: str, symbol: str):
    """Add ``symbol`` to ``imports_map[module]`` defensively.

    Ensures ``imports_map`` is a dict and that the target module's
    value is a mutable list before appending.
    Returns the mutated mapping for convenience.
    """
    if not isinstance(imports_map, dict):
        try:
            imports_map = dict(imports_map)
        except Exception:
            # can't coerce, nothing to do
            return imports_map

    if module in imports_map:
        if isinstance(imports_map[module], list):
            imports_map[module].append(symbol)
        else:
            try:
                imports_map[module] = list(imports_map[module]) + [symbol]
            except Exception:
                imports_map[module] = [symbol]
    else:
        imports_map[module] = [symbol]

    return imports_map


def apply_const_imports(imports_map):
    """Ensure all `CONST_IMPORTS` entries are present in `imports_map`.

    This mutates `imports_map` defensively and returns it for convenience.
    """
    if not isinstance(imports_map, dict):
        try:
            imports_map = dict(imports_map)
        except Exception:
            return imports_map

    # make sure value containers are lists so add_import can append
    for m in list(imports_map):
        if not isinstance(imports_map[m], list):
            try:
                imports_map[m] = list(imports_map[m])
            except Exception:
                imports_map[m] = [imports_map[m]]

    for module, syms in CONST_IMPORTS.items():
        for sym in syms:
            add_import(imports_map, module, sym)

    return imports_map


# Const imports used by code generators. Keep them centralized to avoid
# duplication between `SymtableCodeGen` and `IntermediateCodeGen`.
CONST_IMPORTS = {
    "SNMPv2-SMI": (
        "iso",
        "Bits",  # kept for legacy MIBs that reference Bits without importing
        "Integer32",  # common base integer type (SMIv1/SMIv2 compatibility)
        "TimeTicks",  # some IETF/vendor MIBs import TimeTicks implicitly
        "MODULE-IDENTITY",
        "OBJECT-TYPE",
        "OBJECT-IDENTITY",
        "Unsigned32",
        "IpAddress",  # alias for NetworkAddress/IPADDRESS differences
        "MibIdentifier",
    ),
    "SNMPv2-TC": (
        "DisplayString",  # textual conventions commonly used without explicit import
        "PhysAddress",
        "TEXTUAL-CONVENTION",
    ),
    "SNMPv2-CONF": (
        "MODULE-COMPLIANCE",  # convenience imports for compliance generation
        "NOTIFICATION-GROUP",
    ),
}
