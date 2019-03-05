# python-solidity-parser
A Solidity parser for Python built on top of a robust ANTLR4 grammar

**ⓘ** This is a **python3** port of the [javascript antlr parser](https://github.com/federicobond/solidity-parser-antlr) maintained by [@federicobond](https://github.com/federicobond/). Interfaces are intentionally following the javascript impelementation and therefore not pep8 compliant.

## HowTo

```python

from solidity_parser_antlr import parser
import pprint

node = parser.parse_file(sys.argv[1])
pprint.pprint(node)
```
