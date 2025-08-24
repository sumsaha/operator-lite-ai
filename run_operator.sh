#!/bin/bash
set -e

if [ $# -eq 0 ]; then
  echo "Usage: ./run_operator.sh \"Your instruction here\""
  exit 1
fi

echo "======================================="
echo " Running Operator with natural language "
echo "======================================="

python3 operator.py "$1"
