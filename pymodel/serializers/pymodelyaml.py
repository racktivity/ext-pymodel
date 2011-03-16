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

import yaml

import pymodel
from pymodel.fields import EmptyObject
from pylabs.baseclasses.BaseEnumeration import BaseEnumeration


def handle_list(attr, value):
    data = list()
    type_handler = TYPE_HANDLERS[type(attr.type_)]
    for item in value:
        data.append(type_handler(None, item))

    return data

def handle_dict(attr, value):
    data = dict()
    type_handler = TYPE_HANDLERS[type(attr.type_)]
    for k, v in value.iteritems():
        data[k] = type_handler(None, v)

    return data


def enum_to_string(obj):
    if isinstance(obj, BaseEnumeration):
        #TODO Get rid of protected lookup
        return getattr(obj, '_pm_enumeration_name')


TYPE_HANDLERS = {
    pymodel.String: lambda a, o: o,
    pymodel.Enumeration: lambda a, o: enum_to_string(o),
    pymodel.GUID: lambda a, o: o,
    pymodel.Integer: lambda a, o: o,
    pymodel.Float: lambda a, o: o,
    pymodel.Boolean: lambda a, o: o,
    pymodel.List: handle_list,
    pymodel.Dict: handle_dict,
    pymodel.Object: lambda a, o: object_to_dict(o),
    pymodel.DateTime: lambda a, o: o,
}


def object_to_dict(object_):
    if isinstance(object_, EmptyObject):
        return None

    data = dict()
    spec = type(object_).PYMODEL_MODEL_INFO

    for attribute in spec.attributes:
        attr = attribute.attribute

        try:
            value = getattr(object_, attr.name)
        except AttributeError:
            value = None

        if value is None:
            continue

        handler = TYPE_HANDLERS[type(attr)]

        value = handler(attr, value)
        if value is None:
            continue

        data[attr.name] = value

    return data


def load_dict(attr, data):
    result = dict()
    type_ = attr.type_
    handler = TYPE_SET_HANDLERS[type(type_)]

    for key, value in data.iteritems():
        result[key] = handler(type_, value)

    return result

def load_list(attr, data):
    result = list()
    type_ = attr.type_
    handler = TYPE_SET_HANDLERS[type(type_)]

    for item in data:
        result.append(handler(type_, item))

    return result

TYPE_SET_HANDLERS = {
    pymodel.String: lambda a, o: o,
    pymodel.Enumeration: lambda a, o: o,
    pymodel.GUID: lambda a, o: o,
    pymodel.Integer: lambda a, o: o,
    pymodel.Float: lambda a, o: o,
    pymodel.Boolean: lambda a, o: o,
    pymodel.Dict: load_dict,
    pymodel.Object: lambda a, o: dict_to_object(a.type_(), o),
    pymodel.List: load_list,
    pymodel.DateTime: lambda a, o:o,
}

def dict_to_object(object_, data):
    spec = type(object_).PYMODEL_MODEL_INFO

    for attribute in spec.attributes:
        attr = attribute.attribute

        try:
            value = data[attr.name]
        except KeyError:
            continue

        if value is None:
            continue

        handler = TYPE_SET_HANDLERS[type(attr)]

        value = handler(attr, value)
        if value is None:
            continue

        setattr(object_, attr.name, value)

    return object_

class YamlSerializer(object):
    NAME = 'yaml'

    @staticmethod
    def serialize(object_):
        data = object_to_dict(object_)
        return yaml.dump(data, default_flow_style=False)

    @staticmethod
    def deserialize(type_, data):
        object_ = type_()
        data = yaml.load(data)
        dict_to_object(object_, data)
        return object_
