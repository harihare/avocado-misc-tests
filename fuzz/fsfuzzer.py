#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
#
# Copyright: 2016 IBM
# Author: Praveen K Pandey <praveen@linux.vnet.ibm.com>
#
# Based on code by Martin Bligh <mbligh@google.com>
#   copyright: 2006 Google
#   https://github.com/autotest/autotest-client-tests/tree/master/fsfuzzer

import os
import re

from avocado import Test
from avocado import main
from avocado.utils import archive, build, distro, process
from avocado.utils.software_manager import SoftwareManager


class Fsfuzzer(Test):

    """
    fsfuzzer is a file system fuzzer tool. This test simply runs fsfuzzer
    Fuzzing is slang for fault injection via random inputs. The goal is to
    find bugs in software without reading code or designing detailed test
    cases.
       fsfuzz will inject random errors into the files systems
       mounted. Evidently it has found many errors in many systems.
    """

    def setUp(self):
        '''
        Build fsfuzzer
        Source:
        https://github.com/stevegrubb/fsfuzzer.git
        '''
        detected_distro = distro.detect()

        smm = SoftwareManager()

        if not smm.check_installed("gcc") and not smm.install("gcc"):
            self.error("Gcc is needed for the test to be run")

        locations = ["https://github.com/stevegrubb/fsfuzzer/archive/"
                     "master.zip"]
        tarball = self.fetch_asset("fsfuzzer.zip", locations=locations)
        archive.extract(tarball, self.srcdir)
        os.chdir(os.path.join(self.srcdir, "fsfuzzer-master"))

        if detected_distro.name == "Ubuntu":
            # Patch for ubuntu
            fuzz_fix_patch = 'patch -p1 < %s' % (
                os.path.join(self.datadir, 'fsfuzz_fix.patch'))
            if process.system(fuzz_fix_patch, shell=True, ignore_status=True):
                self.log.warn("Unable to apply sh->bash patch!")

        process.run('./autogen.sh', shell=True)
        process.run('./configure', shell=True)

        build.make('.')

        self._args = self.params.get('fstype', default='')
        self._fsfuzz = os.path.abspath(os.path.join('.', "fsfuzz"))
        fs_sup = process.system_output('%s %s' % (self._fsfuzz, ' --help'))
        match = re.search(r'%s' % self._args, fs_sup, re.M | re.I)
        if not match:
            self.skip('File system ' + self._args +
                      ' is unsupported in ' + detected_distro.name)

    def test(self):

        '''
        Runs the fsfuzz test suite. By default uses all supported fstypes,
        but you can specify only one by `fstype` param.
        '''
        process.system("%s %s" % (self._fsfuzz, self._args), sudo=True)

if __name__ == "__main__":
    main()