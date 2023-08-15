#!/usr/bin/env bash
# shellcheck disable=SC2034

echo "$JAVA_HOME" 


ANTLR_JAR="antlr4.jar"
ANTLR_JAR_URI="https://www.antlr.org/download/antlr-4.9-complete.jar"


GRAMMAR="Solidity"
START_RULE="sourceUnit"
TEST_FILE="test.sol"
ERROR_PATTERN="mismatched|extraneous"

function download_antlr4
{
  if [[ ! -e "$ANTLR_JAR" ]]
  then
    curl -sL "${ANTLR_JAR_URI}" -o "${ANTLR_JAR}" 
  fi
}

echo "Downloading Antlr 4.9..."

download_antlr4

mkdir -p target/

echo "Creating parser"
(
java -jar $ANTLR_JAR $GRAMMAR.g4 -o src/
sleep 1
javac -classpath $ANTLR_JAR src/*.java -d target/
)

echo "Artifacts Generated"
exit 0