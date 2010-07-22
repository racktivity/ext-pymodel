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

    
import os, sys

from pymonkey import q
from pymodel import init

import pymodel.utils

from pymodel.serializers import ThriftSerializer
from pymodel.serializers import YamlSerializer
from pymodel.serializers import XMLSerializer
from pymodel.serializers import ThriftBase64Serializer

from pymodel import ROOTOBJECT_TYPES

class Domain(object):
    pass

class PyModelAccessor(object):
    
    def __init__(self, rootobject_type):
        '''Initialize a new pymodel root object accessor
        '''
        self._ROOTOBJECTTYPE = rootobject_type    
    
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
    


class PyModel(object):

    __shared_state = {}
    
    def __init__(self):
        self.__dict__ = self.__shared_state
        
        # Keep track of domains
        self._domains = {}
        
        if not hasattr(self, 'initialized'):
            self.__initialize()
            setattr(self, 'initialized', True)
            
    def importDomain(self, domainname, specpath):

        domain = Domain()      
        
        init(specpath, domainname)
                 
        from pymodel import ROOTOBJECT_TYPES as types
        for type in types[domainname].itervalues():
            name = getattr(type, 'PYMODEL_TYPE_NAME', type.__name__.lower())
            setattr(domain, name, PyModelAccessor(type))
            
        setattr(self, domainname, domain)
        self._domains[domainname] = domain
        
    def listDomains(self):
        '''
        Returns the list of imported domain names
        '''
        return self._domains.keys()
                    
    def __initialize(self):        
        parentPath = q.system.fs.joinPaths(q.dirs.baseDir, 'lib', 'pymonkey', 'models')
        pymonkeyPath = q.system.fs.joinPaths(q.dirs.baseDir, 'lib', 'pymonkey')

        if not pymonkeyPath in sys.path:
            sys.path.append(pymonkeyPath)
 
        if not q.system.fs.exists(parentPath):
            q.system.fs.createDir(parentPath)
        
        for subPath in q.system.fs.listDirsInDir(parentPath):
            subPath = q.system.fs.getBaseName(subPath)
            domainname = subPath
            specpath = q.system.fs.joinPaths(parentPath, subPath)
            self.importDomain(domainname, specpath)
            
            