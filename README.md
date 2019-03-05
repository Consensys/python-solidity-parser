# python-solidity-parser
A Solidity parser for Python built on top of a robust ANTLR4 grammar

**ⓘ** This is a **python3** port of the [javascript antlr parser](https://github.com/federicobond/solidity-parser-antlr) maintained by [@federicobond](https://github.com/federicobond/). Interfaces are intentionally following the javascript impelementation and therefore not pep8 compliant.

## HowTo

```python

from solidity_parser_antlr import parser
import pprint

sourceUnit = parser.parse_file(sys.argv[1])
pprint.pprint(sourceUnit)
```

output:
````
{'type': 'SourceUnit',
 'children': [{'type': 'PragmaDirective',
               'name': 'solidity',
               'value': '^0.4.22'},
              {'type': 'ContractDefinition'},
               'baseContracts': [],
               'kind': 'contract',
               'name': 'SimpleAuction',
               'subNodes': [{'initialValue': None,
                             'type': 'StateVariableDeclaration',
                             'variables': [{'expression': None,
                                            'isDeclaredConst': False,
                                            'isIndexed': False,
                                            'isStateVar': True,
                                            'name': 'beneficiary',
                                            'type': 'VariableDeclaration',
                                            'typeName': {'name': 'address',
                                                         'type': 'ElementaryTypeName'},
                                            'visibility': 'public'}]},
...
````

### Nodes

parse nodes can be accessed like dictionaries or object attributes. Nodes always carry a `type` field to denote the type of information provided. The first node is of type `sourceUnit`.




## Generate the parser

Update the grammar in `./solidity-antlr4/Solidity.g4` and the parser generator script to overwrite the autogenrated parser files in `solidity_parser_antlr/solidity_antlr4`.
```
#> bash script/antlr4.sh
```
