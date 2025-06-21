#!/bin/bash
# parallel_zip_test.sh - Test script for parallel_zip functions

echo "Running tests for parallel_zip functions..."
echo ""

# Create a temporary Python script with all our tests
cat > parallel_zip_test.py << 'EOL'
#!/usr/bin/env python3
import sys
import os
import shutil
from importlib import reload

# Try to import the parallel_zip module
try:
    import parallel_zip
    reload(parallel_zip)  # Ensure we have the latest version
    from parallel_zip import zipper, parse_command, execute_command, parallel_zip, Cross
except ImportError:
    print("ERROR: Could not import parallel_zip module.")
    print("Make sure the parallel_zip.py file is in the same directory or in your Python path.")
    sys.exit(1)
except AttributeError as e:
    if "module 'parallel_zip' has no attribute 'Cross'" in str(e):
        print("INFO: Cross helper function not found in module. Defining it locally for testing.")
        def Cross(**kwargs):
            """Create a cross-product parameter structure for zipper and parallel_zip."""
            return [{key: vals} for key, vals in kwargs.items()]
    else:
        raise e

# Create test directory and files
test_dir = "parallel_zip_test_tmp"
os.makedirs(test_dir, exist_ok=True)
os.chdir(test_dir)

# Create test files for our tests
with open("file1.txt", "w") as f:
    f.write("This is test file 1\n")

with open("file2.txt", "w") as f:
    f.write("This is test file 2\n")

with open("data.csv", "w") as f:
    f.write("id,name,value\n")
    f.write("1,apple,3.5\n")
    f.write("2,banana,2.7\n")
    f.write("3,cherry,4.2\n")

with open("numbers.txt", "w") as f:
    f.write("10\n20\n30\n40\n50\n")

# Create a list to store test results
test_results = []

