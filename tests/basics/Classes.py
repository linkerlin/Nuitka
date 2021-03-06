#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
class SimpleClass:
    """ The class documentation."""


    # TODO: Doesn't work with Python3, because we don't yet make our own dict visible.
    # print locals()
    print str( locals() ).replace( "'__locals__': {...}, ", "" )

    class_var = 1

    def __init__( self, init_parameter ):
        self.x = init_parameter

    def normal_method( self, arg1, arg2 ):
        self.arg1 = arg1
        self.arg2 = arg2

        return self.arg1, self.arg2, self.x, self

    @staticmethod
    def static_method():
        return "something"

print "Simple class:", SimpleClass
print "Lives in", SimpleClass.__module__
print "Documentation", SimpleClass.__doc__
print "Instantiate simple class:", SimpleClass( 14 )
print "Call simple class normal method:", SimpleClass( 11 ).normal_method( 1, 2 )
print "Call simple class static method:", SimpleClass( 11 ).static_method()

class MetaClass( type ):
    def __init__( cls, name, bases, dictionary ):
        print "MetaClass is called."
        cls.addedin = 5

print MetaClass

class ComplexClass:
    __metaclass__ = MetaClass

print ComplexClass, dir( ComplexClass )

print ComplexClass, hasattr( ComplexClass, "addedin" ) and ComplexClass.addedin


def function():
    x = 1

    class DynamicClass:
        y = x

    return DynamicClass

    x = 2

print function(), function().y

def strangeClassBehaviour():
    class StrangeClass(object):
        count = 0

        def __new__( cls ):
            print "__new__"

            cls.count += 1
            return object.__new__(cls)

        def __del__( self ):
            print "__del__"

            cls = self.__class__
            cls.count -= 1
            assert cls.count >= 0


    x = StrangeClass()

    return x.count

print "Strange class with __new__ and __del__ overloads", strangeClassBehaviour()

class ClosureLocalizer:
    function = function

    def deco( f ):
        return f

    @deco
    def x():
        pass

print "Class with a name from module level renamed to local", ClosureLocalizer.function

print "Class with decorator"

def classdecorator( cls ):
    print "cls decorator", cls.addedin

    return cls

@classdecorator
class MyClass:
    __metaclass__ = MetaClass

print "Class that updates its locals",

class DictUpdating:
    a = 1

    locals().update( { "b" : 2 } )

    for f in range(6):
        locals()[ "test_%s" % f ] = f

print DictUpdating.b, DictUpdating.test_4

def functionThatOffersClosureToPassThroughClass( x ):
    class Foo:
        global x
        x = 1

        def __call__(self, y):
            return x + y

    return Foo()

print functionThatOffersClosureToPassThroughClass(6)(2),
print x

class NameCollisionClosure:
    def x( self ):
        return x

print NameCollisionClosure, NameCollisionClosure().x()
