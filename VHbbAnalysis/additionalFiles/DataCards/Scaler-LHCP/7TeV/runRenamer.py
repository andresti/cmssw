#! /usr/bin/env python

import sys
import os
import commands
import string
mass=["110","110_5","111","111_5","112","112_5","113","113_5","114","114_5","115","115_5","116","116_5","117","117_5","118","118_5","119","119_5","120","120_5","121","121_5","122","122_5","123","123_5","124","124_5","125","125_5","126","126_5","127","127_5","128","128_5","129","129_5","130","130_5","131","131_5","132","132_5","133","133_5","134","134_5","135"]

for item in mass:
    os.system("cp renamer.py %s" % (item))
    os.system("echo 'cd %s' > bs" % (item))
    os.system("echo 'python renamer.py' >> bs")
    os.system("echo 'rm renamer.py' >> bs")
    os.system("chmod +x bs")
    os.system("./bs")
