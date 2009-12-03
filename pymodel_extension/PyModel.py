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
    
import os    

from pymonkey import q

from osis import init
import osis.utils
from osis.model.serializers import ThriftSerializer
from osis.model.serializers import YamlSerializer
from XMLSerializer import XMLSerializer
from ThriftBase64Serializer import ThriftBase64Serializer
from osis import ROOTOBJECT_TYPES

from osis.client import OsisConnection
from osis.client.connection import *


class Domain(object):
    pass

class DummyConnection(object):
    pass

class PyModelOsisClient(object):
    
    def __init__(self, transport, serializer):
        '''Initialize a new OSIS root object client

        @param transport: OSIS client transport
        @type transport: object
        @param serializer: Object serializer implementation
        @type serializer: object
        '''
        self._transport = transport
        self._serializer = serializer    
    
    def getEmptyModelObject(self, *args, **kwargs):
        return self._ROOTOBJECTTYPE(*args, **kwargs)

    #serializing methods
    def object2XML(self, data):
        return self._serialize(XMLSerializer, data)
    
    def object2YAML(self, data):
        return self._serialize(YamlSerializer, data)
     
    def object2ThriftByteStr(self, data):
        return self._serialize(ThriftSerializer, data)
    
    def object2ThriftBase64Str(self, data):        
        return self._serialize(ThriftBase64Serializer, data)
    
    #deserializing methods
    def XML2object(self, data):
        return self._deserializer(XMLSerializer, data)
    
    def YAML2object(self, data):
        return self._deserializer(YamlSerializer, data)
    
    def thriftByteStr2object(self, data):
        return self._deserializer(ThriftSerializer, data)
    
    def thriftBase64Str2object(self, data):
        return self._deserializer(ThriftBase64Serializer, data)
    
    def _serialize(self, serializer, data):
        return data.serialize(serializer)
    
    def _deserializer(self, serializer, data):
        return self._ROOTOBJECTTYPE.deserialize(serializer, data)
    


class PyModel():

    __shared_state = {}
    
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not hasattr(self, 'initialized'):
            self.__initialize()
            setattr(self, 'initialized', True)
            
    def importDomain(self, domainname, specpath):
        init(specpath, OsisConnection, PyModelOsisClient)
        
        domain = Domain()            
        from osis import ROOTOBJECT_TYPES as types
        for type in types.itervalues():
            name = getattr(type, 'OSIS_TYPE_NAME', type.__name__.lower())                
            setattr(domain, name, getattr(OsisConnection(None,None), name))
        setattr(self, domainname, domain)
                    
    def __initialize(self):        
        parentPath = q.system.fs.joinPaths(q.dirs.baseDir, 'lib', 'pymonkey', 'models')
        for subPath in os.listdir(parentPath):
            domainname = subPath
            specpath = q.system.fs.joinPaths(parentPath, subPath)
            self.importDomain(domainname, specpath)
            