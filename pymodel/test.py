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

'''Some utility methods for pymodel testing'''

import re
import sys
import inspect
import unittest

ROOTOBJECT_MODULE_REGEX = re.compile("^pymodel\..+\._rootobjects")

def init(domain, path):
    '''Re-initialize pymodel inside a running Python environment

    This function removes all previously loaded modules from sys.modules, clears
    pymodel.ROOTOBJECT_TYPES. It then re-initializes pymodel using the given
    path.

    @param path: Path to pymodel definition modules
    @type path: string
    '''
    import pymodel

    pymodel.ROOTOBJECT_TYPES.clear()
    for modulename in sys.modules.keys():
        if ROOTOBJECT_MODULE_REGEX.match(modulename):
            sys.modules.pop(modulename)

    pymodel.init(path, domain)


class PymodelTestCase(object):
    '''Base for all generated pymodel test cases

    @see: L{_generate_testcase}
    '''
    #pylint: disable-msg=R0903
    serializer = None


def _generate_testcase(base, serializer):
    '''Generate a pymodel TestCase from a given TestCase and a serializer to
    use'''
    name = '%s_%s' % (base.__name__, serializer.NAME.lstrip('_').capitalize())
    doc = 'This test is executed using the %s serializer' % \
            serializer.NAME.capitalize()
    if base.__doc__:
        doc = '%s\n\n%s' % (base.__doc__.rstrip(), doc)

    attrs = {
        '__doc__': doc,
        '__name__': name,
        '__module__': base.__module__,

        'serializer': serializer,
    }

    bases = (base, PymodelTestCase, )

    return type(name, bases, attrs)


def setup(globals_):
    '''Set up a test module

    Usage::

        from pymodel.test import setup
        setup(globals())

    @param globals_: Globals of the module containing tests
    @type globals_: dict
    '''
    from pymodel.serializers import SERIALIZERS

    # For every element defined in the given module
    for key, value in globals_.copy().iteritems():
        # If it's a subclass of unittest.TestCase and public
        if inspect.isclass(value) and issubclass(value, unittest.TestCase) \
           and not key.startswith('_'):
            # Remove the original from the global dict
            del globals_[key]
            # And generate a test case for every serializer we support
            for key, serializer in SERIALIZERS.iteritems():
                if not key.startswith('_'):
                    # All test serializers start with _, ignore others
                    continue

                test = _generate_testcase(value, serializer)
                assert test.__name__ not in globals_, 'Duplicate class name'
                globals_[test.__name__] = test
