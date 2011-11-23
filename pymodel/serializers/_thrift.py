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

import datetime
import time
import logging

from thrift.Thrift import TType
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
try:
    from thrift.protocol import fastbinary
except:
    fastbinary = None

logger = logging.getLogger('pymodel.thrift')

try:
    from pymonkey.baseclasses import BaseEnumeration
except ImportError:
    logger.info('No PyMonkey Enumeration support')
    BaseEnumeration = None

import pymodel
from pymodel import Model
from pymodel.model import DEFAULT_FIELDS
from pymodel.fields import EmptyObject, WrappedDict, WrappedList

TYPE_SPEC_CACHE = dict()

def struct_args(attr):
    return (attr.type_, generate_thrift_spec(attr.type_.PYMODEL_MODEL_INFO))

def dict_args(attr):
    return (TType.STRING, None,
            FIELD_TYPE_THRIFT_TYPE_MAP[type(attr.type_)](attr.type_),
            FIELD_TYPE_ATTR_ARGS_MAP[type(attr.type_)](attr.type_))

def list_args(attr):
    return (FIELD_TYPE_THRIFT_TYPE_MAP[type(attr.type_)](attr.type_),
            FIELD_TYPE_ATTR_ARGS_MAP[type(attr.type_)](attr.type_))

FIELD_TYPE_ATTR_ARGS_MAP = {
    pymodel.GUID: lambda o: None,
    pymodel.String: lambda o: None,
    pymodel.Integer: lambda o: None,
    pymodel.Boolean: lambda o: None,
    pymodel.Object: struct_args,
    pymodel.Float: lambda o: None,
    pymodel.Dict: dict_args,
    pymodel.List: list_args,
    pymodel.Enumeration: lambda o: None,
    pymodel.DateTime: lambda o: None,
}

FIELD_TYPE_THRIFT_TYPE_MAP = {
    pymodel.GUID: lambda o: TType.STRING,
    pymodel.String: lambda o: TType.STRING,
    pymodel.Integer: lambda o: TType.I64,
    pymodel.Boolean: lambda o: TType.BOOL,
    pymodel.Object: lambda o: TType.STRUCT,
    pymodel.Float: lambda o: TType.DOUBLE,
    pymodel.Dict: lambda o: TType.MAP,
    pymodel.List: lambda o: TType.LIST,
    pymodel.Enumeration: lambda o: TType.STRING,
    pymodel.DateTime: lambda o: TType.I64,
}

def generate_thrift_spec(typeinfo):
    try:
        return TYPE_SPEC_CACHE[typeinfo]
    except KeyError:
        pass

    logger.info('Generating thrift spec for %s' % typeinfo.name)

    spec = [None, ]
    id_ = len(spec)

    def get_thrift_id(field):
        if field.attribute in DEFAULT_FIELDS:
            field.attribute.kwargs['thrift_id'] = \
                    list(DEFAULT_FIELDS).index(field.attribute) + 1
        else:
            field.attribute.kwargs['thrift_id'] += 10

        return field.attribute.kwargs['thrift_id']

    attributes = sorted(typeinfo.attributes,
                        key=get_thrift_id)

    for attribute in attributes:
        name = attribute.name
        attr = attribute.attribute
        aid = attr.kwargs['thrift_id']

        if aid < id_:
            raise RuntimeError

        while aid > id_:
            spec.append(None)
            id_ += 1

        assert len(spec) == aid
        args = FIELD_TYPE_ATTR_ARGS_MAP[type(attr)](attr)
        thrift_type = FIELD_TYPE_THRIFT_TYPE_MAP[type(attr)](attr)
        spec.append((aid, thrift_type, name, args, None, ))

        id_ = len(spec)

    ret = TYPE_SPEC_CACHE[typeinfo] = tuple(spec)
    return ret



WRITE_TYPE_HANDLERS = {
    TType.STRING: lambda data, prot, info: prot.writeString(data),
    TType.I32: lambda data, prot, info: prot.writeI32(data),
    TType.I64: lambda data, prot, info: prot.writeI64(data),
    TType.BOOL: lambda data, prot, info: prot.writeBool(data),
    TType.DOUBLE: lambda data, prot, info: prot.writeDouble(data),
    TType.STRUCT: lambda data, prot, info: _write_struct(data, prot, info),
    TType.LIST: lambda data, prot, info: _write_list(data, prot, info),
    TType.MAP: lambda data, prot, info: _write_map(data, prot, info),
}

