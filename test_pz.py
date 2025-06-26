#!/usr/bin/env python3
"""
AWK exercise tests using pz function
Run with: ward

Focus: Testing diverse AWK functionality through the pz wrapper
Based on exercises from: https://github.com/learnbyexample/learn_gnuawk

All tests use the pz function (parallel_zip wrapper) with verbose=True
Tests cover various AWK features: field manipulation, regex, built-in functions,
control structures, mathematical operations, and string processing.
"""
import os
import subprocess
from ward import test, fixture, skip
from parallel_zip import pz

@fixture
def clean_env():
    """Fixture to provide a clean environment"""
    # Save original environment
    original_env = os.environ.copy()

    # Set any required environment variables
    os.environ['TESTING'] = '1'

    yield os.environ

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def is_gawk_available():
    """Check if GNU AWK (gawk) is available on the system"""
    try:
        result = subprocess.run(['gawk', '--version'], capture_output=True, text=True)
        return result.returncode == 0 and 'GNU Awk' in result.stdout
    except FileNotFoundError:
        return False


def skipif_no_gawk(test_func):
    """Skip test if gawk is not available"""
    if not is_gawk_available():
        return skip("GNU AWK not available")(test_func)
    return test_func


# POSIX AWK Tests
@test("pz executes simple echo command")
def test_pz_simple_echo(env=clean_env):
    """Test that pz can execute a simple echo command"""
    result = pz("echo 'Hello, World!'")
    assert result == ["Hello, World!"], f"Expected ['Hello, World!'], got {result}"


@test("pz handles multiple line output")
def test_pz_multiline_output(env=clean_env):
    """Test that pz returns output as list of lines"""
    result = pz("printf 'Line 1\\nLine 2\\nLine 3\\n'")
    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result == ["Line 1", "Line 2", "Line 3"], f"Unexpected output: {result}"


