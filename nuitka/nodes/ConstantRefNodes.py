#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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
""" Node for constant expressions. Can be any builtin type.

"""

from .NodeBases import NodeBase, CompileTimeConstantExpressionMixin

from nuitka.Constants import (
    getConstantIterationLength,
    isIterableConstant,
    isIndexConstant,
    isNumberConstant,
    isConstant,
    isMutable,
)

# pylint: disable=W0622
from nuitka.__past__ import iterItems, unicode
# pylint: enable=W0622


class ExpressionConstantRef( CompileTimeConstantExpressionMixin, NodeBase ):
    kind = "EXPRESSION_CONSTANT_REF"

    def __init__( self, constant, source_ref ):
        NodeBase.__init__( self, source_ref = source_ref )
        CompileTimeConstantExpressionMixin.__init__( self )

        assert isConstant( constant ), constant

        self.constant = constant

    def __repr__( self ):
        return "<Node %s value %s at %s>" % ( self.kind, self.constant, self.source_ref )

    def makeCloneAt( self, source_ref ):
        return self.__class__( self.constant, source_ref )

    def getDetails( self ):
        return { "value" : repr( self.constant ) }

    def getDetail( self ):
        return repr( self.constant )

    def computeExpression( self, constraint_collection ):
        # No need to check anything, pylint: disable=W0613

        # Cannot compute any further, this is already the best.
        return self, None, None

    def computeExpressionCall( self, call_node, constraint_collection ):
        from .NodeMakingHelpers import makeRaiseExceptionReplacementExpression, wrapExpressionWithSideEffects

        new_node = wrapExpressionWithSideEffects(
            new_node     = makeRaiseExceptionReplacementExpression(
                expression      = self,
                exception_type  = "TypeError",
                exception_value = "'%s' object is not callable" % type( self.constant ).__name__
            ),
            old_node     = call_node,
            side_effects = call_node.extractPreCallSideEffects()
        )

        return new_node, "new_raise", "Predicted call of constant value to exception raise."

    def getCompileTimeConstant( self ):
        return self.constant

    getConstant = getCompileTimeConstant

    def isMutable( self ):
        return isMutable( self.constant )

    def isNumberConstant( self ):
        return isNumberConstant( self.constant )

    def isIndexConstant( self ):
        return isIndexConstant( self.constant )

    def isStringConstant( self ):
        return type( self.constant ) is str

    def isIndexable( self ):
        return self.constant is None or self.isNumberConstant()

    def isKnownToBeIterable( self, count ):
        if isIterableConstant( self.constant ):
            return count is None or getConstantIterationLength( self.constant ) == count
        else:
            return False

    def isKnownToBeIterableAtMin( self, count ):
        length = self.getIterationLength()

        return length is not None and length >= count

    def canPredictIterationValues( self ):
        return self.isKnownToBeIterable( None )

    def getIterationValue( self, count ):
        assert count < len( self.constant )

        return ExpressionConstantRef( self.constant[ count ], self.source_ref )

    def getIterationValues( self ):
        source_ref = self.getSourceReference()

        return tuple(
            ExpressionConstantRef(
                constant   = value,
                source_ref = source_ref
            )
            for value in
            self.constant
        )

    def isMapping( self ):
        return type( self.constant ) is dict

    def isMappingWithConstantStringKeys( self ):
        assert self.isMapping()

        for key in self.constant:
            if type( key ) not in ( str, unicode ):
                return False
        else:
            return True

    def getMappingPairs( self ):
        assert self.isMapping()

        pairs = []

        source_ref = self.getSourceReference()

        for key, value in iterItems( self.constant ):
            pairs.append(
                ExpressionConstantRef(
                    constant   = key,
                    source_ref = source_ref
                ),
                ExpressionConstantRef(
                    constant   = value,
                    source_ref = source_ref
                )
            )

        return pairs

    def getMappingStringKeyPairs( self ):
        assert self.isMapping()

        pairs = []

        source_ref = self.getSourceReference()

        for key, value in iterItems( self.constant ):
            pairs.append(
                (
                    key,
                    ExpressionConstantRef(
                        constant   = value,
                        source_ref = source_ref
                    )
                )
            )

        return pairs


    def isBoolConstant( self ):
        return type( self.constant ) is bool

    def mayHaveSideEffects( self ):
        # Constants have no side effects
        return False

    def extractSideEffects( self ):
        # Constants have no side effects
        return ()

    def mayRaiseException( self, exception_type ):
        # Virtual method, pylint: disable=R0201,W0613

        # Constants won't raise any kind of exception.
        return False

    def mayProvideReference( self ):
        return self.isMutable()

    def getIntegerValue( self ):
        if self.isNumberConstant():
            return int( self.constant )
        else:
            return None

    def getStringValue( self ):
        if self.isStringConstant():
            return self.constant
        else:
            return None

    def getIterationLength( self ):
        if isIterableConstant( self.constant ):
            return getConstantIterationLength( self.constant )
        else:
            return None

    def getStrValue( self ):
        if type( self.constant ) is str:
            return self
        else:
            return ExpressionConstantRef(
                constant   = str( self.constant ),
                source_ref = self.getSourceReference()
            )