def _write_map(data, prot, info):
    assert info[0] == TType.STRING, 'Only string keys supported'

    prot.writeMapBegin(info[0], info[2], len(data))

    for key, value in data.iteritems():
        prot.writeString(key)
        WRITE_TYPE_HANDLERS[info[2]](value, prot, info[3])
    prot.writeMapEnd()

def _write_list(data, prot, info):
    prot.writeListBegin(info[0], len(data))
    for item in data:
        WRITE_TYPE_HANDLERS[info[0]](item, prot, info[1])
    prot.writeListEnd()

def _write_struct(data, prot, info):
    prot.writeStructBegin(data.__class__.__name__)

    info = info[1]

    for field in (f for f in info if f):
        fid, ftype, fname, finfo, fdefault = field
        value = getattr(data, fname)
        if not value and value is not False and not value == 0:
            continue

        prot.writeFieldBegin(fname, ftype, fid)
        WRITE_TYPE_HANDLERS[ftype](value, prot, finfo)
        prot.writeFieldEnd()

    prot.writeFieldStop()
    prot.writeStructEnd()

def thrift_write(obj, spec, _force_native=False):
    transport = TTransport.TMemoryBuffer()
    protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)
    transport.open()
    if protocol.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and \
       spec is not None and \
       fastbinary is not None and \
       not _force_native:
        protocol.trans.write(fastbinary.encode_binary(obj,
                                   (obj.__class__, spec)))

    else:
        _write_struct(obj, protocol, (None, spec, ))

    bytes = transport.getvalue()
    transport.close()

    return bytes



READ_TYPE_HANDLERS = {
    TType.STRING: lambda prot, info: prot.readString(),
    TType.I32: lambda prot, info: prot.readI32(),
    TType.I64: lambda prot, info: prot.readI64(),
    TType.BOOL: lambda prot, info: prot.readBool(),
    TType.DOUBLE: lambda prot, info: prot.readDouble(),
    TType.STRUCT: lambda prot, info: _read_struct(prot, info),
    TType.LIST: lambda prot, info: _read_list(prot, info),
    TType.MAP: lambda prot, info: _read_map(prot, info),
}

def _read_map(prot, info):
    obj = dict()

    ktype, vtype, size = prot.readMapBegin()
    assert ktype == TType.STRING, 'Only string keys are supported'

    for i in xrange(size):
        key = prot.readString()
        value = READ_TYPE_HANDLERS[vtype](prot, info[3])
        obj[key] = value

    prot.readMapEnd()

    return obj

def _read_list(prot, info):
    obj = list()

    type_, size = prot.readListBegin()

    for i in xrange(size):
        item = READ_TYPE_HANDLERS[type_](prot, info[1])
        obj.append(item)

    prot.readListEnd()

    return obj


def _read_struct(protocol, spec, obj=None):
    obj = obj or spec[0]()

    struct_info = spec[1]
    protocol.readStructBegin()

    while True:
        fname, ftype, fid = protocol.readFieldBegin()
        if ftype == TType.STOP:
            break

        field_info = None
        for item in struct_info:
            if item and item[0] == fid:
                field_info = item

        if not field_info:
            logger.info('Unknown field %s (id %d)' % (fname, fid))
            # Unknown field
            protocol.skip(ftype)
            protocol.readFieldEnd()
            continue

        if not ftype == field_info[1]:
            raise RuntimeError('Field of invalid type, corrupted?')

        handler = READ_TYPE_HANDLERS[ftype]
        value = handler(protocol, field_info[3])
        setattr(obj, field_info[2], value)

        protocol.readFieldEnd()
    protocol.readStructEnd()

    return obj


def thrift_read(obj, spec, data, _force_native=False):
    transport = TTransport.TMemoryBuffer(data)
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)

    if protocol.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and \
       isinstance(protocol.trans, TTransport.CReadableTransport) and \
       spec is not None and \
       fastbinary is not None and \
       not _force_native:
        fastbinary.decode_binary(obj, protocol.trans,
                                 (obj.__class__, spec))
        return

    _read_struct(protocol, (None, spec, ), obj)


