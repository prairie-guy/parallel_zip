#!/bin/bash
# pz_test.sh - Test script for pz (quick shell execution) function

echo "Running tests for pz function..."
echo ""

# Create a temporary Python script with all our tests
cat > pz_test.py << 'EOL'
#!/usr/bin/env python3
import sys
import os
import shutil
from importlib import reload

# Try to import the parallel_zip module
try:
    import parallel_zip
    reload(parallel_zip)  # Ensure we have the latest version
    from parallel_zip import pz
except ImportError:
    print("ERROR: Could not import parallel_zip module.")
    print("Make sure the parallel_zip.py file is in the same directory or in your Python path.")
    sys.exit(1)
except AttributeError as e:
    print(f"ERROR: Could not import pz function: {e}")
    print("Make sure pz function is defined in parallel_zip.py")
    sys.exit(1)

# Create test directory and files
test_dir = "pz_test_tmp"
os.makedirs(test_dir, exist_ok=True)
os.chdir(test_dir)

# Create test files for our tests
with open("test1.txt", "w") as f:
    f.write("This is test file 1\nSecond line\nThird line\n")

with open("test2.txt", "w") as f:
    f.write("This is test file 2\nAnother line\nFinal line\n")

with open("data.csv", "w") as f:
    f.write("id,name,value\n")
    f.write("1,apple,3.5\n")
    f.write("2,banana,2.7\n")
    f.write("3,cherry,4.2\n")

with open("numbers.txt", "w") as f:
    for i in range(1, 11):
        f.write(f"{i}\n")

# Create a list to store test results
test_results = []

