#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pprint
from . import parser

if __name__ == "__main__":
    if not len(sys.argv)>2 or sys.argv[1] not in ("parse","outline"):
        print("\n- missing subcommand or path to solidity file.\n")
        print("#> python -m solidity_parser <subcommand> <solidity file>")
        print("")
        print("\t subcommands:")
        print("\t\t parse   ... print the parsetree for the sourceUnit")
        print("\t\t outline ... print a high level outline of the sourceUnit")
        sys.exit(1)

    node = parser.parse_file(sys.argv[2], loc=False)
    if sys.argv[1]=="parse":
        pprint.pprint(node)
    elif sys.argv[1]=="outline":
        level = 0
        sourceUnitObject = parser.objectify(node)
        print("=== pragmas ===")
        level +=1
        for p in sourceUnitObject.pragmas:
            print(("\t" * level) + "* " + str(p))
        level -=1
        print("=== imports ===")
        level +=1
        for p in sourceUnitObject.imports:
            print(("\t" * level) + "* " + str(p))
        level = 0
        for contract_name, contract_object in sourceUnitObject.contracts.items():
            print("=== contract: " + contract_name)
            level +=1

            print(("\t" * level) + "=== Inherited Contracts: " + ','.join([bc.baseName.namePath for bc in  contract_object._node.baseContracts]))
            ## statevars
            print(("\t" * level) + "=== Enums")
            level += 2
            for name in contract_object.enums.keys():
                print(("\t" * level) + "* " + str(name))
            level -= 2
            ## structs
            print(("\t" * level) + "=== Structs")
            level += 2
            for name in contract_object.structs.keys():
                print(("\t" * level) + "* " + str(name))
            level -= 2
            ## statevars
            print(("\t" * level) + "=== statevars" )
            level +=2
            for name in contract_object.stateVars.keys():
                print(("\t" * level) + "* " + str(name) )
            level -=2
            ## modifiers
            print(("\t" * level) + "=== modifiers")
            level += 2
            for name in contract_object.modifiers.keys():
                print(("\t" * level) + "* " + str(name))
            level -= 2
            ## functions
            print(("\t" * level) + "=== functions")
            level += 2
            for name, funcObj in contract_object.functions.items():
                txtAttribs = []
                if funcObj.visibility:
                    txtAttribs.append(funcObj.visibility)
                if funcObj.stateMutability:
                    txtAttribs.append(funcObj.stateMutability)
                print(("\t" * level) + "* " + str(name) + "\t\t (" + ','.join(txtAttribs)+ ")")
            level -= 2

