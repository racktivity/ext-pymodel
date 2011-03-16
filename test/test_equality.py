# <License type="Aserver BSD" version="2.0">
#
# Copyright (c) 2005-2009, Aserver NV.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name Aserver nor the names of other contributors
#   may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ASERVER "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL ASERVER BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

import unittest
import uuid

import pymodel as model

class TestEquality(unittest.TestCase):
    def _test_simple(self, base):
        class Simple(base):
            i = model.Integer()
            s = model.String()
            b = model.Boolean()

        i1 = Simple(i=123, s='test123', b=True)
        i2 = Simple(i=123, s='test123', b=True)

        self.assertNotEqual(i1, i2)

        i3 = Simple(i=123, s='test123', b=False)
        self.assertNotEqual(i1, i3)
        self.assertNotEqual(i2, i3)

    def test_simple_rootobjectmodel(self):
        self._test_simple(model.RootObjectModel)

    def test_simple_model(self):
        self._test_simple(model.Model)

    def test_separate_types(self):
        class C1(model.Model):
            pass

        class C2(model.Model):
            pass

        self.assertNotEqual(C1(), C2())

    def test_equal(self):
        class Simple(model.Model):
            pass

        guid = lambda: str(uuid.uuid4())

        i1 = Simple()
        self.assertEqual(i1, i1)

        i2 = Simple()
        self.assertNotEqual(i1, i2)

        i1.guid = guid()
        self.assertNotEqual(i1, i2)

        i2.guid = i1.guid
        self.assertNotEqual(i1, i2)

        i1.version = guid()
        self.assertNotEqual(i1, i2)

        i2.version = i1.version
        self.assertEqual(i1, i2)
