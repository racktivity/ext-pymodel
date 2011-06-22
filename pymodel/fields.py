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

import operator
import uuid
class Field(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __get__(self, obj, objtype=None):
        if obj is None:
           # Accessed through class, not object
           return None
        try:
            return obj._pymodel_store[self.name]
        except KeyError:
            return None

    def __set__(self, obj, value):
        if not isinstance(value, self.VALID_TYPE) and value is not None:
            raise TypeError(
                'Only objects of type %s can be assigned to this field' % \
                str(self.VALID_TYPE))

        obj._pymodel_store[self.name] = value

    def __delete__(self, obj):
        try:
            obj._pymodel_store[self.name]
        except KeyError:
            #raise AttributeError
            pass

    def _set_name(self, name):
        self._name = name

    name = property(fget=operator.attrgetter('_name'), fset=_set_name)

class ExposedField: pass

class Integer(Field, ExposedField):
    VALID_TYPE = int

class Float(Field, ExposedField):
    VALID_TYPE = float

class String(Field, ExposedField):
    VALID_TYPE = basestring

class GUID(String):
    pass

class Boolean(Field, ExposedField):
    VALID_TYPE = bool

class EmptyObject: pass

def _ObjectHelper(type_):
    class _Helper(object, EmptyObject):
        def new(self, *args, **kwargs):
            return type_(*args, **kwargs)

        def __nonzero__(self):
            return False

    return _Helper()

class Object(Field, ExposedField):
    def __init__(self, type_, **kwargs):
        self.type_ = type_
        Field.__init__(self, **kwargs)
        self.helper = _ObjectHelper(self.type_)

    def __get__(self, obj, objtype=None):
        try:
            value = Field.__get__(self, obj, objtype)
        except AttributeError:
            return self.helper

        if value is None:
            return self.helper

        return value

    def __set__(self, obj, value):
        if value is not None:
            Field.__set__(self, obj, value)
        else:
            try:
                Field.__delete__(self, obj)
            except AttributeError:
                pass
            obj._pymodel_store[self.name] = self.helper

    VALID_TYPE = property(fget=operator.attrgetter('type_'))


class Enumeration(String):
    def __init__(self, type_, **kwargs):
        self.type_ = type_
        Field.__init__(self, **kwargs)

    def __get__(self, obj, objtype=None):
        try:
            value = String.__get__(self, obj, objtype)
        except AttributeError:
            return None

        if value in (None,''):
            return None

        return self.type_.getByName(value)

    def __set__(self, obj, value):
        if not isinstance(value, basestring):
            if not isinstance(value, self.type_) and value is not None:
                raise TypeError(
                    'Only objects of type %s can be assigned '
                    'to this field' % str(self.VALID_TYPE))

            value = value._pm_enumeration_name if value else None


        String.__set__(self, obj, value)

class DateTime(Float):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __set__(self, obj, value):
        from datetime import datetime as dttime
        if not isinstance(value, dttime) and value is not None:
            raise TypeError('Only objects of type Datetime can be assigned to this field')

        obj._pymodel_store[self.name] = value

class Container(Field):
    pass

class SimpleContainer(Container):
    def __init__(self, type_, **kwargs):
        self.type_ = type_
        Container.__init__(self, **kwargs)


class WrappedList: pass
def TypedList(type_):
    class _List(object, WrappedList):
        def __init__(self, sequence=None):
            self._list = list()

            if sequence:
                for item in sequence:
                    if isinstance(item, dict):
                        item = type_.VALID_TYPE(**item)
                    if not isinstance(item, type_.VALID_TYPE):
                        raise TypeError('Only objects of type %s '
                                        'can be stored' % \
                                        type_.VALID_TYPE.__name__)
                    self.append(item)

        def append(self, object_):
            if not isinstance(object_, type_.VALID_TYPE):
                raise TypeError('Only objects of type %s can be stored' % \
                                    type_.VALID_TYPE.__name__)
            if hasattr(object_, 'guid') and not object_.guid:
                object_.guid = str(uuid.uuid4())
            if hasattr(object_, 'version') and not object_.version:
                object_.version = str(uuid.uuid4())
            self._list.append(object_)

        def remove(self, object_):
            if object_ in self._list:
                self._list.remove(object_)

        def __getitem__(self, index):
            return self._list[index]

        def new(self, *args, **kwargs):
            return type_.VALID_TYPE(*args, **kwargs)

        def __len__(self):
            return self._list.__len__()

        def __eq__(self, other):
            if other == None:
                return False
            return self._list.__eq__(other._list)

        def __ne__(self, other):
            if other == None:
                return True
            return self._list.__ne__(other._list)

        def __str__(self):
            return self._list.__str__()

        def __repr__(self):
            return self._list.__repr__()

    return _List

class List(SimpleContainer, ExposedField):
    def __init__(self, type_, **kwargs):
        SimpleContainer.__init__(self, type_, **kwargs)
        self.listtype = TypedList(type_)

    def __get__(self, obj, objtype=None):
        try:
            value = SimpleContainer.__get__(self, obj, objtype)
        except AttributeError:
            pass
        else:
            if value is not None:
                return value

        value = self.listtype()
        SimpleContainer.__set__(self, obj, value)

        return value

    def __set__(self, obj, value):
        SimpleContainer.__set__(self, obj, self.listtype(value))

    VALID_TYPE = property(fget=operator.attrgetter('listtype'))


import UserDict

class WrappedDict: pass

def TypedDict(type_):
    class _Dict(object, UserDict.DictMixin, WrappedDict):
        def __init__(self, dict_=None):
            self._dict = dict()

            if dict_:
                for key, value in dict_.iteritems():
                    if not isinstance(key, basestring):
                        raise TypeError('Dictionary keys should be strings')
                    if not isinstance(value, type_.VALID_TYPE):
                        raise TypeError('Only objects of type %s '
                                        'can be stored' % \
                                        type_.VALID_TYPE.__name__)
                    self._dict[key] = value

        def __getitem__(self, key):
            return self._dict.__getitem__(key)

        def __setitem__(self, key, value):
            if not isinstance(key, basestring):
                raise TypeError('Dictionary keys should be strings')
            if not isinstance(value,type_.VALID_TYPE):
                raise TypeError('Only objects of type %s '
                                'can be stored' % \
                                type_.VALID_TYPE.__name__)
            self._dict.__setitem__(key, value)

        def __delitem__(self, key):
            return self._dict.__delitem__(key)

        def keys(self):
            return self._dict.keys()

        def new(self, *args, **kwargs):
            return type_.VALID_TYPE(*args, **kwargs)

        def __eq__(self, other):
            if other ==None:
                return False
            return self._dict.__eq__(other._dict)

        def __ne__(self, other):
            if other ==None:
                return True
            return self._dict.__ne__(other._dict)

        def __str__(self):
            return self._dict.__str__()

        def __repr__(self):
            return self._dict.__repr__()

    return _Dict


class Dict(SimpleContainer, ExposedField):
    def __init__(self, type_, **kwargs):
        SimpleContainer.__init__(self, type_, **kwargs)
        self.dicttype = TypedDict(type_)

    def __get__(self, obj, objtype=None):
        try:
            value = SimpleContainer.__get__(self, obj, objtype)
        except AttributeError:
            pass
        else:
            if value is not None:
                return value

        value = self.dicttype()
        self.__set__(obj, value)

        return value

    def __set__(self, obj, value):
        if isinstance(value, dict) and not isinstance(value, self.dicttype):
            value = self.dicttype(value)

        super(Dict, self).__set__(obj, value)

    VALID_TYPE = property(fget=operator.attrgetter('dicttype'))
