import os
import re
import keyword

IDENTIFIER_RE = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')

#TODO This could become a more general function
def isValidIdentifier(identifier):
    '''Check whether a given string is a valid Python identifier (variable name)

    In several places (when using user-provided names to create properties or
    attributes) we should be able to alert the user when attempting to use an
    invalid identifier, as defined by the Python grammar.

    This method checks names against the grammar snippet specified in the
    Python language reference (http://docs.python.org/ref/identifiers.html).

    It also filters out keywords.

    @param identifier: Identifier to check
    @type identified: string

    @returns: Whether or not the provided identifier is valid
    @rtype: bool
    '''
    if not IDENTIFIER_RE.match(identifier):
        return False

    if keyword.iskeyword(identifier):
        return False

    return True

class _EnumerationContainer:
    '''Dummy container class to expose enumerations on q'''

enumerations = _EnumerationContainer()


def generateRegisterItem():
    '''Generate an C{BaseEnumeration.registerItem} method

    We need this external generator so we can add the registerItem method to
    subclasses of BaseEnumeration in their metaclass.

    We need to set the methods per subclass, otherwise we can't delete the method
    attribute from the class when the consumer calls C{finishItemRegistration}.
    '''
    def registerItem(cls, itemname, *args, **kwargs):
        '''Register a new item in the enumeration

        The C{itemname} argument will be uppercased and become the class
        attribute name.
        *args and **kwargs are passed to the class constructor as-is.

        @param itemname: name of enumeration item, will be uppercased
        @type itemname: string
        @param *args: arguments passed to class constructor
        @param **kwargs: arguments passed to class constructor
        '''
        attrname = itemname.upper()
        '''Name of the attribute on the class this instance will be bound to'''

        #Check whether this is a valid identifier, ie can we use it as
        #attribute name
        if not isValidIdentifier(attrname):
            raise ValueError('The given item name \'%s\' is not a valid identifier when converted to attribute name \'%s\'. It should be a valid Python identifier' % (itemname, attrname))

        instance = cls(*args, **kwargs)
        '''Class instance to use in the enumeration'''
        #if not hasattr(cls, '_pm_name2level'):
            #cls._pm_name2level = dict()            
        if not hasattr(cls, '_pm_level2name'):
            cls._pm_level2name = dict()
            
        if instance.__dict__.has_key("level"):
            #cls._pm_name2level[itemname] = instance.level
            cls._pm_level2name[instance.level] = instance

        if not hasattr(cls, '_pm_enumeration_items'):
            cls._pm_enumeration_items = dict()
            '''Holder for instances, used by getByName'''

        cls._pm_enumeration_items[itemname] = instance

        #Internal, used for filtering in qshell
        setattr(instance, '_pm_enumeration_hidden', True)
        setattr(instance, '_pm_enumeration_name', itemname)

        #Set attribute on class
        setattr(cls, attrname, instance)

    #Internal, used for filtering in qshell
    #This removes MyEnu.FOO.registerItem, since this should not be visible
    registerItem._pm_enumeration_hidden = True

    return registerItem


def generateFinishItemRegistration():
    '''Generate an C{BaseEnumeration.finishItemRegistration} method

    We need this external generator so we can add the finishItemRegistration
    method to subclasses of BaseEnumeration in their metaclass.

    We need to set the methods per subclass, otherwise we can't del the method
    attribute from the class when the consumer calls finishItemRegistration.
    '''
    def finishItemRegistration(cls):
        '''Finish item registration

        Call this method when all enumeration items are created and no more
        should be creatable.
        '''
        def __init__(self, *args, **kwargs):
            '''Custom constructor which disables further instance creation'''
            raise RuntimeError('No more %s instances should be created, it\'s a finished enumeration' % cls.__name__)

        #Overwrite the class constructor to one which errors out
        #This way no further instances of the enumeration type, next to the
        #registered ones, can be created.
        cls.__init__ = __init__

        #Remove the finishItemRegistration and registerItem methods from the
        #class and its instances
        del cls.finishItemRegistration
        del cls.registerItem

    #Internal, used for filtering in qshell
    finishItemRegistration._pm_enumeration_hidden = True

    return finishItemRegistration


