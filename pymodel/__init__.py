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

from .model import Model, RootObjectModel
__all__ = ['Model', 'RootObjectModel', ]

#Load all types
def _install():
    #logger.info('Installing field types')

    import inspect

    #import pymodel.fields
    from pymodel.fields import ExposedField
    field_mod = inspect.getmodule(ExposedField)

    glob = globals()

    #Load all exposed Field types
    #logger.debug('Loading field types')
    for attr_name in (name for name in dir(field_mod) if not
            name.startswith('_')):
        attr = getattr(field_mod, attr_name)
        if inspect.isclass(attr) and issubclass(attr, ExposedField) \
           and attr is not ExposedField:
            #logger.debug('Found field type %s' % attr_name)
            if attr_name in glob:
                raise RuntimeError('%s already defined' % attr_name)
            glob[attr_name] = attr
            __all__.append(attr_name)

    #Clean up module, so tab completion is nice and shiny
    #logger.debug('Cleaning up package globals')
    for name, value in glob.copy().iteritems():
        if name.startswith('__'):
            continue

        if inspect.isclass(value) and issubclass(value, ExposedField) \
           and value is not ExposedField:
            continue

        if value in (Model, RootObjectModel, ):
            continue

        glob.pop(name)

_install()

ROOTOBJECT_TYPES = dict()

def init(model_path, model_domain):
    '''Initialize the Pymodel library

    @param model_path: Folder path containing all root object model modules for domain
    @type model_path: string


    @param model_domain: Name of the domain where rootobjects belong to
    @type model_domain: string

    '''
    import pymodel.utils

    types = pymodel.utils.find_rootobject_types(model_path, model_domain)

    if not model_domain in ROOTOBJECT_TYPES.keys():
        ROOTOBJECT_TYPES[model_domain] = {}


    for type_ in types:
        name = type_.__name__
        if name in ROOTOBJECT_TYPES[model_domain]:
            raise RuntimeError('Duplicate root object type %s' % name)
        ROOTOBJECT_TYPES[model_domain][name] = type_

def init_domain(model_path):
    import os
    for domain in os.listdir(model_path):
        fullpath = os.path.join(model_path, domain)
        if not os.path.isdir(fullpath):
            continue
        init(fullpath, domain)

def load_models(model_path):
    '''Load all models defined in modules in a given folder

    @param model_path: Path to model module folder
    @type model_path: string

    @return: Iterable of all models
    @rtype: iterable
    '''
    import pymodel.utils
    return pymodel.utils.load_rootobject_types(model_path)



# Set up binding to PyMonkey logging
def _setup_pylabs_logging():
    '''Relay Pymodel log messages to PyMonkey logging if available

    Pymodel uses the standard Python *logging* module to perform logging. This
    function makes sure any messages logged to the logging module in the
    *pymodel* namespace is relayed to the PyMonkey logging subsystem using
    an appropriate loglevel.
    '''
    import logging
    logger = logging.getLogger('pymodel')
    
    try:
        from pylabs import q
    except ImportError:
        logger.info('No PyMonkey support on this system')
        return

    _logging_level_map = {
        logging.CRITICAL: 1,
        logging.ERROR: 2,
        logging.WARNING: 3,
        logging.WARN: 3,
        logging.INFO: 5,
        logging.DEBUG: 6,
        logging.NOTSET: 7,
    }

    class PyMonkeyLogger(logging.Handler):
        '''Basic logging handler which hooks PyMonkey logging to Python
        logging'''
        def emit(self, record):
            '''Emit one logrecord to the PyMonkey logging subsystem'''
            level = _logging_level_map.get(record.levelno, 7)

            q.logger.log('%s%s' % (
                             '[%s] ' % record.name if record.name else '',
                             record.getMessage(),
                         ),
                         level)

    pmlogger = PyMonkeyLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(pmlogger)
