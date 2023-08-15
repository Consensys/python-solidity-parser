#!/usr/bin/env bash
set -o errexit

git submodule sync --recursive && git submodule update --init --recursive
git submodule foreach --recursive git clean -ffdx
git submodule update --remote --rebase solidity-antlr4
sleep 1

# Sanity Check that Submodules was successful 
[ ! -f ./solidity-antlr4/scripts/build.sh ] && { echo "Solidity Antlr4 does not exist."; exit 1; }

cp scripts/build.sh solidity-antlr4/setup.sh
bash solidity-antlr4/setup.sh
sleep 1
bash scripts/anltr4.sh

echo "Solidity Antlr4.9 build complete!"

exit 0