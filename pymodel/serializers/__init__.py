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

import logging
logger = logging.getLogger('pymodel.serializers')

# Dictionary containing all known serializers
# Keys starting with an underscore are considered to be testing serializers
SERIALIZERS = dict()

__all__ = ['SERIALIZERS', ]

try:
    from ._thrift import ThriftSerializer
    logger.info('Loaded Thrift serializer')
    __all__.append('ThriftSerializer')
    SERIALIZERS[ThriftSerializer.NAME] = ThriftSerializer
except ImportError, e:
    logger.info('Unable to load Thrift serializer: %s' % e)
else:
    # Thrift is supported, let's try to load the test implementations
    # Thrift is a special case since we got 2 serializers to test:
    #
    # * An optimized one (using fastbinary.so)
    # * A native Python one
    try:
        from ._thrift import OptimizedSerializer
        logger.debug('Loaded optimized Thrift serializer')
        SERIALIZERS[OptimizedSerializer.NAME] = OptimizedSerializer
    except ImportError, e:
        logger.debug('Unable to load optimized Thrift serializer: %s' % e)

    try:
        from ._thrift import NativeSerializer
        logger.debug('Loaded native Thrift serializer')
        SERIALIZERS[NativeSerializer.NAME] = NativeSerializer
    except ImportError, e:
        logger.debug('Unable to load native Thrift serializer: %s' % e)


try:
    from .pymodelyaml import YamlSerializer
    logger.info('Loaded YAML serializer')
    __all__.append('YamlSerializer')
    SERIALIZERS[YamlSerializer.NAME] = YamlSerializer
    SERIALIZERS['_%s' % YamlSerializer.NAME] = YamlSerializer
except ImportError, e:
    logger.info('Unable to load YAML serializer: %s' % e)

try:
    from .pymodeljson import JsonSerializer
    logger.info('Loaded JSON serializer')
    __all__.append('JsonSerializer')
    SERIALIZERS[JsonSerializer.NAME] = JsonSerializer
    SERIALIZERS['_%s' % JsonSerializer.NAME] = JsonSerializer
except ImportError, e:
    logger.info('Unable to load JSON serializer: %s' % e)

try:
    from .pymodeldict import DictSerializer
    logger.info('Loaded Dict serializer')
    __all__.append('DictSerializer')
    SERIALIZERS[DictSerializer.NAME] = DictSerializer
except ImportError, e:
    logger.info('Unable to load Dict serializer: %s' % e)


try:
    from .XMLSerializer import XMLSerializer
    logger.info('Loaded XML serializer')
    __all__.append('XMLSerializer')
    SERIALIZERS[XMLSerializer.NAME] = XMLSerializer
    SERIALIZERS['_%s' % XMLSerializer.NAME] = XMLSerializer
except ImportError, e:
    logger.info('Unable to load XML serializer: %s' % e)

    
try:
    from .ThriftBase64Serializer import ThriftBase64Serializer
    logger.info('Loaded thriftbase64 serializer')
    __all__.append('ThriftBase64Serializer')
    SERIALIZERS[ThriftBase64Serializer.NAME] = ThriftBase64Serializer
    SERIALIZERS['_%s' % ThriftBase64Serializer.NAME] = ThriftBase64Serializer
except ImportError, e:
    logger.info('Unable to load thriftbase64 serializer: %s' % e)
