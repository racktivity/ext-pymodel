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
    
import xml.dom.minidom as dom
import osis.model
from osis.model.fields import EmptyObject
from pymonkey.baseclasses.BaseEnumeration import BaseEnumeration

def getType(obj):
    """ generates string representation of class of obj 
        discarding decoration """
    return str(obj.__class__).split("'")[1].split(".")[-1]

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
    osis.model.String: lambda a, o: o,
    osis.model.Enumeration: lambda a, o: enum_to_string(o),
    osis.model.GUID: lambda a, o: o,
    osis.model.Integer: lambda a, o: o,
    osis.model.Float: lambda a, o: o,
    osis.model.Boolean: lambda a, o: o,
    osis.model.List: handle_list,
    osis.model.Dict: handle_dict,
    osis.model.Object: lambda a, o: object_to_dict(o),
    osis.model.DateTime: lambda a, o: o,
}


def object_to_dict(object_):
    if isinstance(object_, EmptyObject):
        return None

    data = dict()
    spec = type(object_).OSIS_MODEL_INFO

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
    osis.model.String: lambda a, o: o,
    osis.model.Enumeration: lambda a, o: o,
    osis.model.GUID: lambda a, o: o,
    osis.model.Integer: lambda a, o: o,
    osis.model.Float: lambda a, o: o,
    osis.model.Boolean: lambda a, o: o,
    osis.model.Dict: load_dict,
    osis.model.Object: lambda a, o: dict_to_object(a.type_(), o),
    osis.model.List: load_list,
    osis.model.DateTime: lambda a, o:o,
}

def dict_to_object(object_, data):
    spec = type(object_).OSIS_MODEL_INFO

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

def pickle(root, fabric, elementName="root"):

    node = fabric.createElement(elementName)
    typeStr = getType(root)
    node.attributes["type"]=typeStr    
    node.appendChild(fabric.createTextNode(str(root)))
    return node

def pickleDictItems(root):
    fabric = dom.Document()
    node = fabric.createElement("root")
    for key, value in root.items():
        tempnode = fabric.createElement("item")
        tempnode.appendChild(pickle(key, fabric, "key"))
        tempnode.appendChild(pickle(value, fabric, "value"))
        node.appendChild(tempnode)
    return node

def _getElementChilds(node, doLower = 1):
    """ returns list of (tagname, element) for all element childs of node """

    dolow = doLower and (lambda x:x.lower()) or (lambda x:x)
    return [ (dolow(no.tagName), no) for no in node.childNodes if no.nodeType != no.TEXT_NODE ]

def _getText(nodelist):
    """ returns collected and stripped text of textnodes among nodes in nodelist """
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.strip()

def unpickle(node):
    typeName= node.attributes["type"].value
    initValue = _getText(node.childNodes)
    value = eval("%s(%r)" % (typeName, initValue))
    return value

def unpickleDict(node):
    dd = dict()
    for name, element in _getElementChilds(node):
        if name != "item":
            raise XMLUnpicklingException()
        childList = _getElementChilds(element)
        if len(childList) != 2:
            raise XMLUnpicklingException()
        for name, element in childList:
            if name=="key":
                key = unpickle(element)
            elif name=="value":
                value = unpickle(element)
        dd[key]=value
    return dd 




class XMLSerializer(object):
    
    @classmethod
    def serialize(cls, data):    
        data = object_to_dict(data)
        #return pickle(root=data, fabric=dom.Document())
        return pickleDictItems(data)
            
    @classmethod
    def deserialize(cls, type_, data):   
        object_ = type_()     
        #data = unpickle(data)
        data = unpickleDict(data)
        dict_to_object(object_, data)
        return object_