#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# part of https://github.com/ConsenSys/python-solidity-parser
# derived from https://github.com/federicobond/solidity-parser-antlr/
#


from antlr4 import *
from solidity_parser.solidity_antlr4.SolidityLexer import SolidityLexer
from solidity_parser.solidity_antlr4.SolidityParser import SolidityParser
from solidity_parser.solidity_antlr4.SolidityVisitor import SolidityVisitor


class Node(dict):
    """
    provide a dict interface and object attrib access
    """
    ENABLE_LOC = False
    NONCHILD_KEYS = ("type","name","loc")

    def __init__(self, ctx, **kwargs):
        for k, v in kwargs.items():
            self[k] = v

        if Node.ENABLE_LOC:
            self["loc"] = Node._get_loc(ctx)

    def __getattr__(self, item):
        return self[item]  # raise exception if attribute does not exist

    def __setattr__(self, name, value):
        self[name] = value

    @staticmethod
    def _get_loc(ctx):
        return {
            'start': {
                'line': ctx.start.line,
                'column': ctx.start.column
            },
            'end': {
                'line': ctx.stop.line,
                'column': ctx.stop.column
            }
        }


class AstVisitor(SolidityVisitor):

    def _mapCommasToNulls(self, children):
        if not children or len(children) == 0:
            return []

        values = []
        comma = True

        for el in children:
            if comma:
                if el.getText() == ',':
                    values.append(None)
                else:
                    values.append(el)
                    comma = False
            else:
                if el.getText() != ',':
                    raise Exception('expected comma')

                comma = True

        if comma:
            values.append(None)

        return values

    def _createNode(self, **kwargs):
        ## todo: add loc!
        return Node(**kwargs)

    def visit(self, tree):
        """
        override the default visit to optionally accept a range of children nodes

        :param tree:
        :return:
        """
        if tree is None:
            return None
        elif isinstance(tree, list):
            return self._visit_nodes(tree)
        else:
            return super().visit(tree)

    def _visit_nodes(self, nodes):
        """
        modified version of visitChildren() that returns an array of results

        :param nodes:
        :return:
        """
        allresults = []
        result = self.defaultResult()
        for c in nodes:
            childResult = c.accept(self)
            result = self.aggregateResult(result, childResult)
            allresults.append(result)
        return allresults

    # ********************************************************

    def visitSourceUnit(self, ctx):
        return Node(ctx=ctx,
                    type="SourceUnit",
                    children=self.visit(ctx.children[:-1]))  # skip EOF

    def visitEnumDefinition(self, ctx):
        return Node(ctx=ctx,
                    type="EnumDefinition",
                    name=ctx.identifier().getText(),
                    members=self.visit(ctx.enumValue()))

    def visitEnumValue(self, ctx):
        return Node(ctx=ctx,
                    type="EnumValue",
                    name=ctx.identifier().getText())

    def visitTypeDefinition(self, ctx):
        return Node(ctx=ctx,
                    type="TypeDefinition",
                    typeKeyword=ctx.TypeKeyword().getText(),
                    elementaryTypeName=self.visit(ctx.elementaryTypeName()))


    def visitCustomErrorDefinition(self, ctx):
        return Node(ctx=ctx,
                    type="CustomErrorDefinition",
                    name=self.visit(ctx.identifier()),
                    parameterList=self.visit(ctx.parameterList()))

    def visitFileLevelConstant(self, ctx):
        return Node(ctx=ctx,
                    type="FileLevelConstant",
                    name=self.visit(ctx.identifier()),
                    typeName=self.visit(ctx.typeName()),
                    ConstantKeyword=self.visit(ctx.ConstantKeyword()))


    def visitUsingForDeclaration(self, ctx: SolidityParser.UsingForDeclarationContext):
        typename = None
        if ctx.getChild(3) != '*':
            typename = self.visit(ctx.getChild(3))

        return Node(ctx=ctx,
                    type="UsingForDeclaration",
                    typeName=typename,
                    libraryName=ctx.identifier().getText())

    def visitInheritanceSpecifier(self, ctx: SolidityParser.InheritanceSpecifierContext):
        return Node(ctx=ctx,
                    type="InheritanceSpecifier",
                    baseName=self.visit(ctx.userDefinedTypeName()),
                    arguments=self.visit(ctx.expressionList()))

    def visitContractPart(self, ctx: SolidityParser.ContractPartContext):
        return self.visit(ctx.children[0])


    def visitFunctionDefinition(self, ctx: SolidityParser.FunctionDefinitionContext):
        isConstructor = isFallback =isReceive = False

        fd = ctx.functionDescriptor()
        if fd.ConstructorKeyword():
            name = fd.ConstructorKeyword().getText()
            isConstructor = True
        elif fd.FallbackKeyword():
            name = fd.FallbackKeyword().getText()
            isFallback = True
        elif fd.ReceiveKeyword():
            name = fd.ReceiveKeyword().getText()
            isReceive = True
        elif fd.identifier():
            name = fd.identifier().getText()
        else:
            name = ctx.getText()

        parameters = self.visit(ctx.parameterList())
        returnParameters = self.visit(ctx.returnParameters()) if ctx.returnParameters() else []
        block = self.visit(ctx.block()) if ctx.block() else []
        modifiers = [self.visit(i) for i in ctx.modifierList().modifierInvocation()]

        if ctx.modifierList().ExternalKeyword(0):
            visibility = "external"
        elif ctx.modifierList().InternalKeyword(0):
            visibility = "internal"
        elif ctx.modifierList().PublicKeyword(0):
            visibility = "public"
        elif ctx.modifierList().PrivateKeyword(0):
            visibility = "private"
        else:
            visibility = 'default'

        if ctx.modifierList().stateMutability(0):
            stateMutability = ctx.modifierList().stateMutability(0).getText()
        else:
            stateMutability = None

        return Node(ctx=ctx,
                    type="FunctionDefinition",
                    name=name,
                    parameters=parameters,
                    returnParameters=returnParameters,
                    body=block,
                    visibility=visibility,
                    modifiers=modifiers,
                    isConstructor=isConstructor,
                    isFallback=isFallback,
                    isReceive=isReceive,
                    stateMutability=stateMutability)

    def visitReturnParameters(self, ctx: SolidityParser.ReturnParametersContext):
        return self.visit(ctx.parameterList())

    def visitParameterList(self, ctx: SolidityParser.ParameterListContext):
        parameters = [self.visit(p) for p in ctx.parameter()]
        return Node(ctx=ctx,
                    type="ParameterList",
                    parameters=parameters)

    def visitParameter(self, ctx: SolidityParser.ParameterContext):

        storageLocation = ctx.storageLocation().getText() if ctx.storageLocation() else None
        name = ctx.identifier().getText() if ctx.identifier() else None

        return Node(ctx=ctx,
                    type="Parameter",
                    typeName=self.visit(ctx.typeName()),
                    name=name,
                    storageLocation=storageLocation,
                    isStateVar=False,
                    isIndexed=False
                    )

    def visitModifierInvocation(self, ctx):
        exprList = ctx.expressionList()

        if exprList is not None:
            args = self.visit(exprList.expression())
        else:
            args = []

        return Node(ctx=ctx,
                    type='ModifierInvocation',
                    name=ctx.identifier().getText(),
                    arguments=args)

    def visitElementaryTypeNameExpression(self, ctx):
        return Node(ctx=ctx,
                    type='ElementaryTypeNameExpression',
                    typeName=self.visit(ctx.elementaryTypeName()))

    def visitTypeName(self, ctx):
        if len(ctx.children) > 2:
            length = None
            if len(ctx.children) == 4:
                length = self.visit(ctx.getChild(2))

            return Node(ctx=ctx,
                        type='ArrayTypeName',
                        baseTypeName=self.visit(ctx.getChild(0)),
                        length=length)

        if len(ctx.children) == 2:
            return Node(ctx=ctx,
                        type='ElementaryTypeName',
                        name=ctx.getChild(0).getText(),
                        stateMutability=ctx.getChild(1).getText())

        return self.visit(ctx.getChild(0))

    def visitFunctionTypeName(self, ctx):
        parameterTypes = [self.visit(p) for p in ctx.functionTypeParameterList(0).functionTypeParameter()]
        returnTypes = []

        if ctx.functionTypeParameterList(1):
            returnTypes = [self.visit(p) for p in ctx.functionTypeParameterList(1).functionTypeParameter()]

        visibility = 'default'
        if ctx.InternalKeyword(0):
            visibility = 'internal'
        elif ctx.ExternalKeyword(0):
            visibility = 'external'

        stateMutability = None
        if ctx.stateMutability(0):
            stateMutability = ctx.stateMutability(0).getText()

        return Node(ctx=ctx,
                    type='FunctionTypeName',
                    parameterTypes=parameterTypes,
                    returnTypes=returnTypes,
                    visibility=visibility,
                    stateMutability=stateMutability)

    def visitFunctionCall(self, ctx):
        args = []
        names = []

        ctxArgs = ctx.functionCallArguments()

        if ctxArgs.expressionList():
            args = [self.visit(a) for a in ctxArgs.expressionList().expression()]

        elif ctxArgs.nameValueList():
            for nameValue in ctxArgs.nameValueList().nameValue():
                args.append(self.visit(nameValue.expression()))
                names.append(nameValue.identifier().getText())

        return Node(ctx=ctx,
                    type='FunctionCall',
                    expression=self.visit(ctx.expression()),
                    arguments=args,
                    names=names)

    def visitEmitStatement(self, ctx):
        return Node(ctx=ctx,
                    type='EmitStatement',
                    eventCall=self.visit(ctx.getChild(1)))

    def visitThrowStatement(self, ctx):
        return Node(ctx=ctx,
                    type='ThrowStatement')

    def visitStructDefinition(self, ctx):
        return Node(ctx=ctx,
                    type='StructDefinition',
                    name=ctx.identifier().getText(),
                    members=self.visit(ctx.variableDeclaration()))

    def visitVariableDeclaration(self, ctx):
        storageLocation = None

        if ctx.storageLocation():
            storageLocation = ctx.storageLocation().getText()

        return Node(ctx=ctx,
                    type='VariableDeclaration',
                    typeName=self.visit(ctx.typeName()),
                    name=ctx.identifier().getText(),
                    storageLocation=storageLocation)

    def visitEventParameter(self, ctx):
        storageLocation = None

        # TODO: fixme

        # if (ctx.storageLocation(0)):
        #    storageLocation = ctx.storageLocation(0).getText()

        return Node(ctx=ctx,
                    type='VariableDeclaration',
                    typeName=self.visit(ctx.typeName()),
                    name=ctx.identifier().getText(),
                    storageLocation=storageLocation,
                    isStateVar=False,
                    isIndexed=not not ctx.IndexedKeyword())

    def visitFunctionTypeParameter(self, ctx):
        storageLocation = None

        if ctx.storageLocation():
            storageLocation = ctx.storageLocation().getText()

        return Node(ctx=ctx,
                    type='VariableDeclaration',
                    typeName=self.visit(ctx.typeName()),
                    name=None,
                    storageLocation=storageLocation,
                    isStateVar=False,
                    isIndexed=False)

    def visitWhileStatement(self, ctx):
        return Node(ctx=ctx,
                    type='WhileStatement',
                    condition=self.visit(ctx.expression()),
                    body=self.visit(ctx.statement()))

    def visitDoWhileStatement(self, ctx):
        return Node(ctx=ctx,
                    type='DoWhileStatement',
                    condition=self.visit(ctx.expression()),
                    body=self.visit(ctx.statement()))

    def visitIfStatement(self, ctx):

        TrueBody = self.visit(ctx.statement(0))

        FalseBody = None
        if len(ctx.statement()) > 1:
            FalseBody = self.visit(ctx.statement(1))

        return Node(ctx=ctx,
                    type='IfStatement',
                    condition=self.visit(ctx.expression()),
                    TrueBody=TrueBody,
                    FalseBody=FalseBody)

    def visitTryStatement(self, ctx):
        return Node(ctx=ctx,
                    type='TryStatement',
                    expression=self.visit(ctx.expression()),
                    block=self.visit(ctx.block()),
                    returnParameters=self.visit(ctx.returnParameters()),
                    catchClause=self.visit(ctx.catchClause()))

    def visitCatchClause(self, ctx):
        return Node(ctx=ctx,
                    type='CatchClause',
                    identifier=self.visit(ctx.identifier()),
                    parameterList=self.visit(ctx.parameterList()),
                    block=self.visit(ctx.block()))

    def visitUserDefinedTypeName(self, ctx):
        return Node(ctx=ctx,
                    type='UserDefinedTypeName',
                    namePath=ctx.getText())

    def visitElementaryTypeName(self, ctx):
        return Node(ctx=ctx,
                    type='ElementaryTypeName',
                    name=ctx.getText())

    def visitBlock(self, ctx):
        return Node(ctx=ctx,
                    type='Block',
                    statements=self.visit(ctx.statement()))

    def visitExpressionStatement(self, ctx):
        return Node(ctx=ctx,
                    type='ExpressionStatement',
                    expression=self.visit(ctx.expression()))

    def visitNumberLiteral(self, ctx):
        number = ctx.getChild(0).getText()
        subdenomination = None

        if len(ctx.children) == 2:
            subdenomination = ctx.getChild(1).getText()

        return Node(ctx=ctx,
                    type='NumberLiteral',
                    number=number,
                    subdenomination=subdenomination)

    def visitMapping(self, ctx):
        return Node(ctx=ctx,
                    type='Mapping',
                    keyType=self.visit(ctx.mappingKey()),
                    valueType=self.visit(ctx.typeName()))

    def visitModifierDefinition(self, ctx):
        parameters = []

        if ctx.parameterList():
            parameters = self.visit(ctx.parameterList())

        return Node(ctx=ctx,
                    type='ModifierDefinition',
                    name=ctx.identifier().getText(),
                    parameters=parameters,
                    body=self.visit(ctx.block()))

    def visitStatement(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitSimpleStatement(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitUncheckedStatement(self, ctx):
        return Node(ctx=ctx,
                    type='UncheckedStatement',
                    body=self.visit(ctx.block())) 

    def visitRevertStatement(self, ctx):
        return Node(ctx=ctx,
                    type='RevertStatement',
                    functionCall=self.visit(ctx.functionCall()))

    def visitExpression(self, ctx):

        children_length = len(ctx.children)
        if children_length == 1:
            return self.visit(ctx.getChild(0))

        elif children_length == 2:
            op = ctx.getChild(0).getText()
            if op == 'new':
                return Node(ctx=ctx,
                            type='NewExpression',
                            typeName=self.visit(ctx.typeName()))

            if op in ['+', '-', '++', '--', '!', '~', 'after', 'delete']:
                return Node(ctx=ctx,
                            type='UnaryOperation',
                            operator=op,
                            subExpression=self.visit(ctx.getChild(1)),
                            isPrefix=True)

            op = ctx.getChild(1).getText()
            if op in ['++', '--']:
                return Node(ctx=ctx,
                            type='UnaryOperation',
                            operator=op,
                            subExpression=self.visit(ctx.getChild(0)),
                            isPrefix=False)
        elif children_length == 3:
            if ctx.getChild(0).getText() == '(' and ctx.getChild(2).getText() == ')':
                return Node(ctx=ctx,
                            type='TupleExpression',
                            components=[self.visit(ctx.getChild(1))],
                            isArray=False)

            op = ctx.getChild(1).getText()

            if op == ',':
                return Node(ctx=ctx,
                            type='TupleExpression',
                            components=[
                                self.visit(ctx.getChild(0)),
                                self.visit(ctx.getChild(2))
                            ],
                            isArray=False)


            elif op == '.':
                expression = self.visit(ctx.getChild(0))
                memberName = ctx.getChild(2).getText()
                return Node(ctx=ctx,
                            type='MemberAccess',
                            expression=expression,
                            memberName=memberName)

            binOps = [
                '+',
                '-',
                '*',
                '/',
                '**',
                '%',
                '<<',
                '>>',
                '&&',
                '||',
                '&',
                '|',
                '^',
                '<',
                '>',
                '<=',
                '>=',
                '==',
                '!=',
                '=',
                '|=',
                '^=',
                '&=',
                '<<=',
                '>>=',
                '+=',
                '-=',
                '*=',
                '/=',
                '%='
            ]

            if op in binOps:
                return Node(ctx=ctx,
                            type='BinaryOperation',
                            operator=op,
                            left=self.visit(ctx.getChild(0)),
                            right=self.visit(ctx.getChild(2)))

        elif children_length == 4:

            if ctx.getChild(1).getText() == '(' and ctx.getChild(3).getText() == ')':
                args = []
                names = []

                ctxArgs = ctx.functionCallArguments()
                if ctxArgs.expressionList():
                    args = [self.visit(a) for a in ctxArgs.expressionList().expression()]
                elif ctxArgs.nameValueList():
                    for nameValue in ctxArgs.nameValueList().nameValue():
                        args.append(self.visit(nameValue.expression()))
                        names.append(nameValue.identifier().getText())

                return Node(ctx=ctx,
                            type='FunctionCall',
                            expression=self.visit(ctx.getChild(0)),
                            arguments=args,
                            names=names)

            if ctx.getChild(1).getText() == '[' and ctx.getChild(3).getText() == ']':
                return Node(ctx=ctx,
                            type='IndexAccess',
                            base=self.visit(ctx.getChild(0)),
                            index=self.visit(ctx.getChild(2)))

        elif children_length == 5:
            # ternary
            if ctx.getChild(1).getText() == '?' and ctx.getChild(3).getText() == ':':
                return Node(ctx=ctx,
                            type='Conditional',
                            condition=self.visit(ctx.getChild(0)),
                            TrueExpression=self.visit(ctx.getChild(2)),
                            FalseExpression=self.visit(ctx.getChild(4)))

        raise Exception("unrecognized expression")

    def visitStateVariableDeclaration(self, ctx):
        type = self.visit(ctx.typeName())
        iden = ctx.identifier()
        name = iden.getText()

        expression = None

        if ctx.expression():
            expression = self.visit(ctx.expression())

        visibility = 'default'

        if ctx.InternalKeyword(0):
            visibility = 'internal'
        elif ctx.PublicKeyword(0):
            visibility = 'public'
        elif ctx.PrivateKeyword(0):
            visibility = 'private'

        isDeclaredConst = False
        if ctx.ConstantKeyword(0):
            isDeclaredConst = True

        decl = self._createNode(
            ctx=ctx,
            type='VariableDeclaration',
            typeName=type,
            name=name,
            expression=expression,
            visibility=visibility,
            isStateVar=True,
            isDeclaredConst=isDeclaredConst,
            isIndexed=False)

        return Node(ctx=ctx,
                    type='StateVariableDeclaration',
                    variables=[decl],
                    initialValue=expression)

    def visitForStatement(self, ctx):
        conditionExpression = self.visit(ctx.expressionStatement()) if ctx.expressionStatement() else None

        if conditionExpression:
            conditionExpression = conditionExpression.expression

        return Node(ctx=ctx,
                    type='ForStatement',
                    initExpression=self.visit(ctx.simpleStatement()),
                    conditionExpression=conditionExpression,
                    loopExpression=Node(ctx=ctx,
                        type='ExpressionStatement',
                        expression=self.visit(ctx.expression())),
                    body=self.visit(ctx.statement())
                    )

    def visitPrimaryExpression(self, ctx):
        if ctx.BooleanLiteral():
            return Node(ctx=ctx,
                        type='BooleanLiteral',
                        value=ctx.BooleanLiteral().getText() == 'true')

        if ctx.hexLiteral():
            return Node(ctx=ctx,
                        type='hexLiteral',
                        value=ctx.hexLiteral().getText())

        if ctx.stringLiteral():
            text = ctx.getText()
            return Node(ctx=ctx,
                        type='stringLiteral',
                        value=text[1: len(text) - 1])

        if len(ctx.children) == 3 and ctx.getChild(1).getText() == '[' and ctx.getChild(2).getText() == ']':
            node = self.visit(ctx.getChild(0))
            if node.type == 'Identifier':
                node = Node(ctx=ctx,
                            type='UserDefinedTypeName',
                            namePath=node.name)
            else:
                node = Node(ctx=ctx,
                            type='ElementaryTypeName',
                            name=ctx.getChild(0).getText())

            return Node(ctx=ctx,
                        type='ArrayTypeName',
                        baseTypeName=node,
                        length=None)

        return self.visit(ctx.getChild(0))

    def visitIdentifier(self, ctx):
        return Node(ctx=ctx,
                    type="Identifier",
                    name=ctx.getText())

    def visitTupleExpression(self, ctx):
        children = ctx.children[1:-1]
        components = [None if e is None else self.visit(e) for e in self._mapCommasToNulls(children)]

        return Node(ctx=ctx,
                    type='TupleExpression',
                    components=components,
                    isArray=ctx.getChild(0).getText() == '[')

    def visitIdentifierList(self, ctx: SolidityParser.IdentifierListContext):
        children = ctx.children[1:-1]

        result = []
        for iden in self._mapCommasToNulls(children):
            if iden == None:
                result.append(None)
            else:
                result.append(self._createNode(ctx=ctx,
                                               type="VariableDeclaration",
                                               name=iden.getText(),
                                               isStateVar=False,
                                               isIndexed=False,
                                               iden=iden))

        return result

    def visitVariableDeclarationList(self, ctx: SolidityParser.VariableDeclarationListContext):
        result = []
        for decl in self._mapCommasToNulls(ctx.children):
            if decl == None:
                return None

            result.append(self._createNode(ctx=ctx,
                                           type='VariableDeclaration',
                                           name=decl.identifier().getText(),
                                           typeName=self.visit(decl.typeName()),
                                           isStateVar=False,
                                           isIndexed=False,
                                           decl=decl))

        return result

    def visitVariableDeclarationStatement(self, ctx):

        if ctx.variableDeclaration():
            variables = [self.visit(ctx.variableDeclaration())]
        elif ctx.identifierList():
            variables = self.visit(ctx.identifierList())
        elif ctx.variableDeclarationList():
            variables = self.visit(ctx.variableDeclarationList())

        initialValue = None

        if ctx.expression():
            initialValue = self.visit(ctx.expression())

        return Node(ctx=ctx,
                    type='VariableDeclarationStatement',
                    variables=variables,
                    initialValue=initialValue)

    def visitEventDefinition(self, ctx):
        return Node(ctx=ctx,
                    type='EventDefinition',
                    name=ctx.identifier().getText(),
                    parameters=self.visit(ctx.eventParameterList()),
                    isAnonymous=not not ctx.AnonymousKeyword())

    def visitEventParameterList(self, ctx):
        parameters = []
        for paramCtx in ctx.eventParameter():
            type = self.visit(paramCtx.typeName())
            name = None
            if paramCtx.identifier():
                name = paramCtx.identifier().getText()

            parameters.append(self._createNode(ctx=ctx,
                type='VariableDeclaration',
                typeName=type,
                name=name,
                isStateVar=False,
                isIndexed=not not paramCtx.IndexedKeyword()))

        return Node(ctx=ctx,
                    type='ParameterList',
                    parameters=parameters)

    def visitInlineAssemblyStatement(self, ctx):
        language = None

        if ctx.StringLiteralFragment():
            language = ctx.StringLiteralFragment().getText()
            language = language[1: len(language) - 1]

        return Node(ctx=ctx,
                    type='InLineAssemblyStatement',
                    language=language,
                    body=self.visit(ctx.assemblyBlock()))

    def visitAssemblyBlock(self, ctx):
        operations = [self.visit(it) for it in ctx.assemblyItem()]

        return Node(ctx=ctx,
                    type='AssemblyBlock',
                    operations=operations)

    def visitAssemblyItem(self, ctx):

        if ctx.hexLiteral():
            return Node(ctx=ctx,
                        type='HexLiteral',
                        value=ctx.hexLiteral().getText())

        if ctx.stringLiteral():
            text = ctx.stringLiteral().getText()
            return Node(ctx=ctx,
                        type='StringLiteral',
                        value=text[1: len(text) - 1])

        if ctx.BreakKeyword():
            return Node(ctx=ctx,
                        type='Break')

        if ctx.ContinueKeyword():
            return Node(ctx=ctx,
                        type='Continue')

        return self.visit(ctx.getChild(0))

    def visitAssemblyExpression(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitAssemblyMember(self, ctx):
        return Node(ctx=ctx,
                    type='AssemblyMember',
                    name=ctx.identifier().getText())

    def visitAssemblyCall(self, ctx):
        functionName = ctx.getChild(0).getText()
        args = [self.visit(arg) for arg in ctx.assemblyExpression()]

        return Node(ctx=ctx,
                    type='AssemblyExpression',
                    functionName=functionName,
                    arguments=args)

    def visitAssemblyLiteral(self, ctx):

        if ctx.stringLiteral():
            text = ctx.getText()
            return Node(ctx=ctx,
                        type='StringLiteral',
                        value=text[1: len(text) - 1])

        if ctx.DecimalNumber():
            return Node(ctx=ctx,
                        type='DecimalNumber',
                        value=ctx.getText())

        if ctx.HexNumber():
            return Node(ctx=ctx,
                        type='HexNumber',
                        value=ctx.getText())

        if ctx.hexLiteral():
            return Node(ctx=ctx,
                        type='HexLiteral',
                        value=ctx.getText())

    def visitAssemblySwitch(self, ctx):
        return Node(ctx=ctx,
                    type='AssemblySwitch',
                    expression=self.visit(ctx.assemblyExpression()),
                    cases=[self.visit(c) for c in ctx.assemblyCase()])

    def visitAssemblyCase(self, ctx):
        value = None

        if ctx.getChild(0).getText() == 'case':
            value = self.visit(ctx.assemblyLiteral())

        if value != None:
            node = Node(ctx=ctx,
                        type="AssemblyCase",
                        block=self.visit(ctx.assemblyBlock()),
                        value=value)
        else:
            node = Node(ctx=ctx,
                        type="AssemblyCase",
                        block=self.visit(ctx.assemblyBlock()),
                        default=True)

        return node

    def visitAssemblyLocalDefinition(self, ctx):
        names = ctx.assemblyIdentifierOrList()

        if names.identifier():
            names = [self.visit(names.identifier())]
        else:
            names = self.visit(names.assemblyIdentifierList().identifier())

        return Node(ctx=ctx,
                    type='AssemblyLocalDefinition',
                    names=names,
                    expression=self.visit(ctx.assemblyExpression()))

    def visitAssemblyFunctionDefinition(self, ctx):
        args = ctx.assemblyIdentifierList().identifier()
        returnArgs = ctx.assemblyFunctionReturns().assemblyIdentifierList().identifier()

        return Node(ctx=ctx,
                    type='AssemblyFunctionDefinition',
                    name=ctx.identifier().getText(),
                    arguments=self.visit(args),
                    returnArguments=self.visit(returnArgs),
                    body=self.visit(ctx.assemblyBlock()))

    def visitAssemblyAssignment(self, ctx):
        names = ctx.assemblyIdentifierOrList()

        if names.identifier():
            names = [self.visit(names.identifier())]
        else:
            names = self.visit(names.assemblyIdentifierList().identifier())

        return Node(ctx=ctx,
                    type='AssemblyAssignment',
                    names=names,
                    expression=self.visit(ctx.assemblyExpression()))

    def visitLabelDefinition(self, ctx):
        return Node(ctx=ctx,
                    type='LabelDefinition',
                    name=ctx.identifier().getText())

    def visitAssemblyStackAssignment(self, ctx):
        return Node(ctx=ctx,
                    type='AssemblyStackAssignment',
                    name=ctx.identifier().getText())

    def visitAssemblyFor(self, ctx):
        return Node(ctx=ctx,
                    type='AssemblyFor',
                    pre=self.visit(ctx.getChild(1)),
                    condition=self.visit(ctx.getChild(2)),
                    post=self.visit(ctx.getChild(3)),
                    body=self.visit(ctx.getChild(4)))

    def visitAssemblyIf(self, ctx):
        return Node(ctx=ctx,
                    type='AssemblyIf',
                    condition=self.visit(ctx.assemblyExpression()),
                    body=self.visit(ctx.assemblyBlock()))

    ### /***************************************************

    def visitPragmaDirective(self, ctx):
        return Node(ctx=ctx,
                    type="PragmaDirective",
                    name=ctx.pragmaName().getText(),
                    value=ctx.pragmaValue().getText())

    def visitImportDirective(self, ctx):
        symbol_aliases = {}
        unit_alias = None

        if len(ctx.importDeclaration()) > 0:
            for item in ctx.importDeclaration():

                try:
                    alias = item.identifier(1).getText()
                except:
                    alias = None
                symbol_aliases[item.identifier(0).getText()] = alias

        elif len(ctx.children) == 7:
            unit_alias = ctx.getChild(3).getText()

        elif len(ctx.children) == 5:
            unit_alias = ctx.getChild(3).getText()

        return Node(ctx=ctx,
                    type="ImportDirective",
                    path=ctx.importPath().getText().strip('"'),
                    symbolAliases=symbol_aliases,
                    unitAlias=unit_alias
                    )

    def visitContractDefinition(self, ctx):
        self._currentContract = ctx.identifier().getText()
        return Node(ctx=ctx,
                    type="ContractDefinition",
                    name=ctx.identifier().getText(),
                    baseContracts=self.visit(ctx.inheritanceSpecifier()),
                    subNodes=self.visit(ctx.contractPart()),
                    kind=ctx.getChild(0).getText())

    def visitUserDefinedTypename(self, ctx):
        return Node(ctx=ctx,
                    type="UserDefinedTypename",
                    name=ctx.getText())

    def visitReturnStatement(self, ctx):
        return self.visit(ctx.expression())

    def visitTerminal(self, ctx):
        return ctx.getText()


def parse(text, start="sourceUnit", loc=False, strict=False):
    from antlr4.InputStream import InputStream
    from antlr4 import FileStream, CommonTokenStream

    input_stream = InputStream(text)

    lexer = SolidityLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = SolidityParser(token_stream)
    ast = AstVisitor()

    Node.ENABLE_LOC = loc

    return ast.visit(getattr(parser, start)())


def parse_file(path, start="sourceUnit", loc=False, strict=False):
    with open(path, 'r', encoding="utf-8") as f:
        return parse(f.read(), start=start, loc=loc, strict=strict)


def visit(node, callback_object):
    """

    Walks the AST produced by parse/parse_file and calls callback_object.visit<Node.type>

    :param node: ASTNode returned from parse()
    :param callback: an object implementing the visitor pattern
    :return:
    """

    if node is None or not isinstance(node, Node):
        return node

    # call callback if it is available
    if hasattr(callback_object, "visit"+node.type):
        getattr(callback_object, "visit"+node.type)(node)

    for k,v in node.items():
        if k in node.NONCHILD_KEYS:
            # skip non child items
            continue

        # item is array?
        if isinstance(v, list):
            [visit(child, callback_object) for child in v]
        else:
            visit(v, callback_object)


def objectify(start_node):
    """
    Create an OOP like structure from the tree for easy access of most common information

    sourceUnit
       .pragmas []
       .imports []
       .contracts { name: contract}
           .statevars
           .enums
           .structs
           .functions
           .modifiers
           .

    :param tree:
    :return:
    """

    current_contract = None
    current_function = None

    class ObjectifyContractVisitor(object):

        def __init__(self, node):
            self._node = node
            self.name = node.name

            self.dependencies = []
            self.stateVars = {}
            self.names = {}
            self.enums = {}
            self.structs = {}
            self.mappings = {}
            self.events = {}
            self.modifiers = {}
            self.functions = {}
            self.constructor = None
            self.inherited_names = {}


        def visitEnumDefinition(self, _node):
            self.enums[_node.name]=_node
            self.names[_node.name]=_node

        def visitStructDefinition(self, _node):
            self.structs[_node.name]=_node
            self.names[_node.name]=_node

        def visitStateVariableDeclaration(self, _node):

            class VarDecVisitor(object):

                def __init__(self, current_contract):
                    self._current_contract = current_contract

                def visitVariableDeclaration(self, __node):
                    self._current_contract.stateVars[__node.name] = __node
                    self._current_contract.names[__node.name] = __node

            visit(_node, VarDecVisitor(self))

        def visitEventDefinition(self, _node):

            class EventFunctionVisitor(object):
                def __init__(self, node):
                    self.arguments = {}
                    self.declarations = {}
                    self._node = node

                def visitVariableDeclaration(self, __node):
                    self.arguments[__node.name] = __node
                    self.declarations[__node.name] = __node

            current_function = EventFunctionVisitor(_node)
            visit(_node, current_function)
            self.names[_node.name] = current_function
            self.events[_node.name] = current_function


        def visitFunctionDefinition(self, _node, _definition_type=None):

            class FunctionObject(object):

                def __init__(self, node):
                    self._node = node
                    if(node.type=="FunctionDefinition"):
                        self.visibility = node.visibility
                        self.stateMutability = node.stateMutability
                        self.isConstructor = node.isConstructor
                        self.isFallback = node.isFallback
                        self.isReceive = node.isReceive
                    self.arguments = {}
                    self.returns = {}
                    self.declarations = {}
                    self.identifiers = []
                    
                    

            class FunctionArgumentVisitor(object):

                def __init__(self):
                    self.parameters = {}

                def visitParameter(self, __node):
                    self.parameters[__node.name] = __node

            class VarDecVisitor(object):

                def __init__(self):
                    self.variable_declarations = {}

                def visitVariableDeclaration(self, __node):
                    self.variable_declarations[__node.name] = __node

            class IdentifierDecVisitor(object):

                def __init__(self):
                    self.idents = []

                def visitIdentifier(self, __node):
                    self.idents.append(__node)

                def visitAssemblyCall(self, __node):
                    self.idents.append(__node)

            current_function = FunctionObject(_node)
            self.names[_node.name] = current_function
            if _definition_type=="ModifierDefinition":
                self.modifiers[_node.name] = current_function
            else:
                self.functions[_node.name] = current_function
                if current_function.isConstructor:
                    self.constructor = current_function

            ## get parameters
            funcargvisitor = FunctionArgumentVisitor()
            visit(_node.parameters, funcargvisitor)
            current_function.arguments = funcargvisitor.parameters
            current_function.declarations.update(current_function.arguments)


            ## get returnParams
            if _node.get("returnParameters"):
                # because modifiers dont
                funcargvisitor = FunctionArgumentVisitor()
                visit(_node.returnParameters, funcargvisitor)
                current_function.returns = funcargvisitor.parameters
                current_function.declarations.update(current_function.returns)


            ## get vardecs in body
            vardecs = VarDecVisitor()
            visit(_node.body, vardecs)
            current_function.declarations.update(vardecs.variable_declarations)

            ## get all identifiers
            idents = IdentifierDecVisitor()
            visit(_node, idents)
            current_function.identifiers = idents

        def visitModifierDefinition(self, _node):
            return self.visitFunctionDefinition(_node, "ModifierDefinition")


    class ObjectifySourceUnitVisitor(object):

        def __init__(self, node):
            self._node = node
            self.imports = []
            self.pragmas = []
            self.contracts = {}

            self._current_contract = None

        def visitPragmaDirective(self, node):
            self.pragmas.append(node)

        def visitImportDirective(self, node):
            self.imports.append(node)

        def visitContractDefinition(self, node):
            self.contracts[node.name] = ObjectifyContractVisitor(node)
            self._current_contract = self.contracts[node.name]

            # subparse the contracts //slightly inefficient but more readable :)
            visit(node, self.contracts[node.name])

    objectified_source_unit = ObjectifySourceUnitVisitor(start_node)
    visit(start_node, objectified_source_unit)
    return objectified_source_unit