# Test 1: Basic command execution with default lines=True
print("=== Test 1: Basic command with lines=True (default) ===")
print("Invocation: pz('ls')")
try:
    result1 = pz("ls")
    print(f"Result type: {type(result1)}")
    print(f"Result: {result1}")
    test_results.append(("Basic command with lines=True", "PASS" if isinstance(result1, list) and len(result1) > 0 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Basic command with lines=True", "ERROR"))

# Test 2: Command with lines=False for raw output
print("\n=== Test 2: Command with lines=False ===")
print("Invocation: pz('ls', lines=False)")
try:
    result2 = pz("ls", lines=False)
    print(f"Result type: {type(result2)}")
    print(f"Result: {repr(result2)}")
    test_results.append(("Command with lines=False", "PASS" if isinstance(result2, str) else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with lines=False", "ERROR"))

# Test 3: Command with pipes
print("\n=== Test 3: Command with pipes ===")
print("Invocation: pz('cat test1.txt | grep test')")
try:
    result3 = pz("cat test1.txt | grep test")
    print(f"Result: {result3}")
    test_results.append(("Command with pipes", "PASS" if result3 and "test" in result3[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with pipes", "ERROR"))

# Test 4: AWK command with single quotes
print("\n=== Test 4: AWK command with single quotes ===")
print("Invocation: pz(\"cat data.csv | awk -F, '{print $2}'\")")
try:
    result4 = pz("cat data.csv | awk -F, '{print $2}'")
    print(f"Result: {result4}")
    test_results.append(("AWK with single quotes", "PASS" if result4 and "name" in result4 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("AWK with single quotes", "ERROR"))

# Test 5: Environment variable substitution
print("\n=== Test 5: Environment variable substitution ===")
print("Invocation: pz('echo $HOME')")
try:
    result5 = pz("echo $HOME")
    print(f"Result: {result5}")
    test_results.append(("Environment variable substitution", "PASS" if result5 and "/" in result5[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Environment variable substitution", "ERROR"))

# Test 6: Python variable substitution
print("\n=== Test 6: Python variable substitution ===")
print("Invocation: test_var = 'hello'; pz('echo {test_var}')")
try:
    test_var = "hello"
    result6 = pz("echo {test_var}")
    print(f"Result: {result6}")
    test_results.append(("Python variable substitution", "PASS" if result6 and "hello" in result6[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Python variable substitution", "ERROR"))

# Test 7: Line counting with wc
print("\n=== Test 7: Line counting with wc ===")
print("Invocation: pz('wc -l test1.txt')")
try:
    result7 = pz("wc -l test1.txt")
    print(f"Result: {result7}")
    test_results.append(("Line counting with wc", "PASS" if result7 and "3" in result7[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Line counting with wc", "ERROR"))

# Test 8: Multiple commands with semicolon
print("\n=== Test 8: Multiple commands with semicolon ===")
print("Invocation: pz('echo Start; ls test*.txt; echo End')")
try:
    result8 = pz("echo Start; ls test*.txt; echo End")
    print(f"Result: {result8}")
    test_results.append(("Multiple commands with semicolon", "PASS" if result8 and "Start" in result8 and "End" in result8 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Multiple commands with semicolon", "ERROR"))

# Test 9: Grep with regex
print("\n=== Test 9: Grep with regex ===")
print("Invocation: pz(\"grep '^[0-9]' numbers.txt | head -5\")")
try:
    result9 = pz("grep '^[0-9]' numbers.txt | head -5")
    print(f"Result: {result9}")
    test_results.append(("Grep with regex", "PASS" if result9 and len(result9) == 5 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Grep with regex", "ERROR"))

# Test 10: Output redirection
print("\n=== Test 10: Output redirection ===")
print("Invocation: pz('echo test > output.txt; cat output.txt')")
try:
    result10 = pz("echo test > output.txt; cat output.txt")
    print(f"Result: {result10}")
    test_results.append(("Output redirection", "PASS" if result10 and "test" in result10 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Output redirection", "ERROR"))

# Test 11: Command with no output
print("\n=== Test 11: Command with no output ===")
print("Invocation: pz('true')")
try:
    result11 = pz("true")
    print(f"Result: {result11}")
    test_results.append(("Command with no output", "PASS" if result11 is not None else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with no output", "ERROR"))

# Test 12: Complex AWK with dollar signs
print("\n=== Test 12: Complex AWK with dollar signs ===")
print("Invocation: pz(\"awk '{sum += $3} END {print sum}' data.csv\")")
try:
    result12 = pz("awk '{sum += $3} END {print sum}' data.csv")
    print(f"Result: {result12}")
    # Note: This will include the header 'value' in sum, but that's ok for the test
    test_results.append(("Complex AWK with dollar signs", "PASS" if result12 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Complex AWK with dollar signs", "ERROR"))

# Test 13: Find command
print("\n=== Test 13: Find command ===")
print("Invocation: pz('find . -name \"*.txt\" | sort')")
try:
    result13 = pz('find . -name "*.txt" | sort')
    print(f"Result: {result13}")
    test_results.append(("Find command", "PASS" if result13 and "./test1.txt" in result13 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Find command", "ERROR"))

# Test 14: Sed command with dollar sign
print("\n=== Test 14: Sed command with dollar sign ===")
print("Invocation: pz(\"echo 'hello world' | sed 's/world$/universe/'\")")
try:
    result14 = pz("echo 'hello world' | sed 's/world$/universe/'")
    print(f"Result: {result14}")
    test_results.append(("Sed with dollar sign", "PASS" if result14 and "universe" in result14[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Sed with dollar sign", "ERROR"))

# Test 15: Empty result handling
print("\n=== Test 15: Empty result handling ===")
print("Invocation: pz('grep nonexistent test1.txt')")
try:
    result15 = pz("grep nonexistent test1.txt")
    print(f"Result: {result15}")
    print(f"Result type: {type(result15)}")
    print(f"Result repr: {repr(result15)}")
    # Accept either empty list or None as valid for no output
    test_results.append(("Empty result handling", "PASS" if result15 == [] or result15 == [''] or result15 is None else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Empty result handling", "ERROR"))

# Test 16: Command with quotes and spaces
print("\n=== Test 16: Command with quotes and spaces ===")
print("Invocation: pz('echo \"Hello   World\"')")
try:
    result16 = pz('echo "Hello   World"')
    print(f"Result: {result16}")
    test_results.append(("Command with quotes and spaces", "PASS" if result16 and "Hello   World" in result16[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with quotes and spaces", "ERROR"))

# Test 17: Head and tail combination
print("\n=== Test 17: Head and tail combination ===")
print("Invocation: pz('seq 1 20 | head -10 | tail -3')")
try:
    result17 = pz("seq 1 20 | head -10 | tail -3")
    print(f"Result: {result17}")
    test_results.append(("Head and tail combination", "PASS" if result17 and len(result17) == 3 and "8" in result17 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Head and tail combination", "ERROR"))

# Test 18: Variable expansion in paths
print("\n=== Test 18: Variable expansion in paths ===")
print("Invocation: data_dir = '.'; pz('ls {data_dir}/*.csv')")
try:
    data_dir = "."
    result18 = pz("ls {data_dir}/*.csv")
    print(f"Result: {result18}")
    test_results.append(("Variable expansion in paths", "PASS" if result18 and "data.csv" in result18[0] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Variable expansion in paths", "ERROR"))

# Test 19: Sort and uniq
print("\n=== Test 19: Sort and uniq ===")
print("Invocation: pz('echo -e \"apple\\nbanana\\napple\\ncherry\\nbanana\" | sort | uniq')")
try:
    result19 = pz('echo -e "apple\\nbanana\\napple\\ncherry\\nbanana" | sort | uniq')
    print(f"Result: {result19}")
    test_results.append(("Sort and uniq", "PASS" if result19 and len(result19) == 3 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Sort and uniq", "ERROR"))

# Test 20: Cut command
print("\n=== Test 20: Cut command ===")
print("Invocation: pz('cut -d, -f2 data.csv')")
try:
    result20 = pz("cut -d, -f2 data.csv")
    print(f"Result: {result20}")
    test_results.append(("Cut command", "PASS" if result20 and "apple" in result20 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cut command", "ERROR"))

# Clean up test files
os.remove("output.txt") if os.path.exists("output.txt") else None

# Print a tabulated summary of all test results
print("\n\n=== SUMMARY OF TEST RESULTS ===")
print(f"{'Test Description':<40} | {'Result':<10}")
print("-" * 53)
for description, result in test_results:
    print(f"{description:<40} | {result:<10}")

# Calculate overall pass rate
pass_count = sum(1 for _, result in test_results if result == "PASS")
total_count = len(test_results)
pass_rate = (pass_count / total_count) * 100 if total_count > 0 else 0

print("\n=== OVERALL TEST SUMMARY ===")
print(f"Total Tests: {total_count}")
print(f"Passed: {pass_count}")
print(f"Failed: {total_count - pass_count - sum(1 for _, result in test_results if result == 'ERROR')}")
print(f"Errors: {sum(1 for _, result in test_results if result == 'ERROR')}")
print(f"Pass Rate: {pass_rate:.2f}%")

# Clean up test directory
os.chdir("..")
try:
    shutil.rmtree(test_dir)
except:
    print(f"Warning: Could not remove test directory: {test_dir}")

# Exit with appropriate status code
if pass_count == total_count:
    sys.exit(0)
else:
    sys.exit(1)
EOL

# Make the test script executable
chmod +x pz_test.py

# Run the tests
python3 pz_test.py

# Clean up the test script
rm pz_test.py

exit $?
