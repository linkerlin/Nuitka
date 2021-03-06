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
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional statement, that
would be 'if a: ... else: ...' and there is no 'elif', because that is expressed via
nesting of conditional statements.
"""

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase

# Delayed import into multiple branches is not an issue, pylint: disable=W0404

class ExpressionConditional( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = ( "condition", "expression_yes", "expression_no" )

    def __init__( self, condition, yes_expression, no_expression, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"      : condition,
                "expression_yes" : yes_expression,
                "expression_no"  : no_expression
            },
            source_ref = source_ref
        )

    def getBranches( self ):
        return ( self.getExpressionYes(), self.getExpressionNo() )

    getExpressionYes = ExpressionChildrenHavingBase.childGetter( "expression_yes" )
    getExpressionNo = ExpressionChildrenHavingBase.childGetter( "expression_no" )
    getCondition = ExpressionChildrenHavingBase.childGetter( "condition" )

    def computeExpression( self, constraint_collection ):
        # Children can tell all we need to know, pylint: disable=W0613
        condition = self.getCondition()

        # If the condition raises, we let that escape.
        if condition.willRaiseException( BaseException ):
            return condition, "new_raise", "Conditional expression raises in condition"

        # Decide this based on truth value of condition.
        truth_value = condition.getTruthValue()

        if truth_value is True:
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionYes(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to yes case"
            )
        elif truth_value is False:
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionNo(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to no case"
            )
        else:
            return self, None, None

    def mayHaveSideEffectsBool( self ):
        condition = self.getCondition()

        if condition.mayHaveSideEffectsBool():
            return True

        if self.getExpressionYes().mayHaveSideEffectsBool():
            return True

        if self.getExpressionNo().mayHaveSideEffectsBool():
            return True

        return False

    def mayProvideReference( self ):
        return self.getExpressionYes().mayProvideReference() or \
               self.getExpressionNo().mayProvideReference()


class StatementConditional( StatementChildrenHavingBase ):
    kind = "STATEMENT_CONDITIONAL"

    named_children = ( "condition", "yes_branch", "no_branch" )

    def __init__( self, condition, yes_branch, no_branch, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"  : condition,
                "yes_branch" : yes_branch,
                "no_branch"  : no_branch
            },
            source_ref = source_ref
        )

    getCondition = StatementChildrenHavingBase.childGetter( "condition" )
    getBranchYes = StatementChildrenHavingBase.childGetter( "yes_branch" )
    setBranchYes = StatementChildrenHavingBase.childSetter( "yes_branch" )
    getBranchNo = StatementChildrenHavingBase.childGetter( "no_branch" )
    setBranchNo = StatementChildrenHavingBase.childSetter( "no_branch" )

    def isStatementAborting( self ):
        yes_branch = self.getBranchYes()

        if yes_branch is not None:
            if yes_branch.isStatementAborting():
                no_branch = self.getBranchNo()

                if no_branch is not None:
                    return no_branch.isStatementAborting()
                else:
                    return False
            else:
                return False
        else:
            return False


    def computeStatement( self, constraint_collection ):
        # This is rather complex stuff, pylint: disable=R0912

        # Query the truth value before the expression is evaluated, once it is evaluated
        # in onExpression, it may change.
        condition = self.getCondition()
        truth_value = condition.getTruthValue()

        constraint_collection.onExpression( condition )
        condition = self.getCondition()

        from nuitka.optimizations.ConstraintCollections import ConstraintCollectionBranch

        # TODO: We now know that condition evaluates to true for the yes branch
        # and to not true for no branch

        yes_branch = self.getBranchYes()

        if yes_branch is not None:
            branch_yes_collection = ConstraintCollectionBranch( constraint_collection )

            branch_yes_collection.process( yes_branch )

            # May have just gone away.
            yes_branch = self.getBranchYes()
        else:
            branch_yes_collection = None

        no_branch = self.getBranchNo()

        if no_branch is not None:
            branch_no_collection = ConstraintCollectionBranch( constraint_collection )

            branch_no_collection.process( no_branch )

            # May have just gone away.
            no_branch = self.getBranchNo()
        else:
            branch_no_collection = None


        # Merge into parent constraint collection.
        constraint_collection.mergeBranches( branch_yes_collection, branch_no_collection )

        if yes_branch is not None and no_branch is not None:
            # TODO: Merging should be done by method.
            constraint_collection.variables = constraint_collection.mergeBranchVariables(
                branch_yes_collection.variables,
                branch_no_collection.variables
            )
        elif yes_branch is not None:
            constraint_collection.mergeBranch( branch_yes_collection )
        elif no_branch is not None:
            constraint_collection.mergeBranch( branch_no_collection )
        else:
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            # With both branches eliminated, the condition remains as a side effect.
            result = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = self
            )

            return result, "new_statements", """\
Both branches have no effect, reduced to evaluate condition."""

        if yes_branch is None:
            # Would be eliminated already, if there wasn't any "no" branch either.
            assert no_branch is not None

            from .OperatorNodes import ExpressionOperationNOT

            new_statement = StatementConditional(
                condition = ExpressionOperationNOT(
                    operand    = condition,
                    source_ref = condition.getSourceReference()
                ),
                yes_branch = no_branch,
                no_branch  = None,
                source_ref = self.getSourceReference()
            )

            return new_statement, "new_statements", """\
Empty 'yes' branch for condition was replaced with inverted condition check."""

        # Note: Checking the condition late, so that the surviving branches got processed
        # already. Returning without doing that, will lead to errorneous assumptions.
        if truth_value is not None:
            from .NodeMakingHelpers import wrapStatementWithSideEffects

            if truth_value is True:
                choice = "true"

                new_statement = self.getBranchYes()
            else:
                choice = "false"

                new_statement = self.getBranchNo()

            new_statement = wrapStatementWithSideEffects(
                new_node   = new_statement,
                old_node   = condition,
                allow_none = True # surviving branch may empty
            )

            return new_statement, "new_statements", """\
Condition for branch was predicted to be always %s.""" % choice
        elif condition.willRaiseException( BaseException ):
            from .NodeMakingHelpers import makeStatementExpressionOnlyReplacementNode

            result = makeStatementExpressionOnlyReplacementNode(
                expression = condition,
                node       = self
            )

            return result, "new_raise", """\
Conditional statements already raises implicitely in condition, removing branches"""

        return self, None, None