@test("awk field extraction and NF usage")
def test_awk_fields(env=clean_env):
    """Test AWK field extraction and NF special variable"""
    # Print second field and field count
    result = pz("printf 'apple banana cherry\\ndog cat\\none two three four\\n' | awk '{print $2, NF}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "banana 3", "Second field of 'apple banana cherry' and NF=3"
    assert result[1] == "cat 2", "Second field of 'dog cat' and NF=2"
    assert result[2] == "two 4", "Second field of 'one two three four' and NF=4"

    # Verify each line has correct format
    for line in result:
        parts = line.split()
        assert len(parts) == 2, f"Each output should have 2 parts: field and count"
        assert parts[1].isdigit(), f"Second part should be a digit (field count)"


@test("awk NF and last field extraction")
def test_awk_nf_usage(env=clean_env):
    """Test AWK NF for accessing last field"""
    # Print last field using $NF
    result = pz("printf 'first second last\\nonly\\nalpha beta gamma delta\\n' | awk '{print $NF}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "last", "Last field of 'first second last'"
    assert result[1] == "only", "Last field when only one field"
    assert result[2] == "delta", "Last field of 'alpha beta gamma delta'"

    # Test $(NF-1) for second-to-last field
    result2 = pz("printf 'a b c d\\nx y z\\n' | awk 'NF > 1 {print $(NF-1)}'")
    assert len(result2) == 2, "Should process lines with more than 1 field"
    assert result2[0] == "c", "Second-to-last of 'a b c d'"
    assert result2[1] == "y", "Second-to-last of 'x y z'"


@test("awk pattern matching with regex")
def test_awk_pattern_matching(env=clean_env):
    """Test AWK pattern matching with regular expressions"""
    # Match lines containing 'the' (including as substring in 'another')
    result = pz("printf 'the quick brown\\nfox jumps over\\nthe lazy dog\\nanother line\\n' | awk '/the/'")

    assert len(result) == 3, f"Expected 3 matching lines, got {len(result)}"
    assert "the quick brown" in result, "Should match first line with 'the'"
    assert "the lazy dog" in result, "Should match third line with 'the'"
    assert "another line" in result, "Should match 'another' (contains 'the')"

    # Verify no false matches
    for line in result:
        assert "the" in line, f"Line should contain 'the': {line}"


@test("awk negated pattern matching")
def test_awk_negated_pattern(env=clean_env):
    """Test AWK negated pattern matching"""
    # Print lines NOT containing 'e'
    result = pz("printf 'apple\\nbanana\\ncherry\\nfig\\n' | awk '!/e/'")

    assert len(result) == 2, f"Expected 2 non-matching lines, got {len(result)}"
    assert "banana" in result, "banana doesn't contain 'e'"
    assert "fig" in result, "fig doesn't contain 'e'"

    # Verify no 'e' in results
    for line in result:
        assert "e" not in line, f"Line should not contain 'e': {line}"

    # Verify excluded lines contain 'e'
    excluded = ["apple", "cherry"]
    for item in excluded:
        assert item not in result, f"{item} should be excluded (contains 'e')"


@test("awk gsub global substitution")
def test_awk_gsub(env=clean_env):
    """Test AWK gsub function for global substitution"""
    # Replace all 'o' with '0' (zero)
    result = pz("printf 'hello world\\nfoo bar boo\\nno replacement\\n' | awk '{gsub(/o/, \"0\"); print}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "hell0 w0rld", "All 'o' replaced with '0'"
    assert result[1] == "f00 bar b00", "Multiple 'o' replacements"
    assert result[2] == "n0 replacement", "Single 'o' replacement"

    # Verify no 'o' remains in output
    for line in result:
        assert "o" not in line, f"No 'o' should remain: {line}"
        # Count zeros to verify replacements
        original_o_count = ["hello world", "foo bar boo", "no replacement"]
        for i, line in enumerate(result):
            assert line.count("0") > 0, f"Line {i} should have replacements"


@test("awk sub single substitution")
def test_awk_sub(env=clean_env):
    """Test AWK sub function for single substitution"""
    # Replace only first 'e' with 'E'
    result = pz("printf 'hello everyone\\nsee the tree\\nno match here\\n' | awk '{sub(/e/, \"E\"); print}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "hEllo everyone", "First 'e' replaced in 'hello everyone'"
    assert result[1] == "sEe the tree", "First 'e' replaced in 'see the tree'"
    assert result[2] == "no match hEre", "First 'e' replaced in 'no match here'"

    # Verify only first 'e' was replaced
    for i, line in enumerate(result):
        # Count 'E' - should be exactly 1
        assert line.count("E") == 1, f"Should have exactly one 'E': {line}"
        # Original strings for comparison
        originals = ["hello everyone", "see the tree", "no match here"]
        # Verify remaining 'e's if any
        if originals[i].count("e") > 1:
            assert "e" in line, f"Should still have lowercase 'e': {line}"


@test("awk length function")
def test_awk_length(env=clean_env):
    """Test AWK length function"""
    # Print length of each line
    result = pz("printf 'short\\nmedium length\\nthis is a longer line\\nx\\n' | awk '{print length, $0}'")

    assert len(result) == 4, f"Expected 4 lines, got {len(result)}"
    assert result[0] == "5 short", "Length of 'short' is 5"
    assert result[1] == "13 medium length", "Length of 'medium length' is 13"
    assert result[2] == "21 this is a longer line", "Length of 'this is a longer line' is 21"
    assert result[3] == "1 x", "Length of 'x' is 1"

    # Verify length calculations
    for line in result:
        parts = line.split(' ', 1)
        length = int(parts[0])
        text = parts[1] if len(parts) > 1 else ""
        assert length == len(text), f"Length mismatch: reported {length}, actual {len(text)}"


@test("awk substr function")
def test_awk_substr(env=clean_env):
    """Test AWK substr function"""
    # Extract substring starting at position 3, length 4
    result = pz("printf 'abcdefghij\\n1234567890\\nHello World\\n' | awk '{print substr($0, 3, 4)}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "cdef", "substr('abcdefghij', 3, 4) = 'cdef'"
    assert result[1] == "3456", "substr('1234567890', 3, 4) = '3456'"
    assert result[2] == "llo ", "substr('Hello World', 3, 4) = 'llo '"

    # Test substr without length parameter (to end of string)
    result2 = pz("printf 'prefix_suffix\\nstart_end\\n' | awk '{print substr($0, 8)}'")
    assert len(result2) == 2, "Should process 2 lines"
    assert result2[0] == "suffix", "substr from position 8 to end"
    assert result2[1] == "nd", "substr from position 8 to end"


@test("awk mathematical calculations")
def test_awk_math(env=clean_env):
    """Test AWK mathematical operations"""
    # Sum of fields and average
    result = pz("printf '10 20 30\\n5 15\\n100 200 300 400\\n' | awk '{sum=0; for(i=1;i<=NF;i++) sum+=$i; print sum, sum/NF}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "60 20", "Sum=60, Average=20 for '10 20 30'"
    assert result[1] == "20 10", "Sum=20, Average=10 for '5 15'"
    assert result[2] == "1000 250", "Sum=1000, Average=250 for '100 200 300 400'"

    # Verify calculations
    test_data = [[10, 20, 30], [5, 15], [100, 200, 300, 400]]
    for i, line in enumerate(result):
        parts = line.split()
        sum_val = int(parts[0])
        avg_val = float(parts[1])
        expected_sum = sum(test_data[i])
        expected_avg = expected_sum / len(test_data[i])
        assert sum_val == expected_sum, f"Sum mismatch line {i+1}"
        assert avg_val == expected_avg, f"Average mismatch line {i+1}"


@test("awk conditional mathematical operations")
def test_awk_conditional_math(env=clean_env):
    """Test AWK conditional logic with mathematical operations"""
    # Count positive and negative numbers
    result = pz("printf '5 -3 8 -2\\n10 20 30\\n-5 -10 -15\\n0 1 -1\\n' | awk '{pos=0; neg=0; for(i=1;i<=NF;i++) if($i>0) pos++; else if($i<0) neg++; print \"pos:\" pos \" neg:\" neg}'")

    assert len(result) == 4, f"Expected 4 lines, got {len(result)}"
    assert result[0] == "pos:2 neg:2", "2 positive, 2 negative in '5 -3 8 -2'"
    assert result[1] == "pos:3 neg:0", "3 positive, 0 negative in '10 20 30'"
    assert result[2] == "pos:0 neg:3", "0 positive, 3 negative in '-5 -10 -15'"
    assert result[3] == "pos:1 neg:1", "1 positive, 1 negative in '0 1 -1' (0 is neither)"

    # Verify the counting logic
    test_data = [
        [5, -3, 8, -2],
        [10, 20, 30],
        [-5, -10, -15],
        [0, 1, -1]
    ]
    for i, line in enumerate(result):
        pos_count = sum(1 for x in test_data[i] if x > 0)
        neg_count = sum(1 for x in test_data[i] if x < 0)
        expected = f"pos:{pos_count} neg:{neg_count}"
        assert line == expected, f"Line {i+1} count mismatch"


@test("awk for loop and string manipulation")
def test_awk_for_loop(env=clean_env):
    """Test AWK for loop with string manipulation"""
    # Reverse each word character by character - converted to single line
    result = pz("printf 'hello\\nworld\\nawk\\n' | awk '{ rev=\"\"; for(i=length($0); i>=1; i--) rev=rev substr($0,i,1); print rev }'")

    assert len(result) == 3, f"Should process 3 input lines, got {len(result)}"
    assert result[0] == "olleh", "Reverse of 'hello' should be 'olleh'"
    assert result[1] == "dlrow", "Reverse of 'world' should be 'dlrow'"
    assert result[2] == "kwa", "Reverse of 'awk' should be 'kwa'"

    # Verify reversals are correct
    original_words = ["hello", "world", "awk"]
    for i, reversed_word in enumerate(result):
        expected = original_words[i][::-1]
        assert reversed_word == expected, f"Reverse of '{original_words[i]}' should be '{expected}'"


@test("awk BEGIN and END blocks with counters")
def test_awk_begin_end_blocks(env=clean_env):
    """Test AWK BEGIN and END blocks with counting"""
    # Count words and lines - converted to single line
    result = pz("printf 'first line here\\nsecond line with more words\\nthird\\nfinal line\\n' | awk 'BEGIN { print \"Starting count...\" } { words += NF; lines++ } END { print \"Lines:\", lines, \"Words:\", words }'")

    assert len(result) == 2, f"Should have BEGIN message and END summary, got {len(result)} lines"
    assert result[0] == "Starting count...", "Should start with BEGIN message"
    assert result[1] == "Lines: 4 Words: 11", "Should count 4 lines and 11 words"

    # Verify the count logic matches actual input
    input_lines = ["first line here", "second line with more words", "third", "final line"]
    expected_lines = len(input_lines)
    expected_words = sum(len(line.split()) for line in input_lines)

    summary_parts = result[1].split()
    actual_lines = int(summary_parts[1])
    actual_words = int(summary_parts[3])

    assert actual_lines == expected_lines, f"Line count should be {expected_lines}"
    assert actual_words == expected_words, f"Word count should be {expected_words}"


@test("awk case conversion functions")
def test_awk_case_conversion(env=clean_env):
    """Test AWK toupper and tolower functions"""
    # Convert to upper and lower case
    result = pz("printf 'Hello World\\nTEST String\\nMiXeD cAsE\\n' | awk '{print toupper($0), \"|\", tolower($0)}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "HELLO WORLD | hello world", "Case conversion of 'Hello World'"
    assert result[1] == "TEST STRING | test string", "Case conversion of 'TEST String'"
    assert result[2] == "MIXED CASE | mixed case", "Case conversion of 'MiXeD cAsE'"

    # Verify conversions
    for line in result:
        upper, lower = line.split(" | ")
        assert upper.isupper(), f"First part should be uppercase: {upper}"
        assert lower.islower(), f"Second part should be lowercase: {lower}"
        assert upper.lower() == lower, "Upper and lower should match when normalized"


@test("awk split function with array processing")
def test_awk_split_function(env=clean_env):
    """Test AWK split function and array processing"""
    # Split on commas and print in reverse order - converted to single line
    result = pz("printf 'apple,banana,cherry\\nred,green,blue\\none,two,three,four\\n' | awk '{ n=split($0,arr,\",\"); for(i=n;i>=1;i--) printf \"%s%s\", arr[i], (i>1?\" \":\"\\n\") }'")

    assert len(result) == 3, f"Should process 3 input lines, got {len(result)}"
    assert result[0] == "cherry banana apple", "Reverse comma-separated list"
    assert result[1] == "blue green red", "Reverse comma-separated list"
    assert result[2] == "four three two one", "Reverse comma-separated list"

    # Verify reversal logic
    original_data = ["apple,banana,cherry", "red,green,blue", "one,two,three,four"]
    for i, reversed_line in enumerate(result):
        original_items = original_data[i].split(",")
        expected_reversed = " ".join(reversed(original_items))
        assert reversed_line == expected_reversed, f"Incorrect reversal for line {i+1}"


@test("awk field-specific pattern matching")
def test_awk_field_pattern_matching(env=clean_env):
    """Test AWK pattern matching on specific fields"""
    # Match lines where second field contains 'ing'
    result = pz("printf 'good morning sunshine\\nbad evening rain\\nnice running weather\\nold sitting position\\n' | awk '$2 ~ /ing/'")

    assert len(result) == 4, f"Should match 4 lines with 'ing' in second field, got {len(result)}"
    assert "good morning sunshine" in result, "Should match 'morning'"
    assert "bad evening rain" in result, "Should match 'evening'"
    assert "nice running weather" in result, "Should match 'running'"
    assert "old sitting position" in result, "Should match 'sitting'"

    # Verify each matched line has 'ing' in the second field
    for line in result:
        second_field = line.split()[1]
        assert "ing" in second_field, f"Second field should contain 'ing': {second_field}"


@test("awk POSIX word boundary workaround")
def test_awk_posix_word_boundaries(env=clean_env):
    """Test AWK word boundary matching using POSIX-compatible approach"""
    # POSIX AWK doesn't support \< \> word boundaries, so we use space/start/end matching
    # Match ' is ' as a complete word (with spaces around it, or at start/end of line)
    result = pz("printf 'this is test\\nthisis not\\nis this it\\nwhat is happening\\nmisunderstand this\\n' | awk '{ if ($0 ~ /^is / || $0 ~ / is / || $0 ~ / is$/) { gsub(/^is /, \"was \"); gsub(/ is /, \" was \"); gsub(/ is$/, \" was\") } print }'")

    assert len(result) == 5, f"Should process 5 lines, got {len(result)}"
    assert result[0] == "this was test", "'is' replaced in 'this is test'"
    assert result[1] == "thisis not", "No change in 'thisis not' (not a word)"
    assert result[2] == "was this it", "'is' at start replaced"
    assert result[3] == "what was happening", "'is' in middle replaced"
    assert result[4] == "misunderstand this", "No change (no word 'is')"

    # Verify word boundary behavior
    for i, line in enumerate(result):
        if i in [1, 4]:  # Lines that should NOT change
            assert " was " not in line and not line.startswith("was"), f"Line {i} should not have replacements"
        else:  # Lines that should change
            assert " is " not in line and not line.startswith("is "), f"Line {i} should have 'is' replaced"


@test("awk string comparison and conditionals")
def test_awk_string_comparison(env=clean_env):
    """Test AWK string comparison operators"""
    # Compare strings and print results
    result = pz("printf 'apple banana\\nzebra ant\\nsame same\\n' | awk '{if($1 < $2) print $1 \" before \" $2; else if($1 > $2) print $1 \" after \" $2; else print $1 \" equals \" $2}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "apple before banana", "apple comes before banana"
    assert result[1] == "zebra after ant", "zebra comes after ant"
    assert result[2] == "same equals same", "same equals same"

    # Verify string comparison logic
    test_pairs = [("apple", "banana"), ("zebra", "ant"), ("same", "same")]
    for i, (str1, str2) in enumerate(test_pairs):
        if str1 < str2:
            assert "before" in result[i], f"{str1} should be before {str2}"
        elif str1 > str2:
            assert "after" in result[i], f"{str1} should be after {str2}"
        else:
            assert "equals" in result[i], f"{str1} should equal {str2}"


@test("awk printf formatting")
def test_awk_printf(env=clean_env):
    """Test AWK printf formatting"""
    # Format numbers and strings
    result = pz("printf '42 3.14159 hello\\n100 2.71828 world\\n7 1.41421 test\\n' | awk '{printf \"Int: %03d, Float: %.2f, String: %-10s\\n\", $1, $2, $3}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "Int: 042, Float: 3.14, String: hello     ", "Formatting with padding"
    assert result[1] == "Int: 100, Float: 2.72, String: world     ", "Formatting with padding"
    assert result[2] == "Int: 007, Float: 1.41, String: test      ", "Formatting with padding"

    # Verify formatting
    for line in result:
        # Check integer padding (3 digits with leading zeros)
        assert line.startswith("Int: ") and line[5:8].isdigit(), "Integer should be 3 digits"
        # Check float format (2 decimal places)
        assert ", Float: " in line and "." in line.split("Float: ")[1][:4], "Float should have decimal"
        # Check string padding (10 characters, left-aligned)
        string_part = line.split("String: ")[1]
        assert len(string_part) == 10, f"String should be padded to 10 chars: '{string_part}'"


# GNU AWK Specific Tests
@test("gawk word boundaries")
@skipif_no_gawk
def test_gawk_word_boundaries(env=clean_env):
    """Test GNU AWK word boundary feature \\< and \\>"""
    # Use proper GNU AWK word boundaries
    result = pz("printf 'this is test\\nthisis not\\nis this it\\nwhat is happening\\nmisunderstand this\\n' | gawk '{gsub(/\\<is\\>/, \"was\")} 1'")

    assert len(result) == 5, f"Should process 5 lines, got {len(result)}"
    assert result[0] == "this was test", "'is' replaced in 'this is test'"
    assert result[1] == "thisis not", "No change in 'thisis not' (not a word)"
    assert result[2] == "was this it", "'is' at start replaced"
    assert result[3] == "what was happening", "'is' in middle replaced"
    assert result[4] == "misunderstand this", "No change (no word 'is')"


@test("gawk word boundaries for whole word 'the'")
@skipif_no_gawk
def test_gawk_whole_word_the(env=clean_env):
    """Test GNU AWK word boundaries to match only whole word 'the'"""
    # Using word boundaries, 'the' in 'another' won't match
    result = pz("printf 'the quick brown\\nfox jumps over\\nthe lazy dog\\nanother line\\n' | gawk '/\\<the\\>/'")

    assert len(result) == 2, f"Expected 2 lines with whole word 'the', got {len(result)}"
    assert "the quick brown" in result, "Should match line starting with 'the'"
    assert "the lazy dog" in result, "Should match line with 'the' as a word"
    assert "another line" not in result, "Should NOT match 'another' (contains 'the' but not as word)"
    assert "fox jumps over" not in result, "Should NOT match line without 'the'"


@test("gawk gensub with backreferences")
@skipif_no_gawk
def test_gawk_gensub(env=clean_env):
    """Test GNU AWK gensub function with backreferences"""
    # Use gensub to surround words starting with 'c' with brackets
    result = pz("printf 'cat and cow\\ndog and cat\\ncow cat\\n' | gawk '{print gensub(/(\\<c\\w+)/, \"[\\\\1]\", \"g\")}'")

    assert len(result) == 3, f"Expected 3 lines, got {len(result)}"
    assert result[0] == "[cat] and [cow]", "Words starting with 'c' surrounded"
    assert result[1] == "dog and [cat]", "Only 'cat' surrounded"
    assert result[2] == "[cow] [cat]", "Both words surrounded"


@test("gawk RT variable for record separator")
@skipif_no_gawk
def test_gawk_rt_variable(env=clean_env):
    """Test GNU AWK RT variable that captures the record separator"""
    # RT contains the actual characters that matched RS
    result = pz("printf 'apple,42;banana,31;cherry,90\\n' | gawk 'BEGIN{RS=\"[,;]\"} {print NR \": \" $0 \" [RT=\" RT \"]\"}' | head -5")

    assert len(result) == 5, f"Expected 5 lines, got {len(result)}"
    assert result[0] == "1: apple [RT=,]", "First field with comma separator"
    assert result[1] == "2: 42 [RT=;]", "Second field with semicolon separator"
    assert result[2] == "3: banana [RT=,]", "Third field with comma separator"
    assert result[3] == "4: 31 [RT=;]", "Fourth field with semicolon separator"
    assert result[4] == "5: cherry [RT=,]", "Fifth field with comma separator"


@test("gawk FPAT for field parsing")
@skipif_no_gawk
def test_gawk_fpat(env=clean_env):
    """Test GNU AWK FPAT variable for advanced field parsing"""
    # FPAT defines what a field is, rather than what separates fields
    # Parse CSV with quoted fields that may contain commas
    result = pz("printf '\"Smith, John\",42,\"New York\"\\n\"Doe, Jane\",28,\"Los Angeles\"\\n' | gawk 'BEGIN{FPAT=\"([^,]+)|(\\\"[^\\\"]+\\\")\"; OFS=\" | \"} {print $1, $2, $3}'")

    assert len(result) == 2, f"Expected 2 lines, got {len(result)}"
    assert result[0] == "\"Smith, John\" | 42 | \"New York\"", "Quoted fields preserved"
    assert result[1] == "\"Doe, Jane\" | 28 | \"Los Angeles\"", "Quoted fields preserved"
