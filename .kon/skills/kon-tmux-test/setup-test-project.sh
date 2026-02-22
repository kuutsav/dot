#!/bin/bash

# Setup script for kon e2e testing
# Creates a deterministic test project structure at /tmp/kon-test-project

TEST_DIR="/tmp/kon-test-project"

# Cleanup and recreate test project
rm -rf $TEST_DIR
mkdir -p $TEST_DIR
cd $TEST_DIR

# Create deterministic test files
echo "# Test Project" > README.md
echo '{"name": "test", "version": "1.0.0"}' > config.json
echo "Todo:
- Read config.json
- Calculate sum" > notes.txt
echo 'def add(a, b): return a + b
def multiply(a, b): return a * b
result = multiply(5, 3)
print(f"5 * 3 = {result}")' > utils.py
echo 'DATA = ["item1", "item2", "item3"]
for item in DATA:
    print(item)' > data.py

echo "✓ Test project created at $TEST_DIR"