def _native_type(obj):
    # Warning
    # Whenever changing the code below the following block, make sure the
    # conditions in this block are altere appropriately
    if not isinstance(obj, (EmptyObject, Model, WrappedList, WrappedDict)):
        if BaseEnumeration:
            if not isinstance(obj, BaseEnumeration):
                return obj
        else:
            return obj

    if isinstance(obj, EmptyObject):
        return None

    elif isinstance(obj, Model):
        return ThriftObjectWrapper(obj)

    elif isinstance(obj, WrappedList):
        return [_native_type(item) for item in obj]

    elif isinstance(obj, WrappedDict):
        return dict((key, _native_type(value)) \
                    for (key, value) in obj.iteritems())

    elif BaseEnumeration:
        if isinstance(obj, BaseEnumeration):
            #TODO Get rid of protected lookup
            return getattr(obj, '_pm_enumeration_name')

    # LEAVE THIS LINE AS-IS
    assert False, 'Not reached'

def _serialize_datetime(dt):
    if dt: return time.mktime(dt.timetuple())

def _deserialize_datetime(d):
    if d: return datetime.datetime.fromtimestamp(d)

ATTRIBUTE_SERIALIZER_MAP = {
    pymodel.GUID: lambda o: o,
    pymodel.String: lambda o: o,
    pymodel.Integer: lambda o: o,
    pymodel.Boolean: lambda o: o,
    pymodel.Object: lambda o: o,
    pymodel.Float: lambda o: o,
    pymodel.Dict: lambda o: o,
    pymodel.List: lambda o: o,
    pymodel.Enumeration: lambda o: o,
    pymodel.DateTime: _serialize_datetime,
}

ATTRIBUTE_DESERIALIZER_MAP = {
    pymodel.GUID: lambda o: o,
    pymodel.String: lambda o: o,
    pymodel.Integer: lambda o: o,
    pymodel.Boolean: lambda o: o,
    pymodel.Object: lambda o: o,
    pymodel.Float: lambda o: o,
    pymodel.Dict: lambda o: o,
    pymodel.List: lambda o: o, 
    pymodel.Enumeration: lambda o: o,
    pymodel.DateTime: _deserialize_datetime,
}

class ThriftObjectWrapperBase(object):
    def __init__(self, object_):
        self._object = object_

        self._attribute_types = dict([(attr.name, type(attr.attribute))
            for attr in object_.PYMODEL_MODEL_INFO.attributes])

class ThriftObjectWrapper(ThriftObjectWrapperBase):
    def __init__(self, object_):
        ThriftObjectWrapperBase.__init__(self, object_)

    def __getattr__(self, name):
        attr = getattr(self._object, name)

        f = ATTRIBUTE_SERIALIZER_MAP[self._attribute_types[name]]

        return _native_type(f(attr))

    def __setattr__(self, name, value):
        if name in ('_object', '_attribute_types'):
            ThriftObjectWrapperBase.__setattr__(self, name, value)
            return

        object_ =  ThriftObjectWrapperBase.__getattribute__(self, '_object')

        f = ATTRIBUTE_DESERIALIZER_MAP[self._attribute_types[name]]

        setattr(object_, name, f(value))


class ThriftSerializer(object):
    NAME = 'thrift'
    FORCE_NATIVE = False

    @classmethod
    def serialize(cls, object_):
        object_type = type(object_)
        model_info = object_type.PYMODEL_MODEL_INFO
        spec = generate_thrift_spec(model_info)
        wrapped = ThriftObjectWrapper(object_)
        data = thrift_write(wrapped, spec, _force_native=cls.FORCE_NATIVE)
        return data

    @classmethod
    def deserialize(cls, type_, data):
        model_info = type_.PYMODEL_MODEL_INFO
        spec = generate_thrift_spec(model_info)
        object_ = type_()
        wrapper = ThriftObjectWrapper(object_)
        thrift_read(wrapper, spec, data, _force_native=cls.FORCE_NATIVE)
        return wrapper._object


if fastbinary:
    class OptimizedSerializer(ThriftSerializer):
        NAME = '_ThriftOptimized'
        FORCE_NATIVE = False

class NativeSerializer(ThriftSerializer):
    NAME = '_ThriftNative'
    FORCE_NATIVE = True