class BaseEnumerationMeta(type):
    '''Meta class for BaseEnumeration and its subclasses

    Why do we need this?
    --------------------
    We want to be able to remove the registerItem and finishItemRegistration
    methods from subclasses of BaseEnumeration at runtime, more precisely after
    finishItemRegistration on a subclass is called.

    These methods are attributes at class-level (ie. on the enumeration
    subclass or one of its parents).

    We can not place the methods in the BaseEnumeration class (which would be more
    logical), because if we'd put it there, removing the desired methods from
    subclasses won't work, because they are not attributes on the actual
    subclass (they are attributes on the parent Enumeration class). We could
    obviously remove them from the parent BaseEnumeration class, but then, all at
    once, the method would be completely gone on _any_ subclass of BaseEnumeration
    as well, including unfinished enumerations. Which is not exactly the
    desired behaviour.

    How to solve this
    -----------------
    As explained in the previous paragraphs, we can't have registerItem and
    finishItemRegistration on the BaseEnumeration class, so we should add them as
    attributes to the actual enumeration subclasses. This way we _can_ remove
    the methods from the class (and it's instances) at runtime.

    This is exactly what this metaclass does: it generates the desired methods
    using some method generators, and adds them as attributes on the
    BaseEnumeration subclasses.

    It does not add the methods on the BaseEnumeration type itself, so this class
    is (and should be) useless as-is.
    '''

    _enumeration_types = dict()
    '''This will store all enumerations we ever met, so we don't re-register,
    not even when doing imp.load_module to load an extension'''

    def __new__(cls, name, bases, attrs):
        ret = super(BaseEnumerationMeta, cls).__new__(cls, name, bases, attrs)

        #This gets the file a class is defined in, without its extension
        import inspect
        modfile = lambda klass: os.path.splitext(os.path.abspath(inspect.getfile(klass)))[0]

        try:
            ret = BaseEnumerationMeta._enumeration_types[(modfile(ret), name, )]

            if not '_INTERMEDIATE_CLASS' in attrs:
                #If the enumeration is sealed/finished, we still need to provide
                #dummy behaviour, since registerItem etc can be re-called on it
                ret.registerItem = classmethod(lambda *args, **kwargs: None)
                ret.finishItemRegistration = classmethod(generateFinishItemRegistration())

            return ret

        except KeyError:
            pass

        try:
            #Check whether BaseEnumeration is already defined. If it isn't, we're
            #registering BaseEnumeration itself, so the methods should not be added
            BaseEnumeration
        except NameError:
            return ret

        #This is the case for non-final enumeration types, eg EnumerationWithValue
        if '_INTERMEDIATE_CLASS' in attrs:
            pass
        else:
            #Add methods to the class
            ret.registerItem = classmethod(generateRegisterItem())
            ret.finishItemRegistration = classmethod(generateFinishItemRegistration())

        BaseEnumerationMeta._enumeration_types[(modfile(ret), name, )] = ret

        #Call class._initItems
        getattr(ret, '_initItems', lambda: None)()

        #Since we can't hook enumerations on pymonkey.q directly, since 'q'
        #could be not initialized when the first enumeration type is created.
        #To get around this, we use a module-global container variable which
        #gets populated, and should be hooked onto pymonkey.q whenever
        #applicable.
        #
        #For some reason, it was decided to use smallCapStarting names for
        #enumerations registered on q.enumerators, although they're types.
        #I guess this should be emulated here.
        if hasattr(enumerations, name):
            raise RuntimeError('Unable to register enumeration %s, name already in use' % name)
        else:
            setattr(enumerations, name, ret)

        return ret

##workaround to be able to serialize enums
def getEnumName(name):
    return name

class BaseEnumeration(object):
    '''Base class for any enumeration-style class

    If you are creating a subclass of BaseEnumeration which is *not* a 'final'
    class (ie representing a real-world object, just creating an BaseEnumeration
    type which provides some more functionality which should be subclassed as
    well), you should add an attribute called _INTERMEDIATE_CLASS to your
    intermediate class so the BaseEnumeration type system can take this into
    account when adding methods to final classes.

    Subclasses of BaseEnumeration can have a classmethod called C{_initItems}
    which will be called when the corresponding type is constructed. Thisq.enumerators.MessageType.UNKNOWN
    allows you to add items to an enumeration inside the enumeration
    definition, eg:

    >>> class MyEnumeration(BaseEnumeration):
    ...     @classmethod
    ...     def _initItems(cls):
    ...         cls.registerItem('foo')
    ...         cls.registerItem('bar')
    ...         cls.finishItemRegistration()
    ...
    >>> print MyEnumeration.FOO
    foo
    >>> print MyEnumeration.BAR
    bar
    '''

    #Set type generator so registerItem and finishItemRegistration are added
    #if necessary
    __metaclass__ = BaseEnumerationMeta

    def getByName(cls, itemname):
        '''Get enumeration value based on item name as provided to L{registerItem}'''
        try:
            return cls._pm_enumeration_items[itemname]
        except KeyError:
            raise KeyError('Enumeration %s got no item with name %s' % \
                    (cls.__name__, itemname))

    def getByLevel(cls, level):
        '''
        Get enumeration value based on item level as provided to L{registerItem}
        only works for enumeration where level has been defined
        '''
        try:
            return cls._pm_level2name[level]
        except KeyError:
            raise KeyError('Enumeration %s got no item with level %s' % \
                    (cls.__name__, level))
        
    getByName._pm_enumeration_hidden = True
    getByName = classmethod(getByName)
    getByLevel = classmethod(getByLevel)

    ##workaround to be able to serialize enums
    def __reduce_ex__(self,prot):
        return (getEnumName, (str(self),))

    def __str__(self):
        return self._pm_enumeration_name

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return type(self) == type(other) and self._pm_enumeration_name == other._pm_enumeration_name

    @classmethod
    def check(cls, value):
        '''Type check for this enumeration type

        This method checks whether the provided argument value is an instance
        of this enumeration type and is registered on it.

        @param value: Value to validate
        @type value: BaseEnumeration subclass
        @returns: Whether value is a valid enumeration item
        @rtype: bool
        '''
        return isinstance(value, cls) and \
                value is cls._pm_enumeration_items[value._pm_enumeration_name]

    def printdoc(self):
        #@todo get this to work
        print __doc__