# Test 1: Basic usage with a single parameter
print("=== Test 1: Basic command with single parameter ===")
print("Invocation: parallel_zip(\"ls {dir}\", dir=\"/tmp\", verbose=True)")
try:
    result1 = parallel_zip("ls {dir}", dir="/tmp", verbose=True)
    print(f"Result 1: {result1}")
    test_results.append(("Basic command with single parameter", "PASS" if result1 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Basic command with single parameter", "ERROR"))

# Test 2: Multiple values in a parameter
print("\n=== Test 2: Multiple values in parameter ===")
print("Invocation: parallel_zip(\"ls {dir}\", dir=[\"/tmp\", \"/home\"], verbose=True)")
try:
    result2 = parallel_zip("ls {dir}", dir=["/tmp", "/home"], verbose=True)
    print(f"Result 2: {result2}")
    test_results.append(("Multiple values in parameter", "PASS" if result2 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Multiple values in parameter", "ERROR"))

# Test 3: Dry run to see what commands would be executed
print("\n=== Test 3: Dry run test ===")
print("Invocation: parallel_zip(\"cat {file}\", file=[\"file1.txt\", \"file2.txt\"], dry_run=True)")
try:
    commands = parallel_zip("cat {file}", file=["file1.txt", "file2.txt"], dry_run=True)
    print(f"Commands: {commands}")
    test_results.append(("Dry run test", "PASS" if commands and len(commands) == 2 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Dry run test", "ERROR"))

# Test 4: Cross product functionality
print("\n=== Test 4: Cross product functionality ===")
print("""Invocation: parallel_zip(
    "echo 'Processing {file} with {mode}'",
    file=["file1.txt", "file2.txt"],
    cross=[{"mode": ["fast", "thorough"]}],
    verbose=True
)""")
try:
    result4 = parallel_zip(
        "echo 'Processing {file} with {mode}'",
        file=["file1.txt", "file2.txt"],
        cross=[{"mode": ["fast", "thorough"]}],
        verbose=True
    )
    print(f"Result 4: {result4}")
    test_results.append(("Cross product functionality", "PASS" if result4 and "fast" in result4 and "thorough" in result4 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cross product functionality", "ERROR"))

# Test 5: Test awk command with complex syntax
print("\n=== Test 5: Awk command with complex syntax ===")
print("""Invocation: parallel_zip(
    "awk -F, '{{print $1,$2}}' {file}",
    file="data.csv",
    verbose=True
)""")
try:
    result5 = parallel_zip(
        "awk -F, '{{print $1,$2}}' {file}",
        file="data.csv",
        verbose=True
    )
    print(f"Result 5: {result5}")
    test_results.append(("Awk command with complex syntax", "PASS" if result5 and "id name" in result5 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Awk command with complex syntax", "ERROR"))

# Test 6: Multiple parameters and complex command
print("\n=== Test 6: Multiple parameters and complex command ===")
print("""Invocation: parallel_zip(
    "head -{lines} {file} | cut -d, -f{columns}",
    file=["data.csv"],
    lines=2,
    columns="1,2",
    verbose=True
)""")
try:
    result6 = parallel_zip(
        "head -{lines} {file} | cut -d, -f{columns}",
        file=["data.csv"],
        lines=2,
        columns="1,2",
        verbose=True
    )
    print(f"Result 6: {result6}")
    test_results.append(("Multiple parameters and complex command", "PASS" if result6 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Multiple parameters and complex command", "ERROR"))

# Test 7: Multi-line commands (each line joined with &&)
print("\n=== Test 7: Multi-line commands ===")
print("""Invocation: multiline_cmd = \"\"\"
    mkdir -p test_dir_{num}
    echo "Test {num}" > test_dir_{num}/test.txt
    ls -la test_dir_{num}
    \"\"\"
    parallel_zip(multiline_cmd, num=[1, 2], verbose=True)""")
try:
    multiline_cmd = """
    mkdir -p test_dir_{num}
    echo "Test {num}" > test_dir_{num}/test.txt
    ls -la test_dir_{num}
    """
    result7 = parallel_zip(multiline_cmd, num=[1, 2], verbose=True)
    print(f"Result 7: {result7}")
    test_results.append(("Multi-line commands", "PASS" if result7 and "test.txt" in result7 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Multi-line commands", "ERROR"))

# Test 8: Multiple cross-product parameters
print("\n=== Test 8: Multiple cross-product parameters ===")
print("""Invocation: parallel_zip(
    "echo 'Processing {file} with option {option} at level {level}'",
    file=["file1.txt", "file2.txt"],
    cross=[
        {"option": ["a", "b"]},
        {"level": [1, 2]}
    ],
    verbose=True
)""")
try:
    result8 = parallel_zip(
        "echo 'Processing {file} with option {option} at level {level}'",
        file=["file1.txt", "file2.txt"],
        cross=[
            {"option": ["a", "b"]},
            {"level": [1, 2]}
        ],
        verbose=True
    )
    print(f"Result 8: {result8}")
    test_results.append(("Multiple cross-product parameters", "PASS" if result8 and "option a at level 1" in result8 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Multiple cross-product parameters", "ERROR"))

# Test 9: Python expression evaluation in command
print("\n=== Test 9: Python expression evaluation ===")
print("""Invocation: nums = [10, 20, 30]
    parallel_zip(
        "echo 'Double of {num} is {int(num) * 2}'",
        num=nums,
        verbose=True
    )""")
try:
    nums = [10, 20, 30]
    result9 = parallel_zip(
        "echo 'Double of {num} is {int(num) * 2}'",
        num=nums,
        verbose=True
    )
    print(f"Result 9: {result9}")
    test_results.append(("Python expression evaluation", "PASS" if result9 and "Double of 10 is 20" in result9 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Python expression evaluation", "ERROR"))

# Test 10: Broadcasting single values with multiple inputs
print("\n=== Test 10: Broadcasting single values with multiple inputs ===")
print("""Invocation: parallel_zip(
    "echo 'Combining {file} with version {version}'",
    file=["file1.txt", "file2.txt", "data.csv"],
    version="v1.0",
    verbose=True
)""")
try:
    result10 = parallel_zip(
        "echo 'Combining {file} with version {version}'",
        file=["file1.txt", "file2.txt", "data.csv"],
        version="v1.0",
        verbose=True
    )
    print(f"Result 10: {result10}")
    test_results.append(("Broadcasting single values", "PASS" if result10 and result10.count("v1.0") == 3 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Broadcasting single values", "ERROR"))

# Test 11: Complex cross product with multiple parameters
print("\n=== Test 11: Complex cross product ===")
print("""Invocation: parallel_zip(
    "echo 'Processing {file} with {tool} on {platform}'",
    file=["file1.txt"],
    cross=[
        {"tool": ["grep", "sed", "awk"]},
        {"platform": ["linux", "mac"]}
    ],
    verbose=True
)""")
try:
    result11 = parallel_zip(
        "echo 'Processing {file} with {tool} on {platform}'",
        file=["file1.txt"],
        cross=[
            {"tool": ["grep", "sed", "awk"]},
            {"platform": ["linux", "mac"]}
        ],
        verbose=True
    )
    print(f"Result 11: {result11}")
    test_results.append(("Complex cross product", "PASS" if result11 and "grep" in result11 and "linux" in result11 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Complex cross product", "ERROR"))

# Test 12: Complex shell command structure
print("\n=== Test 12: Complex shell command ===")
print("""Invocation: complex_cmd = \"\"\"
    mkdir -p output_{id}
    cat {file} | grep {pattern} > output_{id}/filtered.txt
    wc -l output_{id}/filtered.txt
    \"\"\"
    parallel_zip(
        complex_cmd,
        id=[1, 2],
        file=["file1.txt", "file2.txt"],
        pattern="test",
        verbose=True
    )""")
try:
    complex_cmd = """
    mkdir -p output_{id}
    cat {file} | grep {pattern} > output_{id}/filtered.txt
    wc -l output_{id}/filtered.txt
    """
    result12 = parallel_zip(
        complex_cmd,
        id=[1, 2],
        file=["file1.txt", "file2.txt"],
        pattern="test",
        verbose=True
    )
    print(f"Result 12: {result12}")
    test_results.append(("Complex shell command structure", "PASS" if result12 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Complex shell command structure", "ERROR"))

# Test 13: Motivating example from documentation
print("\n=== Test 13: Motivating example - RNA-seq pipeline ===")
print("""Invocation: samples = ['U', 'E']
    refs = ['28SrRNA', '18SrRNA']
    ref_path = '~/reference'
    in_path = 'trim'
    out_path = 'map'
    parallel_zip(\"\"\"
    hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
    \"\"\",
        R1=[f'{sample}_R1' for sample in samples],
        R2=[f'{sample}_R2' for sample in samples],
        cross=[{'sample': samples}, {'ref': refs}],
        dry_run=True
    )""")
try:
    samples = ['U', 'E']
    refs = ['28SrRNA', '18SrRNA']
    ref_path = '~/reference'
    in_path = 'trim'
    out_path = 'map'
    result13 = parallel_zip("""
    hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
    """,
        R1=[f'{sample}_R1' for sample in samples],
        R2=[f'{sample}_R2' for sample in samples],
        cross=[{'sample': samples}, {'ref': refs}],
        dry_run=True
    )
    print(f"Result 13: {result13}")
    test_results.append(("Motivating example - RNA-seq pipeline", "PASS" if result13 and len(result13) == 8 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Motivating example - RNA-seq pipeline", "ERROR"))

# Test 14: Cross-only parameters
print("\n=== Test 14: Cross-only parameters ===")
print("""Invocation: parallel_zip(
    "echo 'Testing mode={mode} level={level}'",
    cross=[
        {"mode": ["fast", "thorough"]},
        {"level": ["low", "high"]}
    ],
    verbose=True
)""")
try:
    result14 = parallel_zip(
        "echo 'Testing mode={mode} level={level}'",
        cross=[
            {"mode": ["fast", "thorough"]},
            {"level": ["low", "high"]}
        ],
        verbose=True
    )
    print(f"Result 14: {result14}")
    test_results.append(("Cross-only parameters", "PASS" if result14 and "fast" in result14 and "high" in result14 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cross-only parameters", "ERROR"))

# Test 15: Using Cross helper function with named values
print("\n=== Test 15: Cross helper function with named values ===")
print("""Invocation: parallel_zip(
    "echo 'File: {file}, Option: {option}, Level: {level}'",
    file=["file1.txt", "file2.txt"],
    cross=Cross(
        option=["a", "b"],
        level=["1", "2"]
    ),
    verbose=True
)""")
try:
    result15 = parallel_zip(
        "echo 'File: {file}, Option: {option}, Level: {level}'",
        file=["file1.txt", "file2.txt"],
        cross=Cross(
            option=["a", "b"],
            level=["1", "2"]
        ),
        verbose=True
    )
    print(f"Result 15: {result15}")
    test_results.append(("Cross helper function with named values", "PASS" if result15 and "Option: a" in result15 and "Level: 1" in result15 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cross helper function with named values", "ERROR"))

# Test 16: Cross helper function with only cross parameters
print("\n=== Test 16: Cross helper function with only cross parameters ===")
print("""Invocation: parallel_zip(
    "echo 'Testing tool={tool} platform={platform} option={option}'",
    cross=Cross(
        tool=["hammer", "screwdriver", "wrench"],
        platform=["wood", "metal"],
        option=["fast", "precise"]
    ),
    verbose=True
)""")
try:
    result16 = parallel_zip(
        "echo 'Testing tool={tool} platform={platform} option={option}'",
        cross=Cross(
            tool=["hammer", "screwdriver", "wrench"],
            platform=["wood", "metal"],
            option=["fast", "precise"]
        ),
        verbose=True
    )
    print(f"Result 16: {result16}")
    test_results.append(("Cross helper function with only cross parameters", "PASS" if result16 and "hammer" in result16 and "metal" in result16 and "fast" in result16 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cross helper function with only cross parameters", "ERROR"))

# Test 17: Using Cross helper function in RNA-seq pipeline example
print("\n=== Test 17: Cross helper function in RNA-seq pipeline example ===")
print("""Invocation: samples = ['U', 'E']
    refs = ['28SrRNA', '18SrRNA']
    ref_path = '~/reference'
    in_path = 'trim'
    out_path = 'map'
    parallel_zip(\"\"\"
    hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
    \"\"\",
        R1=[f'{sample}_R1' for sample in samples],
        R2=[f'{sample}_R2' for sample in samples],
        cross=Cross(
            sample=samples,
            ref=refs
        ),
        dry_run=True
    )""")
try:
    samples = ['U', 'E']
    refs = ['28SrRNA', '18SrRNA']
    ref_path = '~/reference'
    in_path = 'trim'
    out_path = 'map'
    result17 = parallel_zip("""
    hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
    """,
        R1=[f'{sample}_R1' for sample in samples],
        R2=[f'{sample}_R2' for sample in samples],
        cross=Cross(
            sample=samples,
            ref=refs
        ),
        dry_run=True
    )
    print(f"Result 17: {result17}")
    test_results.append(("Cross helper function in RNA-seq pipeline example", "PASS" if result17 and len(result17) == 8 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Cross helper function in RNA-seq pipeline example", "ERROR"))

# NEW TEST 18: Command with no parameters (testing the fix)
print("\n=== Test 18: Command with no parameters ===")
print("Invocation: parallel_zip(\"ls\", verbose=True)")
try:
    result18 = parallel_zip("ls", verbose=True)
    print(f"Result 18: {result18}")
    # Should run successfully and list current directory
    test_results.append(("Command with no parameters", "PASS" if result18 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with no parameters", "ERROR"))

# NEW TEST 19: Command with no parameters in dry run mode
print("\n=== Test 19: Command with no parameters (dry run) ===")
print("Invocation: parallel_zip(\"echo 'Hello World'\", dry_run=True)")
try:
    result19 = parallel_zip("echo 'Hello World'", dry_run=True)
    print(f"Result 19: {result19}")
    # Should return a list with the command
    test_results.append(("Command with no parameters (dry run)", "PASS" if result19 == ["echo 'Hello World'"] else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with no parameters (dry run)", "ERROR"))

# NEW TEST 20: Verify verbose output doesn't show misleading warnings
print("\n=== Test 20: Verify no misleading warnings in verbose mode ===")
print("Invocation: parallel_zip(\"echo 'Test'\", verbose=True)")
print("(Note: This test passes if no 'warning' text appears in output)")
try:
    # Capture stdout to check for warning text
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        result20 = parallel_zip("echo 'Test'", verbose=True)

    captured_output = f.getvalue()
    print(f"Captured output: {captured_output}")
    print(f"Result 20: {result20}")

    # Test passes if there's no "warning" in the output
    has_warning = "warning" in captured_output.lower()
    test_results.append(("No misleading warnings in verbose mode", "PASS" if not has_warning and result20 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("No misleading warnings in verbose mode", "ERROR"))

# NEW TEST 21: Command with only cross parameters and no named parameters
print("\n=== Test 21: Command with only cross parameters and no named parameters ===")
print("""Invocation: parallel_zip(
    "echo 'Mode: {mode}'",
    cross=[{"mode": ["test1", "test2"]}],
    verbose=True
)""")
try:
    result21 = parallel_zip(
        "echo 'Mode: {mode}'",
        cross=[{"mode": ["test1", "test2"]}],
        verbose=True
    )
    print(f"Result 21: {result21}")
    test_results.append(("Command with only cross parameters", "PASS" if result21 and "test1" in result21 and "test2" in result21 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Command with only cross parameters", "ERROR"))

# NEW TEST 22: Complex command with no parameters
print("\n=== Test 22: Complex multi-line command with no parameters ===")
print("""Invocation: complex_no_params = \"\"\"
    pwd
    date
    echo "Done"
    \"\"\"
    parallel_zip(complex_no_params, verbose=True)""")
try:
    complex_no_params = """
    pwd
    date
    echo "Done"
    """
    result22 = parallel_zip(complex_no_params, verbose=True)
    print(f"Result 22: {result22}")
    test_results.append(("Complex multi-line command with no parameters", "PASS" if result22 and "Done" in result22 else "FAIL"))
except Exception as e:
    print(f"Exception: {e}")
    test_results.append(("Complex multi-line command with no parameters", "ERROR"))

# Clean up test directories
for i in [1, 2]:
    try:
        shutil.rmtree(f"test_dir_{i}")
        shutil.rmtree(f"output_{i}")
    except:
        pass

# Print a tabulated summary of all test results
print("\n\n=== SUMMARY OF TEST RESULTS ===")
print(f"{'Test Description':<55} | {'Result':<10}")
print("-" * 68)
for description, result in test_results:
    print(f"{description:<55} | {result:<10}")

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
chmod +x parallel_zip_test.py

# Run the tests
python3 parallel_zip_test.py

# Clean up the test script
rm parallel_zip_test.py

exit $?
