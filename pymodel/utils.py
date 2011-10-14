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

'''Several utility functions'''

import sys
import os
import os.path
import imp
import new
import logging
import inspect
import hashlib

from pymodel.model import RootObjectModel #pylint: disable-msg=E0611

logger = logging.getLogger('pymodel.utils') #pylint: disable-msg=C0103

def _get_module_name(path):
    return 'pymodel._loader.%s' % hashlib.sha1(path).hexdigest()

def load_rootobject_types(path, package=None):
    '''Find and load all root object types defined in modules in a given path

    @param path: Folder containing the model modules
    @type path: string

    @return: Iterable of all root object types
    @rtype: iterable
    '''
    logger.info('Loading RootObjectModel definitions in %s', path)
    path = os.path.realpath(path)

    if not package:
        imp.acquire_lock()
        try:
            pymodel_module_name = _get_module_name(path)
            if pymodel_module_name not in sys.modules:
                sys.modules[pymodel_module_name] = new.module(pymodel_module_name)
        finally:
            imp.release_lock()

    else:
        pymodel_module_name = package

    def find_modules():
        '''Find all module files in a given path

        @return: Generator yielding all module paths
        @rtype: generator
        '''
        potential_modules = os.listdir(path)

        for filename in potential_modules:
            filepath = os.path.join(path, filename)
            if filepath.endswith('.py') and os.path.isfile(filepath):
                yield filename[:-3], filepath

    def load_modules():
        '''Load a module from a given path

        @return: Generator yielding all modules
        @rtype: generator
        '''
        for module_name, module_path in find_modules():
            logger.debug('Loading %s' % module_path)

            modname = '%s.%s' % (pymodel_module_name, module_name)
            if modname in sys.modules:
                logger.debug('%s already loaded', modname)
                yield sys.modules[modname]
            else:
                logger.debug('Loading %s from %s', modname, module_path)
                yield imp.load_source(modname, module_path)

    syspath = sys.path[:]
    imp.acquire_lock()
    try:
        sys.path.append(path)
        for module in load_modules():
            for attrname in dir(module):
                attr = getattr(module, attrname)
                if inspect.isclass(attr) and \
                   issubclass(attr, RootObjectModel) and \
                   attr.__module__ == module.__name__: # Get around imports
                    logger.info('Found RootObjectModel \'%s\'' % attr.__name__)
                    yield attr
    finally:
        imp.release_lock()
        sys.path = syspath

def find_rootobject_types(path, domain):
    '''Find all root object types defined in any module in a given path

    This method will list all Python files in a given file, import them, and
    check whether a subclass of L{RootObjectModel} is defined in them. It will
    yield any such type it finds.

    @param path: Folder to inspect
    @type path: string

    @return: Generator yielding all L{RootObjectModel} subtypes found
    @rtype: generator
    '''
    logger.info('Looking up RootObjectModel definitions in %s' % path)

    pymodel_module_name = 'pymodel.%s._rootobjects' % domain

    if pymodel_module_name not in sys.modules:
        logger.debug('Creating fake %s module' % pymodel_module_name)

        mod = new.module(pymodel_module_name)
        sys.modules[pymodel_module_name] = mod

    return load_rootobject_types(path, pymodel_module_name)


def compare_content(a, b):
    '''Compare the content of 2 model instances

    This function compares the value of 2 model instances and returns their
    equality.

    @param a: First instance in comparison
    @type a: pymodel.model.Model
    @param b: Second instance in comparison
    @type b: pymodel.model.Model

    @returns: Equality of a and b
    @rtype: bool
    '''
    if type(a) is not type(b):
        return NotImplemented

    from pymodel.model import DEFAULT_FIELDS

    for attr in a.PYMODEL_MODEL_INFO.attributes:
        attr = attr.name

        # Don't compare default fields (guid, version, creationdate)
        if attr in (field.name for field in DEFAULT_FIELDS):
            continue

        if not getattr(a, attr) == getattr(b, attr):
            return False

    return True
