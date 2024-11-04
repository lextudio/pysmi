#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2019, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import re
import sys
from collections import OrderedDict
from time import strftime, strptime

from pysmi import config, debug, error
from pysmi.codegen.base import AbstractCodeGen
from pysmi.mibinfo import MibInfo

if sys.version_info[0] > 2:
    unicode = str
    long = int


class IntermediateCodeGen(AbstractCodeGen):
    """Turns MIB AST into an intermediate representation.

    This intermediate representation is based on built-in Python types
    and structures that could easily be used from within the template
    engines.
    """

    constImports = {
        "SNMPv2-SMI": (
            "iso",
            "NOTIFICATION-TYPE",  # bug in some MIBs (e.g. A3COM-HUAWEI-DHCPSNOOP-MIB)
            "MODULE-IDENTITY",
            "OBJECT-TYPE",
            "OBJECT-IDENTITY",
        ),
        "SNMPv2-TC": (
            "DisplayString",
            "PhysAddress",
            "TEXTUAL-CONVENTION",
        ),  # XXX
        "SNMPv2-CONF": (
            "MODULE-COMPLIANCE",
            "NOTIFICATION-GROUP",
        ),  # XXX
    }

    # never compile these, they either:
    # - define MACROs (implementation supplies them)
    # - or carry conflicting OIDs (so that all IMPORT's of them will be rewritten)
    # - or have manual fixes
    # - or import base ASN.1 types from implementation-specific MIBs
    fakeMibs = (
        "ASN1",
        "ASN1-ENUMERATION",
        "ASN1-REFINEMENT",
    ) + AbstractCodeGen.baseMibs

    baseTypes = ["Integer", "Integer32", "Bits", "ObjectIdentifier", "OctetString"]

    SMI_TYPES = {
        "NetworkAddress": "IpAddress",  # RFC1065-SMI, RFC1155-SMI -> SNMPv2-SMI
        "nullSpecific": "zeroDotZero",  # RFC1158-MIB -> SNMPv2-SMI
        "ipRoutingTable": "ipRouteTable",  # RFC1158-MIB -> RFC1213-MIB
        "snmpEnableAuthTraps": "snmpEnableAuthenTraps",  # RFC1158-MIB -> SNMPv2-MIB
    }

    def __init__(self):
        self._rows = set()
        self._seenSyms = set()
        self._importMap = {}
        self._out = {}  # k, v = name, generated code
        self._moduleIdentityOid = None
        self._moduleRevision = None
        self._enterpriseOid = None
        self._oids = set()
        self._complianceOids = []
        self.moduleName = ["DUMMY"]
        self.genRules = {"text": True}
        self.symbolTable = {}

    def prep_data(self, pdata):
        data = []
        for el in pdata:
            if not isinstance(el, tuple):
                data.append(el)
            elif len(el) == 1:
                data.append(el[0])
            else:
                data.append(self.handlersTable[el[0]](self, self.prep_data(el[1:])))
        return data

    def gen_imports(self, imports):
        # convertion to SNMPv2
        toDel = []
        for module in list(imports):
            if module in self.convertImportv2:
                for symbol in imports[module]:
                    if symbol in self.convertImportv2[module]:
                        toDel.append((module, symbol))

                        for newImport in self.convertImportv2[module][symbol]:
                            newModule, newSymbol = newImport

                            if newModule in imports:
                                imports[newModule].append(newSymbol)
                            else:
                                imports[newModule] = [newSymbol]

        # removing converted symbols
        for d in toDel:
            imports[d[0]].remove(d[1])

        # merging mib and constant imports
        for module in self.constImports:
            if module in imports:
                imports[module] += self.constImports[module]
            else:
                imports[module] = self.constImports[module]

        outDict = OrderedDict()
        outDict["class"] = "imports"
        for module in sorted(imports):
            symbols = []
            for symbol in sorted(set(imports[module])):
                symbols.append(symbol)

            if symbols:
                self._seenSyms.update([self.trans_opers(s) for s in symbols])
                self._importMap.update([(self.trans_opers(s), module) for s in symbols])
                if module not in outDict:
                    outDict[module] = []

                outDict[module].extend(symbols)

        return OrderedDict(imports=outDict), tuple(sorted(imports))

    def add_to_exports(self, symbol, moduleIdentity=0):
        self._seenSyms.add(symbol)

    # noinspection PyUnusedLocal
    def reg_sym(
        self,
        symbol,
        outDict,
        parentOid=None,
        moduleIdentity=False,
        moduleCompliance=False,
    ):
        if symbol in self._seenSyms and symbol not in self._importMap:
            raise error.PySmiSemanticError(f"Duplicate symbol found: {symbol}")

        self.add_to_exports(symbol, moduleIdentity)
        self._out[symbol] = outDict

        if "oid" in outDict:
            self._oids.add(outDict["oid"])

            if not self._enterpriseOid and outDict["oid"].startswith("1.3.6.1.4.1."):
                self._enterpriseOid = ".".join(outDict["oid"].split(".")[:7])

            if moduleIdentity:
                if self._moduleIdentityOid:
                    if config.STRICT_MODE:
                        raise error.PySmiSemanticError("Duplicate module identity")
                    else:
                        pass
                else:
                    self._moduleIdentityOid = outDict["oid"]

            if moduleCompliance:
                self._complianceOids.append(outDict["oid"])

    def gen_numeric_oid(self, oid):
        numericOid = ()

        for part in oid:
            if isinstance(part, tuple):
                parent, module = part
                if parent == "iso":
                    numericOid += (1,)
                    continue

                if module not in self.symbolTable:
                    # TODO: do getname for possible future borrowed mibs
                    raise error.PySmiSemanticError(
                        f'no module "{module}" in symbolTable'
                    )

                if parent not in self.symbolTable[module]:
                    raise error.PySmiSemanticError(
                        f'no symbol "{parent}" in module "{module}"'
                    )
                numericOid += self.gen_numeric_oid(
                    self.symbolTable[module][parent]["oid"]
                )

            else:
                numericOid += (part,)

        return numericOid

    def get_base_type(self, symName, module):
        if module not in self.symbolTable:
            raise error.PySmiSemanticError(f'no module "{module}" in symbolTable')

        if symName not in self.symbolTable[module]:
            raise error.PySmiSemanticError(
                f'no symbol "{symName}" in module "{module}"'
            )

        symType, symSubtype = self.symbolTable[module][symName].get(
            "syntax", (("", ""), "")
        )
        if not symType[0]:
            raise error.PySmiSemanticError(f'unknown type for symbol "{symName}"')

        if symType[0] in self.baseTypes:
            return symType, symSubtype

        else:
            baseSymType, baseSymSubtype = self.get_base_type(*symType)
            if isinstance(baseSymSubtype, list):
                if isinstance(symSubtype, list):
                    symSubtype += baseSymSubtype
                else:
                    symSubtype = baseSymSubtype

            return baseSymType, symSubtype

    def is_type_derived_from_tc(self, symName, module):
        """Is the given type derived from a Textual-Convention declaration?

        Given that deriving simple types from textual conventions is currently
        not supported altogether, this method tests only the immediate parent.

        Any problems are ignored: if the given type is not definitely derived
        from a textual convention, this method returns False.
        """
        if module not in self.symbolTable or symName not in self.symbolTable[module]:
            return False

        return self.symbolTable[module][symName]["isTC"]

    # Clause generation functions

    # noinspection PyUnusedLocal
    def gen_agent_capabilities(self, data):
        name, productRelease, status, description, reference, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "agentcapabilities"

        if productRelease:
            outDict["productrelease"] = productRelease

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_module_identity(self, data):
        name, lastUpdated, organization, contactInfo, description, revisions, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "moduleidentity"

        if revisions:
            outDict["revisions"] = revisions

            self._moduleRevision = revisions[0]["revision"]

        if self.genRules["text"]:
            if lastUpdated:
                outDict["lastupdated"] = lastUpdated
            if organization:
                outDict["organization"] = organization
            if contactInfo:
                outDict["contactinfo"] = contactInfo
            if description:
                outDict["description"] = description

        self.reg_sym(pysmiName, outDict, parentOid, moduleIdentity=True)

        return outDict

    # noinspection PyUnusedLocal
    def gen_module_compliance(self, data):
        name, status, description, reference, compliances, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "modulecompliance"

        if compliances:
            outDict["modulecompliance"] = compliances

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid, moduleCompliance=True)

        return outDict

    # noinspection PyUnusedLocal
    def gen_notification_group(self, data):
        name, objects, status, description, reference, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid
        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "notificationgroup"

        if objects:
            outDict["objects"] = [
                {
                    "module": self._importMap.get(
                        self.trans_opers(obj), self.moduleName[0]
                    ),
                    "object": obj,
                }
                for obj in objects
            ]

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_notification_type(self, data):
        name, objects, status, description, reference, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid
        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "notificationtype"

        if objects:
            outDict["objects"] = [
                {
                    "module": self._importMap.get(
                        self.trans_opers(obj), self.moduleName[0]
                    ),
                    "object": obj,
                }
                for obj in objects
            ]

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_object_group(self, data):
        name, objects, status, description, reference, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid
        outDict = OrderedDict({"name": name, "oid": oidStr, "class": "objectgroup"})

        if objects:
            outDict["objects"] = [
                {
                    "module": self._importMap.get(
                        self.trans_opers(obj), self.moduleName[0]
                    ),
                    "object": obj,
                }
                for obj in objects
            ]

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_object_identity(self, data):
        name, status, description, reference, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "objectidentity"

        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_object_type(self, data):
        (
            name,
            syntax,
            units,
            maxaccess,
            status,
            description,
            reference,
            augmention,
            index,
            defval,
            oid,
        ) = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid
        indexStr, fakeSyms, fakeSymDicts = index or ("", [], [])

        defval = self.gen_def_val(defval, objname=pysmiName)

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr

        if syntax[0]:
            nodetype = syntax[0] == "Bits" and "scalar" or syntax[0]  # Bits hack
            # If this object type is used as a column, but it also has a
            # "SEQUENCE OF" syntax, then it is really a table and not a column.
            #
            # Note that _symtable_cols contains original (non-Pythonized)
            # symbol names! Thus, check with 'name' rather than 'pysmiName'.
            isColumn = (
                name in self.symbolTable[self.moduleName[0]]["_symtable_cols"]
                and syntax[1]
            )
            nodetype = isColumn and "column" or nodetype
            outDict["nodetype"] = nodetype

        outDict["class"] = "objecttype"

        if syntax[1]:
            outDict["syntax"] = syntax[1]
        if defval:
            outDict["default"] = defval
        if units:
            outDict["units"] = units
        if maxaccess:
            outDict["maxaccess"] = maxaccess
        if indexStr:
            outDict["indices"] = indexStr
        if self.genRules["text"] and reference:
            outDict["reference"] = reference
        if augmention:
            augmention = self.trans_opers(augmention)
            outDict["augmention"] = OrderedDict()
            outDict["augmention"]["name"] = name
            outDict["augmention"]["module"] = self.moduleName[0]
            outDict["augmention"]["object"] = augmention
        if status:
            outDict["status"] = status

        if self.genRules["text"] and description:
            outDict["description"] = description

        self.reg_sym(pysmiName, outDict, parentOid)

        for fakeSym, fakeSymDict in zip(fakeSyms, fakeSymDicts):
            fakeSymDict["oid"] = f"{oidStr}.{fakeSymDict['oid']}"
            self.reg_sym(fakeSym, fakeSymDict, pysmiName)

        return outDict

    # noinspection PyUnusedLocal
    def gen_trap_type(self, data):
        name, enterprise, variables, description, reference, value = data

        pysmiName = self.trans_opers(name)

        enterpriseStr, parentOid = enterprise

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = enterpriseStr + ".0." + str(value)
        outDict["class"] = "notificationtype"

        if variables:
            outDict["objects"] = [
                {
                    "module": self._importMap.get(
                        self.trans_opers(obj), self.moduleName[0]
                    ),
                    "object": obj,
                }
                for obj in variables
            ]

        if self.genRules["text"] and description:
            outDict["description"] = description

        if self.genRules["text"] and reference:
            outDict["reference"] = reference

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # noinspection PyUnusedLocal
    def gen_type_declaration(self, data):
        name, declaration = data

        outDict = OrderedDict()
        outDict["name"] = name
        outDict["class"] = "type"

        if declaration:
            parentType, attrs = declaration
            if parentType:  # skipping SEQUENCE case
                pysmiName = self.trans_opers(name)
                outDict.update(attrs)
                self.reg_sym(pysmiName, outDict)

                # Establish if this type is derived from a Textual-Convention
                # declaration, as needed for pysnmp code generation.
                typeType = outDict["type"]["type"]
                if (
                    typeType in self.symbolTable[self.moduleName[0]]
                    or typeType in self._importMap
                ):
                    module = self._importMap.get(typeType, self.moduleName[0])
                    isDerivedFromTC = self.is_type_derived_from_tc(typeType, module)
                else:
                    isDerivedFromTC = False
                outDict["type"]["tcbase"] = isDerivedFromTC

        return outDict

    # noinspection PyUnusedLocal
    def gen_value_declaration(self, data):
        name, oid = data

        pysmiName = self.trans_opers(name)

        oidStr, parentOid = oid
        outDict = OrderedDict()
        outDict["name"] = name
        outDict["oid"] = oidStr
        outDict["class"] = "objectidentity"

        self.reg_sym(pysmiName, outDict, parentOid)

        return outDict

    # Subparts generation functions

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_bit_names(self, data):
        names = data[0]
        return names

    def gen_bits(self, data):
        bits = data[0]

        outDict = OrderedDict()
        outDict["type"] = "Bits"
        outDict["class"] = "type"
        outDict["bits"] = OrderedDict()

        for name, bit in sorted(bits, key=lambda x: x[1]):
            outDict["bits"][name] = bit

        return "scalar", outDict

    # noinspection PyUnusedLocal
    def gen_compliances(self, data):
        compliances = []

        for complianceModule in data[0]:
            name = complianceModule[0] or self.moduleName[0]
            compliances += [
                {"object": compl, "module": name} for compl in complianceModule[1]
            ]

        return compliances

    # noinspection PyUnusedLocal
    def gen_conceptual_table(self, data):
        row = data[0]

        if row[1] and row[1][-2:] == "()":
            row = row[1][:-2]
            self._rows.add(row)

        return "table", ""

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_contact_info(self, data):
        text = data[0]
        return self.textFilter("contact-info", text)

    # noinspection PyUnusedLocal
    def gen_display_hint(self, data):
        return data[0]

    # noinspection PyUnusedLocal
    def gen_def_val(self, data, objname=None):
        if not data:
            return {}

        if not objname:
            return data

        defval = data[0]
        defvalType = self.get_base_type(objname, self.moduleName[0])

        outDict = OrderedDict(basetype=defvalType[0][0])

        if isinstance(defval, (int, long)):  # number
            outDict.update(value=defval, format="decimal")

        elif self.is_hex(defval):  # hex
            # common bug in MIBs
            if defvalType[0][0] in ("Integer32", "Integer"):
                outDict.update(
                    value=str(int(len(defval) > 3 and defval[1:-2] or "0", 16)),
                    format="hex",
                )

            else:
                outDict.update(value=defval[1:-2], format="hex")

        elif self.is_binary(defval):  # binary
            binval = defval[1:-2]

            # common bug in MIBs
            if defvalType[0][0] in ("Integer32", "Integer"):
                outDict.update(value=str(int(binval or "0", 2)), format="bin")

            else:
                hexval = binval and hex(int(binval, 2))[2:] or ""
                outDict.update(value=hexval, format="hex")

        # quoted string
        elif defval and defval[0] == defval[-1] and defval[0] == '"':
            # common bug in MIBs
            if defval[1:-1] == "" and defvalType != "OctetString":
                # a warning should be here
                return {}  # we will set no default value

            outDict.update(value=defval[1:-1], format="string")

        # symbol (oid as defval) or name for enumeration member
        else:
            # oid
            if defvalType[0][0] == "ObjectIdentifier" and (
                self.trans_opers(defval) in self.symbolTable[self.moduleName[0]]
                or self.trans_opers(defval) in self._importMap
            ):
                pysmiDefval = self.trans_opers(defval)
                module = self._importMap.get(pysmiDefval, self.moduleName[0])

                try:
                    val = str(
                        self.gen_numeric_oid(
                            self.symbolTable[module][pysmiDefval]["oid"]
                        )
                    )

                    outDict.update(value=val, format="oid")

                except Exception:
                    # or no module if it will be borrowed later
                    raise error.PySmiSemanticError(
                        f'no symbol "{defval}" in module "{module}"'
                    )

            # enumeration
            elif defvalType[0][0] in ("Integer32", "Integer") and isinstance(
                defvalType[1], list
            ):
                # For enumerations, the ASN.1 DEFVAL statements contain names,
                # whereas the code generation template expects integer values
                # (represented as strings).
                nameToValueMap = dict(defvalType[1])

                # buggy MIB: DEFVAL { { ... } }
                if isinstance(defval, list):
                    defval = [dv for dv in defval if dv in nameToValueMap]
                    if defval:
                        outDict.update(
                            value=str(nameToValueMap[defval[0]]), format="enum"
                        )

                # good MIB: DEFVAL { ... }
                elif defval in nameToValueMap:
                    outDict.update(value=str(nameToValueMap[defval]), format="enum")

            elif defvalType[0][0] == "Bits":
                defvalBits = []

                bits = dict(defvalType[1])

                for bit in defval:
                    bitValue = bits.get(bit, None)
                    if bitValue is not None:
                        defvalBits.append((bit, bitValue))

                    else:
                        raise error.PySmiSemanticError(
                            f'no such bit as "{bit}" for symbol "{objname}"'
                        )

                outDict.update(value=self.gen_bits([defvalBits])[1], format="bits")

            else:
                raise error.PySmiSemanticError(
                    f'unknown type "{defvalType}" for defval "{defval}" of symbol "{objname}"'
                )

        return {"default": outDict}

    # noinspection PyMethodMayBeStatic
    def gen_description(self, data):
        return self.textFilter("description", data[0])

    # noinspection PyMethodMayBeStatic
    def gen_reference(self, data):
        return self.textFilter("reference", data[0])

    # noinspection PyMethodMayBeStatic
    def gen_status(self, data):
        return data[0]

    def gen_product_release(self, data):
        return data[0]

    def gen_enum_spec(self, data):
        items = data[0]
        return {"enumeration": dict(items)}

    # noinspection PyUnusedLocal
    def gen_table_index(self, data):
        def gen_fake_sym_dict(fakeSym, fakeOidSuffix, idxType):
            syntaxDict = OrderedDict()
            syntaxDict["type"] = self.SMI_TYPES.get(idxType, idxType)
            syntaxDict["class"] = "type"

            outDict = OrderedDict()
            outDict["name"] = fakeSym
            outDict["oid"] = str(fakeOidSuffix)  # suffix only; fixed up later
            outDict["class"] = "objecttype"
            outDict["nodetype"] = "column"
            outDict["syntax"] = syntaxDict
            outDict["maxaccess"] = "not-accessible"
            outDict["status"] = "mandatory"  # SMIv1
            return outDict

        indexes = data[0]
        idxStrlist, fakeSyms, fakeSymDicts = [], [], []

        # For fake indices, we generate fake column object types. Each of those
        # is given its own OID. Minimize the chance of collisions by starting
        # with the highest possible OID child number and going backward.
        fakeOidSuffix = 2**32 - 1

        for idx in indexes:
            isImplied = idx[0]
            idxName = idx[1]
            if idxName in self.smiv1IdxTypes:  # SMIv1 support
                idxType = idxName
                idxName = self.fakeIdxPrefix + str(self.fakeIdxNumber)
                fakeSymDict = gen_fake_sym_dict(idxName, fakeOidSuffix, idxType)
                fakeSyms.append(idxName)
                fakeSymDicts.append(fakeSymDict)
                self.fakeIdxNumber += 1
                fakeOidSuffix -= 1

            index = OrderedDict()
            index["module"] = self._importMap.get(
                self.trans_opers(idxName), self.moduleName[0]
            )
            index["object"] = idxName
            index["implied"] = isImplied
            idxStrlist.append(index)

        return idxStrlist, fakeSyms, fakeSymDicts

    def gen_integer_subtype(self, data):
        ranges = []
        for rng in data[0]:
            vmin, vmax = len(rng) == 1 and (rng[0], rng[0]) or rng
            vmin, vmax = self.str2int(vmin), self.str2int(vmax)
            ran = OrderedDict()
            ran["min"] = vmin
            ran["max"] = vmax
            ranges.append(ran)

        return {"range": ranges}

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_max_access(self, data):
        return data[0]

    def gen_octetstring_subtype(self, data):
        sizes = []
        for rng in data[0]:
            vmin, vmax = len(rng) == 1 and (rng[0], rng[0]) or rng
            vmin, vmax = self.str2int(vmin), self.str2int(vmax)

            size = OrderedDict()
            size["min"] = vmin
            size["max"] = vmax
            sizes.append(size)

        outDict = {"size": sizes}

        # If the union of ranges consists of a single size, then store that
        # information as well, so that pysnmp (which needs to know) does not
        # have to compute it itself. We take a slightly elaborate approach so
        # that strange ranges such as SIZE(4 | 4) also produce a fixed size.
        #
        # Note that as per RFC 2578 Sec. 9 point (3), derived types may only
        # ever reduce the ranges of their base types, so we never need to
        # override a base type's fixed length to be "non-fixed" again.
        minSize = min(size["min"] for size in sizes)
        maxSize = max(size["max"] for size in sizes)
        if minSize == maxSize:
            outDict["fixed"] = minSize

        return outDict

    # noinspection PyUnusedLocal
    def gen_oid(self, data):
        out = ()
        parent = ""
        for el in data[0]:
            if isinstance(el, (str, unicode)):
                parent = self.trans_opers(el)
                out += ((parent, self._importMap.get(parent, self.moduleName[0])),)

            elif isinstance(el, (int, long)):
                out += (el,)

            elif isinstance(el, tuple):
                out += (el[1],)  # XXX Do we need to create a new object el[0]?

            else:
                raise error.PySmiSemanticError(f"unknown datatype for OID: {el}")

        return ".".join([str(x) for x in self.gen_numeric_oid(out)]), parent

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_objects(self, data):
        return data[0]

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_time(self, data):
        times = []
        for timeStr in data:
            if len(timeStr) == 11:
                timeStr = "19" + timeStr

            elif config.STRICT_MODE and len(timeStr) != 13:
                raise error.PySmiSemanticError(f"Invalid date {timeStr}")
            try:
                times.append(
                    strftime("%Y-%m-%d %H:%M", strptime(timeStr, "%Y%m%d%H%MZ"))
                )

            except ValueError:
                if config.STRICT_MODE:
                    raise error.PySmiSemanticError(f"Invalid date {timeStr}")

                timeStr = "197001010000Z"  # dummy date for dates with typos
                times.append(
                    strftime("%Y-%m-%d %H:%M", strptime(timeStr, "%Y%m%d%H%MZ"))
                )

        return times

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_last_updated(self, data):
        return data[0]

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_organization(self, data):
        return self.textFilter("organization", data[0])

    # noinspection PyUnusedLocal
    def gen_revisions(self, data):
        revisions = []
        for x in data[0]:
            revision = OrderedDict()
            revision["revision"] = self.gen_time([x[0]])[0]
            revision["description"] = self.textFilter("description", x[1][1])
            revisions.append(revision)
        return revisions

    def gen_row(self, data):
        row = data[0]
        row = self.trans_opers(row)

        return (
            row in self.symbolTable[self.moduleName[0]]["_symtable_rows"]
            and ("row", "")
            or self.gen_simple_syntax(data)
        )

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_sequence(self, data):
        return "", ""

    def gen_simple_syntax(self, data):
        objType = data[0]
        objType = self.SMI_TYPES.get(objType, objType)
        objType = self.trans_opers(objType)

        subtype = len(data) == 2 and data[1] or {}

        outDict = OrderedDict()
        outDict["type"] = objType
        outDict["class"] = "type"

        if subtype:
            outDict["constraints"] = subtype

        return "scalar", outDict

    # noinspection PyUnusedLocal
    def gen_type_declaration_rhs(self, data):
        if len(data) == 1:
            parentType, attrs = data[0]

            outDict = OrderedDict()
            if not attrs:
                return outDict
            # just syntax
            outDict["type"] = attrs

        else:
            # Textual convention
            display, status, description, reference, syntax = data
            parentType, attrs = syntax

            outDict = OrderedDict()
            outDict["type"] = attrs
            outDict["class"] = "textualconvention"
            if display:
                outDict["displayhint"] = display
            if status:
                outDict["status"] = status
            if self.genRules["text"] and description:
                outDict["description"] = description
            if self.genRules["text"] and reference:
                outDict["reference"] = reference

        return parentType, outDict

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def gen_units(self, data):
        text = data[0]
        return self.textFilter("units", text)

    handlersTable = {
        "agentCapabilitiesClause": gen_agent_capabilities,
        "moduleIdentityClause": gen_module_identity,
        "moduleComplianceClause": gen_module_compliance,
        "notificationGroupClause": gen_notification_group,
        "notificationTypeClause": gen_notification_type,
        "objectGroupClause": gen_object_group,
        "objectIdentityClause": gen_object_identity,
        "objectTypeClause": gen_object_type,
        "trapTypeClause": gen_trap_type,
        "typeDeclaration": gen_type_declaration,
        "valueDeclaration": gen_value_declaration,
        "PRODUCT-RELEASE": gen_product_release,
        "ApplicationSyntax": gen_simple_syntax,
        "BitNames": gen_bit_names,
        "BITS": gen_bits,
        "ComplianceModules": gen_compliances,
        "conceptualTable": gen_conceptual_table,
        "CONTACT-INFO": gen_contact_info,
        "DISPLAY-HINT": gen_display_hint,
        "DEFVAL": gen_def_val,
        "DESCRIPTION": gen_description,
        "REFERENCE": gen_reference,
        "Status": gen_status,
        "enumSpec": gen_enum_spec,
        "INDEX": gen_table_index,
        "integerSubType": gen_integer_subtype,
        "MaxAccessPart": gen_max_access,
        "Notifications": gen_objects,
        "octetStringSubType": gen_octetstring_subtype,
        "objectIdentifier": gen_oid,
        "Objects": gen_objects,
        "LAST-UPDATED": gen_last_updated,
        "ORGANIZATION": gen_organization,
        "Revisions": gen_revisions,
        "row": gen_row,
        "SEQUENCE": gen_sequence,
        "SimpleSyntax": gen_simple_syntax,
        "typeDeclarationRHS": gen_type_declaration_rhs,
        "UNITS": gen_units,
        "VarTypes": gen_objects,
        # 'a': lambda x: genXXX(x, 'CONSTRAINT')
    }

    # TODO: make intermediate format less tied to JSON
    # One thing is to produce OIDs in a tuple form
    # The other thing is index data - may be we should
    # have it prepared at the intermediate stage...?

    def gen_code(self, ast, symbolTable, **kwargs):
        self.genRules["text"] = kwargs.get("genTexts", False)
        self.textFilter = kwargs.get("textFilter") or (
            lambda symbol, text: re.sub(r"\s+", " ", text)
        )
        self.symbolTable = symbolTable
        self._rows.clear()
        self._seenSyms.clear()
        self._importMap.clear()
        self._out.clear()
        self._moduleIdentityOid = None
        self._enterpriseOid = None
        self._oids = set()
        self._complianceOids = []
        self.moduleName[0], moduleOid, imports, declarations = ast

        outDict, importedModules = self.gen_imports(imports)

        for declr in declarations or []:
            if declr:
                self.handlersTable[declr[0]](self, self.prep_data(declr[1:]))

        for sym in self.symbolTable[self.moduleName[0]]["_symtable_order"]:
            if sym not in self._out:
                raise error.PySmiCodegenError(f"No generated code for symbol {sym}")

            outDict[sym] = self._out[sym]

        outDict["meta"] = OrderedDict()
        outDict["meta"]["module"] = self.moduleName[0]

        if "comments" in kwargs:
            outDict["meta"]["comments"] = kwargs["comments"]

        debug.logger & debug.FLAG_CODEGEN and debug.logger(
            f"canonical MIB name {self.moduleName[0]} ({moduleOid}), imported MIB(s) {','.join(importedModules) or '<none>'}"
        )

        return (
            MibInfo(
                oid=moduleOid,
                identity=self._moduleIdentityOid,
                name=self.moduleName[0],
                revision=self._moduleRevision,
                oids=self._oids,
                enterprise=self._enterpriseOid,
                compliance=self._complianceOids,
                imported=tuple(x for x in importedModules if x not in self.fakeMibs),
            ),
            outDict,
        )
