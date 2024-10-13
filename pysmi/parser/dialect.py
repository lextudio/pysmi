#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#

#
# Preconfigured sets of parser options.
# Individual options could be used in certain combinations.
#
smi_v2 = {}  # TODO: move strict mode here.

smi_v1 = smi_v2.copy()
smi_v1.update(supportSmiV1Keywords=True, supportIndex=True)

smi_v1_relaxed = smi_v1.copy()
smi_v1_relaxed.update(
    commaAtTheEndOfImport=True,
    commaAtTheEndOfSequence=True,
    mixOfCommasAndSpaces=True,
    uppercaseIdentifier=True,
    lowcaseIdentifier=True,
    curlyBracesAroundEnterpriseInTrap=True,
    noCells=True,
)
