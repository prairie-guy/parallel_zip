# parallel_zip

**A Python wrapper for GNU parallel that naturally embeds shell code into Python scripts or Jupyter notebooks (no delimiter hell). Features parameter substitution, environment substitution, and cross-product generation to eliminate shell loops. Ideal for seamlessly integrating third-party Unix programs into Python environments for bioinformatics and data science pipelines.**

**Author**: C. Bryan Daniels (quendor_at_nandor.net)

## See It In Action

**Before** - Python script depending upon  Juptyer magic `!` command or else  `subprocess` function in Python
``` python
%%time

in_paths = ['dedup_MT', 'dedup_2', 'dedup_human']
out_paths = ['conv_unconv3n_MT', 'conv_unconv3n_2', 'conv_unconv3n_human']
samples = ['E1', 'E2', 'E3', 'Z1', 'Z2', 'Z3', 'U1', 'U2', 'U3']
threads = 6

for in_path, out_path in zip(in_paths, out_paths):
    ref = str(in_path).split('_')[-1]
    for sample in samples:
        !samtools view -e "rlen<100000" -h {fname(in_path,sample,'bam')} |\
        hisat-3n-table -p {threads}--unique-only --alignments - --ref {get_ref(ref,'fa')} --output-name /dev/stdout --base-change C,T|\
        bgzip -@ {nc} -c > {fname(out_path,sample,'tsv.gz')}
```

``` markdown
CPU times: user 951 ms, sys: 113 ms, total: 1.06 s
Wall time: 6h 16m 42s
```

**After** - `parallel_zip` using native shell code, portable to Jupyter or Python, with parallelism built-in for speed 
``` python
%%time
from parallel_zip import parallel_zip, Cross

parallel_zip(
    """
    samtools view -e "rlen<100000" -h {in_path}/{sample}.bam | \
    hisat-3n-table -p 6 --unique-only --alignments - --ref {get_ref(ref,'fa')} --output-name /dev/stdout --base-change C,T | \
    bgzip -@ 6 -c > {out_path}/{sample}.tsv.gz
    """, 
        in_paths = ['dedup_MT', 'dedup_2', 'dedup_human']  , 
        out_paths= ['conv_unconv3n_MT', 'conv_unconv3n_2', 'conv_unconv3n_human']
        cross=Cross(sample=['E1', 'E2', 'E3', 'Z1', 'Z2', 'Z3', 'U1', 'U2', 'U3']))
```

``` markdown
CPU times: user 103 ms, sys: 12.4 ms, total: 116 ms
Wall time: 41min 27s
```



**Real output example** - See exactly what gets executed:
```python
parallel_zip("""
    hisat-3n --index {ref} -1 reads/{sample}_R1.fq.gz -2 reads/{sample}_R2.fq.gz -S alignments/{sample}_{ref}.sam
""",
    cross=Cross(sample=['treated', 'control'], ref=['hg38', 'mm10']),
    dry_run=True)
Out[23]: 
["hisat-3n --index hg38 -1 reads/treated_R1.fq.gz -2 reads/treated_R2.fq.gz -S alignments/treated_hg38.sam",
 "hisat-3n --index mm10 -1 reads/treated_R1.fq.gz -2 reads/treated_R2.fq.gz -S alignments/treated_mm10.sam",
 "hisat-3n --index hg38 -1 reads/control_R1.fq.gz -2 reads/control_R2.fq.gz -S alignments/control_hg38.sam",
 "hisat-3n --index mm10 -1 reads/control_R1.fq.gz -2 reads/control_R2.fq.gz -S alignments/control_mm10.sam"]
```

**Quick shell commands** with the `pz()` function:
```python
from parallel_zip import pz

# Get file sizes
pz("ls -la *.txt")
# Returns: ['total 48', '-rw-r--r-- 1 user staff 156 Jan 15 data1.txt', ...]

# Quick data inspection
pz("head -3 data.csv")
# Returns: ['id,name,value', '1,apple,3.5', '2,banana,2.7']

# Complex shell command with natural syntax (no delimiting hell)
pz("""ls -l {os.getcwd()} | cut -f1 -d' ' | sed s/--// | sed s/^-// | awk '$1 ~ /x/ {split($1, parts, "-"); print parts[1]}' """)
# Returns: ['drwxrwxr', 'drwxrwxr', 'drwxrwxr', 'drwxrwxr']
```

## Why Use parallel_zip?

### **Best of Both Worlds**
- **Easy shell command execution from Python**: Run shell commands with near-native syntax from within Python
- **True Python integration**: Pass Python expressions, variables, and environment directly into command templates
- **Multi-line bash script support**: Write complex workflows as readable templates with automatic line-by-line execution
- **Built-in parallelism**: Inherits GNU parallel's battle-tested performance, load balancing, and resource management

### **Quick Shell Power with `pz()`**
- **One-liner shell commands**: Execute any shell command and get clean results with `pz("command")`
- **Automatic output formatting**: Returns lists of lines by default, or raw strings when needed
- **Useful when loops and passing variables are not required**: Perfect for simple commands and quick data inspection
- **No ceremony required**: Direct shell execution without parameter setup or parallel processing overhead

### **Replace Complexity with Elegance**
- **No more nested loops**: Transform complex for-loop combinations into single, readable function calls
- **Clean parameter substitution**: Use intuitive `{param}` syntax instead of error-prone string concatenation
- **Eliminate boilerplate**: Skip tedious setup code for parallel execution and parameter management

### **Cross-Product Power Without Pain**
- **Automatic parameter combinations**: Generate all combinations of multiple parameter sets instantly
- **No manual combinatorics**: Skip the nested loop math - just specify what parameters to vary
- **Broadcasting magic**: Single values automatically expand across parameter lists when needed

### **Built for Exploration and Development**
- **Dry run everything**: See exactly what commands will execute before running them
- **Flexible output control**: Get results as strings, lists, or run silently as your workflow needs
- **Interactive-friendly**: Perfect for Jupyter notebooks, iterative analysis, and experimental workflows
- **Immediate feedback**: Quick `pz()` commands for one-off tasks and data exploration

### **Handles the Hard Stuff**
- **Shell quoting protection**: Proper handling of `$`, quotes, and special characters that break naive approaches
- **Smart error handling**: Choose strict mode for critical pipelines or continue-on-failure for exploratory work
- **Python expression evaluation**: Embed calculations and string manipulation directly in command templates

### **More Intuitive Than Alternatives**
- **vs. Raw GNU parallel**: No complex option syntax, confusing escape sequences, or command-line juggling
- **vs. Python multiprocessing**: Purpose-built for shell commands with parameter substitution, not generic Python functions
- **vs. Shell scripting**: Get parameter combinations and parallel execution without variable explosion or syntax nightmares

Perfect for bioinformatics pipelines, data processing workflows, file operations, and any scenario where you need the power of shell tools with the convenience of Python.

## Quick Start That Actually Works

### Installation

#### Prerequisites
**GNU parallel** is required and must be installed on your system:

**Linux (Ubuntu/Debian)**
```bash
sudo apt-get install parallel
```

**Linux (CentOS/RHEL/Fedora)**
```bash
sudo yum install parallel          # CentOS/RHEL
sudo dnf install parallel          # Fedora
```

**macOS**
```bash
brew install parallel
```

#### Installing parallel_zip
This is a single-file module. The simplest way to install:

```bash
# Clone and copy the module to your project
git clone https://github.com/prairie-guy/parallel_zip.git
cp parallel_zip/parallel_zip.py /path/to/your/project/
```

**Optional: Install Locally with pip**
```bash
git clone https://github.com/prairie-guy/parallel_zip.git
cd parallel_zip
pip install .
```

### Your First Command

```python
from parallel_zip import parallel_zip

# Process multiple files in parallel
parallel_zip("""wc -l sample_data/{file}""", 
    file=["data1.txt", "data2.txt", "data3.txt"],
    verbose=True, lines=True)
# Returns:
['2 sample_data/data1.txt',
 '14 sample_data/data2.txt',
 '45 sample_data/data3.txt']

# Same files, different parameters - extract different numbers of lines
parallel_zip("""head -{num_lines} sample_data/{file}""",
    file=["data1.txt", "data2.txt"],
    num_lines=[2, 5],
    verbose=True, lines=True)
# Returns:
['Sample data line one',
 'This is line two',
 'Line 1: Introduction',
 'Line 2: Methods overview',
 'Line 3: Data collection started',
 'Line 4: Quality control passed',
 'Line 5: Processing pipeline initialized  ']
```

### Your First Cross Product

```python
from parallel_zip import parallel_zip, Cross

# Test every file with every search pattern - 6 total combinations
parallel_zip("""grep -c '{pattern}' sample_data/{file}""",
    file=["data1.txt", "data2.txt"],
    cross=Cross(pattern=["line", "data", "Line"]),
    verbose=True, lines=True)
# Returns: ['3', '1', '0', '1', '0', '15']
```

### Quick Shell Commands with `pz()`

```python
from parallel_zip import pz

# One-liner for immediate results
pz("ls sample_data")
# Returns:
['data1.txt',
 'data2.txt',
 'data3.txt',
 'data.csv',
 'numbers.txt',
 'sample1.txt',
 'sample2.txt',
 'server_logs.txt']

pz("wc -w sample_data/*.txt")
# Returns:
['  11 sample_data/data1.txt',
 '  70 sample_data/data2.txt',
 ' 148 sample_data/data3.txt',
 '   8 sample_data/numbers.txt',
 '  16 sample_data/sample1.txt',
 '  16 sample_data/sample2.txt',
 '  31 sample_data/server_logs.txt',
 ' 300 total']

pz("pwd")
# Returns: ['/home/quendor/stuff/parallel_zip']
```

## Core Concepts with Real Examples

### Parameter Substitution

The heart of `parallel_zip` is intuitive parameter substitution using `{parameter}` syntax in command templates.

**Warning**: The following parameter names are reserved and should not be used as named parameters to `parallel_zip`: `command`, `cross`, `verbose`, `lines`, `dry_run`, `strict`, `java_memory`. This is a known issue that will be fixed in a future version.

#### Basic Substitution
```python
# Single parameter
parallel_zip("""cat sample_data/{filename}""", filename="data1.txt", verbose=True, lines=True)
# Returns: ['Sample data line one', 'This is line two', 'Final line three']

# Multiple parameters
parallel_zip("""head -{num} sample_data/{file} | tail -{last}""",
    file="data2.txt", num=10, last=3, verbose=True, lines=True)
# Returns: 
['Line 8: Statistical analysis begun',
 'Line 9: Results compilation phase',
 'Line 10: Visualization generated']
```

#### List Parameters - Zipped Together
```python
# Parameters are zipped together (like Python's zip function)
parallel_zip("""echo 'File {file} has {line_count} lines'""",
    file=["data1.txt", "data2.txt", "data3.txt"],
    line_count=[3, 15, 42], verbose=True, lines=True)
# Returns:
['File data1.txt has 3 lines',
 'File data2.txt has 15 lines',
 'File data3.txt has 42 lines']

# Real file processing - multi-step workflow
parallel_zip("""
    wc -w sample_data/{input} > sample_data/{output}
    cat sample_data/{output}
    rm sample_data/{output}
""",
    input=["data1.txt", "data2.txt"],
    output=["count1.txt", "count2.txt"],
    verbose=True, lines=True)
# Returns: ['11 sample_data/data1.txt', '70 sample_data/data2.txt']
```

#### Broadcasting - Single Values Expand
```python
# Single values automatically broadcast to match list length
parallel_zip("""grep '{pattern}' sample_data/{file}""",
    file=["data1.txt", "data2.txt", "server_logs.txt"],
    pattern="line", dry_run=True)
# Returns:
["grep 'line' sample_data/data1.txt",
 "grep 'line' sample_data/data2.txt",
 "grep 'line' sample_data/server_logs.txt"]
```

#### Python Expression Evaluation
```python
# Embed Python expressions directly in commands
parallel_zip("""echo 'File {file} - uppercase: {file.upper()}'""",
    file=["data1.txt", "sample1.txt"], verbose=True, lines=True)
# Returns:
['File data1.txt - uppercase: DATA1.TXT',
 'File sample1.txt - uppercase: SAMPLE1.TXT']

# Mathematical operations
parallel_zip("""echo 'Number {num} doubled is {int(num) * 2}'""",
    num=[5, 10, 15], verbose=True, lines=True)
# Returns:
['Number 5 doubled is 10',
 'Number 10 doubled is 20',
 'Number 15 doubled is 30']

# Access Python environment
import os
parallel_zip("""echo 'Working in {os.getcwd()}/sample_data'""", verbose=True, lines=True)
# Returns: ['Working in /home/quendor/stuff/parallel_zip/sample_data']
```

#### Literal Braces with {{ }}

When you need literal curly braces in your output (for JSON, shell scripts, or code generation), use `{{ }}` to prevent them from being interpreted as parameter placeholders.

```python
# Generate valid JSON with literal braces
parallel_zip("""echo '{file}: {{"{key}": "{value}"}}' > {file}.json
            cat {file}.json
            rm {file}.json""",
    file=["config", "settings", "params"],
    key=["version", "mode", "level"],
    value=["1.0", "production", "debug"],
    verbose=True, lines=True)
# Returns:
['config: {"version": "1.0"}',
 'settings: {"mode": "production"}',
 'params: {"level": "debug"}']

# Generate shell scripts with literal braces for command grouping
parallel_zip("""echo 'if [ -f {file} ]; then {{ echo "Found {file}"; process_{action}; }}' > check_{file}.sh
            echo '> cat' check_{file}.sh  && cat check_{file}.sh
            rm check_{file}.sh
            """,
    file=["data1.txt", "data2.txt"], 
    action=["validate", "transform"],
    verbose=True, lines=True)
# Returns:
['> cat check_data1.txt.sh',
 'if [ -f data1.txt ]; then { echo "Found data1.txt"; process_validate; }',
 '> cat check_data2.txt.sh',
 'if [ -f data2.txt ]; then { echo "Found data2.txt"; process_transform; }']
```

**Key Points:**
- `{{` becomes `{` in the output
- `}}` becomes `}` in the output
- Parameters like `{file}` inside `{{ }}` are still substituted
- Perfect for generating JSON, shell scripts, or any text that needs literal braces

### Cross Products Made Simple

Cross products let you run every combination of parameters automatically. Use the `Cross()` helper for clean, readable syntax.

#### Basic Cross Product
```python
# Run every file with every pattern - 6 total combinations
parallel_zip("""grep -c '{pattern}' sample_data/{file}""",
    file=["data1.txt", "data2.txt"],
    cross=Cross(pattern=["line", "data", "INFO"]),
    verbose=True, lines=True)
# Returns: ['3', '1', '0', '1', '0', '0']
# (line in data1, data in data1, INFO in data1, line in data2, data in data2, INFO in data2)
```

#### Multiple Cross Parameters
```python
# Every file × every tool × every option = 8 combinations
parallel_zip("""echo 'Processing {file} with {tool} using {option}'""",
    file=["data1.txt"],
    cross=Cross(
        tool=["grep", "awk"],
        option=["fast", "thorough", "detailed", "quick"]
    ),
    verbose=True, lines=True)
# Returns:
['Processing data1.txt with grep using fast',
 'Processing data1.txt with grep using thorough', 
 'Processing data1.txt with grep using detailed',
 'Processing data1.txt with grep using quick',
 'Processing data1.txt with awk using fast',
 'Processing data1.txt with awk using thorough',
 'Processing data1.txt with awk using detailed', 
 'Processing data1.txt with awk using quick']
```

#### Cross Products with Zipped Parameters
```python
# Zipped parameters stay together, cross parameters expand
parallel_zip("""echo 'File {input} -> {output}, method: {method}, quality: {quality}'""",
    input=["data1.txt", "data2.txt"],           # Zipped together
    output=["result1.txt", "result2.txt"],      # Zipped together  
    cross=Cross(
        method=["standard", "advanced"],         # Cross product
        quality=["low", "high"]                  # Cross product
    ),
    verbose=True, lines=True)
# Returns: 2 file pairs × 2 methods × 2 qualities = 8 combinations
['File data1.txt -> result1.txt, method: standard, quality: low',
 'File data1.txt -> result1.txt, method: standard, quality: high',
 'File data1.txt -> result1.txt, method: advanced, quality: low', 
 'File data1.txt -> result1.txt, method: advanced, quality: high',
 'File data2.txt -> result2.txt, method: standard, quality: low',
 'File data2.txt -> result2.txt, method: standard, quality: high',
 'File data2.txt -> result2.txt, method: advanced, quality: low',
 'File data2.txt -> result2.txt, method: advanced, quality: high']
```

#### Cross vs. List Format
```python
# These are equivalent - use Cross() for readability
# Cross() format (recommended)
parallel_zip("""echo '{tool} on {file}'""",
    file=["data1.txt"],
    cross=Cross(tool=["grep", "awk"]),
    verbose=True, lines=True)
# Returns: ['grep on data1.txt', 'awk on data1.txt']

# List format (also works)
parallel_zip("""echo '{tool} on {file}'""", 
    file=["data1.txt"],
    cross=[{"tool": ["grep", "awk"]}],
    verbose=True, lines=True)
# Returns: ['grep on data1.txt', 'awk on data1.txt']
```

#### Three-Dimensional Cross Products
```python
# Every combination across 3 parameter sets
parallel_zip("""echo 'Processing {file} with {tool} at {quality} quality and {mode} mode'""",
    file=["data1.txt"],
    cross=Cross(
        tool=["grep", "awk"],
        quality=["low", "high"],
        mode=["fast", "thorough"]
    ),
    dry_run=True)
# Returns: 8 combinations (2×2×2)
["echo 'Processing data1.txt with grep at low quality and fast mode'",
 "echo 'Processing data1.txt with grep at low quality and thorough mode'",
 "echo 'Processing data1.txt with grep at high quality and fast mode'",
 "echo 'Processing data1.txt with grep at high quality and thorough mode'",
 "echo 'Processing data1.txt with awk at low quality and fast mode'",
 "echo 'Processing data1.txt with awk at low quality and thorough mode'",
 "echo 'Processing data1.txt with awk at high quality and fast mode'",
 "echo 'Processing data1.txt with awk at high quality and thorough mode'"]
```


### The `pz()` Function - Quick Shell Power

When you need quick shell commands without parameter substitution or parallelization, `pz()` is your friend. Perfect for data exploration, one-off commands, and simple shell operations.

#### Basic Usage
```python
from parallel_zip import pz

# Simple file listing
pz("ls sample_data")
# Returns:
['data1.txt', 'data2.txt', 'data3.txt', 'data.csv', 'numbers.txt', 'sample1.txt', 'sample2.txt', 'server_logs.txt']

# Get current directory
pz("pwd")
# Returns: ['/home/quendor/stuff/parallel_zip']

# Quick file inspection
pz("head -3 sample_data/data2.txt")
# Returns:
['Line 1: Introduction', 'Line 2: Methods overview', 'Line 3: Data collection started']
```

#### Text Processing with AWK
```python
# Extract specific fields
pz("""awk '{print $1, $3}' sample_data/sample1.txt""")
# Returns:
['product_1 299.99', 'product_2 19.95', 'product_3 149.50', 'product_4 79.99']

# Count and sum - use single quotes to protect $ from shell expansion
pz("""awk '{sum += $3; count++} END {print "Total items:", count, "Sum:", sum}' sample_data/sample1.txt""")
# Returns: ['Total items: 4 Sum: 549.43']

# Pattern matching with AWK
pz("""awk '/product_[13]/ {print $2, $4}' sample_data/sample1.txt""")
# Returns: ['electronics in_stock', 'electronics in_stock']
```

#### Data Analysis Pipelines
```python
# Complex shell pipeline in one line
pz("""sort sample_data/numbers.txt | head -3""")
# Returns: ['10', '18', '2']

# Multiple command chaining
pz("""cat sample_data/numbers.txt | sort -n | tail -3""")
# Returns: ['29', '33', '41']

# String manipulation
pz("""echo 'hello world' | tr 'a-z' 'A-Z'""")
# Returns: ['HELLO WORLD']
```

#### Python Expression Integration
```python
# Access Python environment in shell commands
import os
pz("""ls -la {os.getcwd()}/sample_data | head -5""")
# Returns:
['total 40', 'drwxrwxr-x 2 quendor quendor 4096 Jun 26 15:37 .', 'drwxrwxr-x 8 quendor quendor 4096 Jun 26 14:54 ..', '-rw-r--r-- 1 quendor quendor   54 Jun 26 14:55 data1.txt', '-rw-r--r-- 1 quendor quendor  501 Jun 26 14:55 data2.txt']

# Mathematical calculations
pz("""echo 'Result: {2 + 3 * 4}'""")
# Returns: ['Result: 14']
```

#### Output Format Control
```python
# Get output as list of lines (default)
result_lines = pz("""cat sample_data/data1.txt""")
# Returns: ['Sample data line one', 'This is line two', 'Final line three']

# Get output as single string
result_string = pz("""cat sample_data/data1.txt""", lines=False)
# Returns: 'Sample data line one\nThis is line two\nFinal line three'
```

#### Advanced Text Processing
```python
# CSV analysis with AWK
pz("""awk -F',' 'NR>1 {print $2, $3}' sample_data/data.csv""")
# Returns:
['apple 3.5', 'banana 2.7', 'carrot 1.8', 'cherry 4.2', 'potato 2.1']

# Log file analysis
pz("""awk '/ERROR/ {print "ERROR at", $2 ":", substr($0, index($0,$4))}' sample_data/server_logs.txt""")
# Returns: ['ERROR at 09:00:32: File not found: config.xml']

# Field counting and statistics
pz("""awk '{print NF, $0}' sample_data/sample2.txt""")
# Returns:
['4 order_1001 2024-01-15 customer_a 450.00', '4 order_1002 2024-01-15 customer_b 125.75', '4 order_1003 2024-01-16 customer_c 299.99', '4 order_1004 2024-01-16 customer_a 89.50']
```

#### When to Use `pz()` vs `parallel_zip()`
```python
# Use pz() for simple, one-off commands
file_count = pz("""ls sample_data | wc -l""")
disk_usage = pz("""du -sh sample_data""")
current_user = pz("""whoami""")

# Use parallel_zip() for parameter substitution and parallelization
parallel_zip("""wc -l sample_data/{file}""", 
    file=["data1.txt", "data2.txt", "data3.txt"])
```

**Key Points:**
- Use `pz()` when you don't need parameter substitution or parallel execution
- Perfect for quick data exploration and shell command testing
- Automatically returns clean output as list of lines
- Supports Python expressions for dynamic shell commands
- Great for AWK, sed, grep, and other text processing tools

## Real-World Workflows

Move beyond basic examples to see how `parallel_zip` handles more compplex processing tasks.

#### Batch File Operations
```python
# Check which files exist before processing
parallel_zip("""test -f sample_data/{file} && echo '{file} exists' || echo '{file} missing'""",
    file=["data1.txt", "missing.txt", "data2.txt"],
    verbose=True, lines=True)
# Returns:
['data1.txt exists', 'missing.txt missing', 'data2.txt exists']

# Process only existing files with error handling
parallel_zip("""[ -f sample_data/{file} ] && wc -l sample_data/{file} || echo 'SKIP: {file}'""",
    file=["data1.txt", "missing.txt", "data3.txt"],
    verbose=True, lines=True)
# Returns:
['2 sample_data/data1.txt', 'SKIP: missing.txt', '45 sample_data/data3.txt']
```

#### File Analysis and Comparison
```python
# Get file statistics
parallel_zip("""echo '{file}:' && wc -l sample_data/{file} && wc -c sample_data/{file}""",
    file=["data1.txt", "data2.txt"],
    verbose=True, lines=True)
# Returns:
['data1.txt:',
 '3 sample_data/data1.txt',
 '55 sample_data/data1.txt',
 'data2.txt:',
 '15 sample_data/data2.txt',
 '502 sample_data/data2.txt']

# Find patterns across multiple files
parallel_zip("""echo 'File = {file}:' && grep -n '{pattern}' sample_data/{file} || echo 'No matches'""",
    file=["data1.txt", "data2.txt", "server_logs.txt"],
    cross=Cross(pattern=["line", "ERROR", "data"]),
    verbose=True, lines=True)
# Returns:
['File = data1.txt:',
 '1:Sample data line one',
 '2:This is line two',
 '3:Final line three',
 'File = data1.txt:',
 'No matches',
 'File = data1.txt:',
 '1:Sample data line one',
 'File = data2.txt:',
 '5:Line 5: Processing pipeline initialized  ',
 'File = data2.txt:',
 'No matches',
 'File = data2.txt:',
 'No matches',
 'File = server_logs.txt:',
 'No matches',
 'File = server_logs.txt:',
 '3:2024-01-15 09:00:32 ERROR File not found: config.xml',
 'File = server_logs.txt:',
 'No matches']
```

#### Data Extraction and Transformation
```python
# Extract and reformat CSV data
pz("""awk -F',' 'NR>1 {printf "%-10s %8.2f %s\\n", $2, $3, $4}' sample_data/data.csv""")
# Returns:
['apple          3.50 fruit',
 'banana         2.70 fruit', 
 'carrot         1.80 vegetable',
 'cherry         4.20 fruit',
 'potato         2.10 vegetable']

# Calculate statistics across categories
pz("""awk -F',' 'NR>1 {sum[$4] += $3; count[$4]++} END {for(cat in sum) printf "%s: avg=%.2f (n=%d)\\n", cat, sum[cat]/count[cat], count[cat]}' sample_data/data.csv""")
# Returns:
['vegetable: avg=1.95 (n=2)', 'fruit: avg=3.47 (n=3)']
```

#### Log File Analysis
```python
# Analyze server logs by time patterns
logs = pz("""awk '{print $2}' sample_data/server_logs.txt | sort | uniq -c""")
[l.strip() for l in logs]
# Returns:
['1 09:00:01', '1 09:00:15', '1 09:00:32', '1 09:01:05', '1 09:01:45']

# Extract errors with context
pz("""awk '/ERROR/ {print "ERROR at", $2 ":", substr($0, index($0,$4))}' sample_data/server_logs.txt""")
# Returns: ['ERROR at 09:00:32: File not found: config.xml']

# Generate summary report with single-line AWK
pz("""awk '{level = $3; count[level]++; if (level == "ERROR") errors[NR] = $0} END {print "=== LOG SUMMARY ==="; for (l in count) print l ": " count[l]; print "\\n=== ERROR DETAILS ==="; for (e in errors) print errors[e]}' sample_data/server_logs.txt""")
# Returns:
['=== LOG SUMMARY ===',
 'WARNING: 1',
 'ERROR: 1', 
 'INFO: 3',
 '',
 '=== ERROR DETAILS ===',
 '2024-01-15 09:00:32 ERROR File not found: config.xml']
```

#### Multi-File Data Processing
```python
# Process different file types with appropriate tools
parallel_zip("""echo 'Processing = {file}:' && {processor} sample_data/{file}""",
    file=["data.csv", "numbers.txt", "server_logs.txt"],
    processor=["awk -F',' 'NR>1 {print $2, $3}'", 
               "sort -n", 
               "grep ERROR"],
    verbose=True, lines=True)
# Returns:
['Processing = data.csv:',
 'apple 3.5',
 'banana 2.7',
 'carrot 1.8',
 'cherry 4.2',
 'potato 2.1',
 'Processing = numbers.txt:',
 '2',
 '7',
 '10',
 '18',
 '25',
 '29',
 '33',
 '41',
 'Processing = server_logs.txt:',
 '2024-01-15 09:00:32 ERROR File not found: config.xml']

# Cross-reference data between files
parallel_zip("""
echo "=== Analysis of {file} ==="
wc -l sample_data/{file}
echo "Top 3 lines:"
head -3 sample_data/{file}
echo "Contains 'data': $(grep -c data sample_data/{file} || echo 0)"
""",
    file=["data1.txt", "data2.txt", "sample1.txt"],
    verbose=True, lines=True)
# Returns:
['=== Analysis of data1.txt ===',
 '3 sample_data/data1.txt',
 'Top 3 lines:',
 'Sample data line one',
 'This is line two',
 'Final line three',
 "Contains 'data': 1",
 '=== Analysis of data2.txt ===',
 '15 sample_data/data2.txt',
 'Top 3 lines:',
 'Line 1: Introduction',
 'Line 2: Methods overview',
 'Line 3: Data collection started',
 "Contains 'data': 0",
 '0',
 '=== Analysis of sample1.txt ===',
 '4 sample_data/sample1.txt',
 'Top 3 lines:',
 'product_1 electronics 299.99 in_stock',
 'product_2 books 19.95 out_of_stock',
 'product_3 electronics 149.50 in_stock',
 "Contains 'data': 0",
 '0']
```


#### Performance and Quality Control
```python
# Validate data quality across files
parallel_zip("""echo 'Quality check for {file}:' && awk 'END {print "Lines:", NR, "Fields per line:", NF}' sample_data/{file}""",
    file=["data.csv", "sample1.txt", "sample2.txt"],
    verbose=True, lines=True)
# Returns:
['Quality check for data.csv:',
 'Lines: 6 Fields per line: 1',
 'Quality check for sample1.txt:',
 'Lines: 4 Fields per line: 4',
 'Quality check for sample2.txt:',
 'Lines: 4 Fields per line: 4']

# Compare processing approaches
parallel_zip("""echo '=== cat {file} | {filter.split(' ')[0]} | {extract.split(' ')[0]} ===' && cat sample_data/{file} | {filter} | {extract}""",
    file=["data2.txt"],
    cross=Cross(
        filter=["head -3", "tail -2", "grep started"],
        extract=["cut -d' ' -f2", "sed 's/^[^ ]* [^ ]* //'", "awk '{print $1, $2}'"]
    ),
    verbose=True, lines=True)
# Returns:
['=== cat data2.txt | head | cut ===',
 '1:',
 '2:',
 '3:',
 '=== cat data2.txt | head | sed ===',
 'Introduction',
 'Methods overview',
 'Data collection started',
 '=== cat data2.txt | head | awk ===',
 'Line 1:',
 'Line 2:',
 'Line 3:',
 '=== cat data2.txt | tail | cut ===',
 '14:',
 '15:',
 '=== cat data2.txt | tail | sed ===',
 'Documentation updated',
 'Analysis finished successfully',
 '=== cat data2.txt | tail | awk ===',
 'Line 14:',
 'Line 15:',
 '=== cat data2.txt | grep | cut ===',
 '3:',
 '13:',
 '=== cat data2.txt | grep | sed ===',
 'Data collection started',
 'Report generation started',
 '=== cat data2.txt | grep | awk ===',
 'Line 3:',
 'Line 13:']
```

**Key Workflow Principles:**
- **AWK on single lines**: Use semicolons (;) to separate AWK statements instead of newlines
- **Self-contained commands**: Each line in multi-line blocks must be a complete shell command
- **Validation first**: Check file existence and properties before processing
- **Error handling**: Use shell conditionals and `|| echo` for graceful failure handling
- **Quality control**: Validate data structure and content before complex operations
- **Performance awareness**: Monitor command execution time and resource usage

## Output Control & Debugging

Master the tools for previewing, controlling output, and handling errors in your `parallel_zip` workflows.

### Dry Run - Preview Before Execution

Always preview commands before running them, especially with cross products or complex parameter combinations.

```python
# See exactly what commands will be generated
parallel_zip("""echo 'Processing {file} with {tool}'""",
    file=["data1.txt", "data2.txt"],
    cross=Cross(tool=["grep", "awk"]),
    dry_run=True)
# Returns:
["echo 'Processing data1.txt with grep'",
 "echo 'Processing data1.txt with awk'", 
 "echo 'Processing data2.txt with grep'",
 "echo 'Processing data2.txt with awk'"]

# Debug complex find operations
parallel_zip("""find sample_data -name '*{pattern}*' -type f""",
    cross=Cross(pattern=["data", "sample", "server"]),
    dry_run=True)
# Returns:
["find sample_data -name '*data*' -type f",
 "find sample_data -name '*sample*' -type f", 
 "find sample_data -name '*server*' -type f"]
```

### Output Format Control

Choose the right output format for your workflow needs.

#### Silent Execution
```python
# Run commands without capturing output (fastest)
parallel_zip("""echo 'This runs silently for {file}'""",
    file=["data1.txt", "data2.txt"],
    verbose=False)
# Returns: None
```

#### String Output
```python
# Get output as single string (good for single commands)
parallel_zip("""echo 'Line 1 for {file}'; echo 'Line 2 for {file}'""",
    file=["data1.txt"],
    verbose=True, lines=False)
# Returns: 'Line 1 for data1.txt\nLine 2 for data1.txt\n'
```

#### List Output (Default for verbose=True)
```python
# Get output as list of lines (best for processing)
parallel_zip("""echo 'Line 1 for {file}'; echo 'Line 2 for {file}'""",
    file=["data1.txt"],
    verbose=True, lines=True)
# Returns: ['Line 1 for data1.txt', 'Line 2 for data1.txt']
```

### Error Handling Strategies

Control how `parallel_zip` responds to command failures.

#### Continue on Failure (Default)
```python
# Handle expected failures gracefully
parallel_zip("""grep 'nonexistent_pattern' sample_data/{file} || echo 'No match in {file}'""",
    file=["data1.txt", "data2.txt"],
    strict=False, verbose=True, lines=True)
# Returns: ['No match in data1.txt', 'No match in data2.txt']

# Commands that naturally return non-zero (like grep with no matches)
parallel_zip("""grep 'NOTFOUND' sample_data/{file}""",
    file=["data1.txt", "data2.txt"],
    strict=False, verbose=True, lines=True)
# Returns: []  # Empty results, but no error
```

#### Strict Mode - Stop on Any Failure
```python
# Stop processing if any command fails
parallel_zip("""test -f sample_data/{file} && echo '{file} exists'""",
    file=["data1.txt", "missing.txt", "data2.txt"],
    strict=True, verbose=True, lines=True)
# Output:
# parallel_zip: error with return code 1
# Error details:
# test -f sample_data/data1.txt && echo 'data1.txt exists'
# test -f sample_data/missing.txt && echo 'missing.txt exists'
# test -f sample_data/data2.txt && echo 'data2.txt exists'
# Returns: None
```

#### Mixed Success/Failure Handling
```python
# Handle mixed scenarios with proper shell logic
parallel_zip("""echo 'Testing {file}' && test -f sample_data/{file} && echo 'EXISTS' || echo 'MISSING'""",
    file=["data1.txt", "missing.txt", "data2.txt"],
    strict=False, verbose=True, lines=True)
# Returns:
['Testing data1.txt', 'EXISTS', 'Testing missing.txt', 'MISSING', 'Testing data2.txt', 'EXISTS']
```

### Debugging Techniques

#### Preview and Execute Pattern
```python
# Step 1: Preview commands
commands = parallel_zip("""find sample_data -name '*{pattern}*' -type f""",
    cross=Cross(pattern=["data", "sample", "server"]),
    dry_run=True)
print("Will execute:", commands)

# Step 2: Execute after verification
result = parallel_zip("""find sample_data -name '*{pattern}*' -type f""",
    cross=Cross(pattern=["data", "sample", "server"]),
    verbose=True, lines=True)
# Returns:
['sample_data/data3.txt', 'sample_data/data1.txt', 'sample_data/data.csv', 'sample_data/data2.txt', 'sample_data/sample1.txt', 'sample_data/sample2.txt', 'sample_data/server_logs.txt']
```

#### Verbose Pipeline Debugging
```python
# Add echo statements to track pipeline progress
parallel_zip("""echo 'Starting {operation}' && {cmd} sample_data/{file} && echo 'Completed {operation}'""",
    file=["data1.txt", "numbers.txt"],
    operation=["count_lines", "sort_content"],
    cmd=["wc -l", "sort"],
    verbose=True, lines=True)
# Returns:
['Starting count_lines', '2 sample_data/data1.txt', 'Completed count_lines', 'Starting sort_content', '10', '18', '2', '25', '29', '33', '41', '7', 'Completed sort_content']
```

#### Parameter Substitution Debugging
```python
# Debug what parameters will be substituted
parallel_zip("""echo 'File: {file}, Pattern: {pattern}, Command will be: grep {pattern} sample_data/{file}'""",
    file=["data1.txt"],
    cross=Cross(pattern=["line", "data"]),
    dry_run=True)
# Returns:
["echo 'File: data1.txt, Pattern: line, Command will be: grep line sample_data/data1.txt'",
 "echo 'File: data1.txt, Pattern: data, Command will be: grep data sample_data/data1.txt'"]
```

### Error Handling with `pz()`

```python
# pz() also supports strict mode
pz("""grep 'line' sample_data/data1.txt""", strict=False)
# Returns: ['Sample data line one', 'This is line two', 'Final line three']

pz("""grep 'NOTFOUND' sample_data/data1.txt""", strict=False)
# Returns: []  # No error, just empty results
```

### Best Practices for Debugging

1. **Always dry run first** for complex parameter combinations
2. **Use verbose mode** during development and testing
3. **Choose strict=False for exploratory work** (grep, find, test commands)
4. **Choose strict=True for critical pipelines** where failures should stop processing
5. **Add echo statements** to track progress in multi-step workflows
6. **Test with small datasets first** before scaling up
7. **Use shell error handling** (`|| echo "fallback"`) for expected failures

**Common Command Exit Codes:**
- `grep`: Returns 1 when no matches found (not an error)
- `test`/`[`: Returns 1 when condition is false (not an error)
- `find`: Returns 0 even when no files found
- `diff`: Returns 1 when files differ (not an error)

## Advanced Features

Push `parallel_zip` to its limits with complex workflows, advanced parameter handling, and sophisticated command patterns.

### Multi-line Commands

Break complex workflows into readable, multi-step processes.

```python
# Complex multi-step workflow
parallel_zip("""
echo "=== Processing {file} ==="
cp sample_data/{file} temp_{file}
wc -l temp_{file}
rm temp_{file}
echo "=== Completed {file} ==="
""",
    file=["data1.txt", "data2.txt"],
    verbose=True, lines=True)
# Returns:
['=== Processing data1.txt ===',
 '3 temp_data1.txt',
 '=== Completed data1.txt ===',
 '=== Processing data2.txt ===',
 '15 temp_data2.txt',
 '=== Completed data2.txt ===']
```

### Advanced Python Expressions

Embed sophisticated Python logic directly in command templates.

#### String and File Manipulation
```python
# Advanced string operations
parallel_zip("""echo 'File: {file}, File Name Length: {len(file)}, Extension: {file.split(".")[-1]}'""",
    file=["data1.txt", "sample2.txt", "server_logs.txt"],
    verbose=True, lines=True)
# Returns:
['File: data1.txt, File Name Length: 9, Extension: txt',
 'File: sample2.txt, File Name Length: 11, Extension: txt', 
 'File: server_logs.txt, File Name Length: 15, Extension: txt']

# String manipulation showcase
parallel_zip("""echo 'Original: {name}, Upper: {name.upper()}, Reversed: {name[::-1]}, First 3: {name[:3]}'""",
    name=["alice", "bob", "charlie"],
    verbose=True, lines=True)
# Returns:
['Original: alice, Upper: ALICE, Reversed: ecila, First 3: ali',
 'Original: bob, Upper: BOB, Reversed: bob, First 3: bob',
 'Original: charlie, Upper: CHARLIE, Reversed: eilrahc, First 3: cha']
```

#### Mathematical Expressions
```python
# Complex calculations
parallel_zip("""echo 'Number {num}: squared={int(num)**2}, factorial={int(num)*int(num)-1 if int(num)>1 else 1}'""",
    num=[3, 4, 5],
    verbose=True, lines=True)
# Returns:
['Number 3: squared=9, factorial=8',
 'Number 4: squared=16, factorial=15',
 'Number 5: squared=25, factorial=24']
```

#### Python Environment Integration
```python
# Access Python environment and modules
from parallel_zip import paralel_zip
import os
import datetime

user = os.environ.get('USER', 'unknown')
parallel_zip("""echo 'User {user} processing {file} at {datetime.datetime.now().strftime("%H:%M:%S")}'""",
    file=["data1.txt", "data2.txt"],
    user=user,
    verbose=True, lines=True)
# Returns:
['User quendor processing data1.txt at 16:16:45',
 'User quendor processing data2.txt at 16:16:45']
```

### Shell Quoting and Special Characters

Handle complex shell syntax safely and correctly.

#### Shell Quoting for AWK
```python
# Use single quotes to protect AWK syntax - no double braces needed
parallel_zip("""awk '{print $1, $3}' sample_data/{file}""",
    file=["sample1.txt", "sample2.txt"],
    verbose=True, lines=True)
# Returns:
['product_1 299.99', 'product_2 19.95', 'product_3 149.50', 'product_4 79.99', 'order_1001 customer_a', 'order_1002 customer_b', 'order_1003 customer_c', 'order_1004 customer_a']
```

#### Protecting $ in AWK and Shell
```python
# CRITICAL: Use single quotes to protect $ from shell expansion
pz("""awk '{sum += $3; count++} END {print "Total items:", count, "Sum:", sum}' sample_data/sample1.txt""")
# Returns: ['Total items: 4 Sum: 549.43']

# WRONG - $ gets expanded by shell before AWK sees it:
# pz('awk "{sum += $3; count++} END {print \"Total:\", sum}" file.txt')
```

#### Regular Expressions and Pattern Matching
```python
# Complex regex patterns with proper escaping
parallel_zip("""grep -E '{pattern}' sample_data/{file} || echo 'No matches'""",
    file=["data1.txt", "server_logs.txt"],
    cross=Cross(pattern=["^[A-Z]", "[0-9]+", "line$"]),
    verbose=True, lines=True)
# Returns:
['Sample data line one',
 'This is line two',
 'Final line three',
 'No matches',
 'No matches',
 'No matches',
 '2024-01-15 09:00:01 INFO User login successful',
 '2024-01-15 09:00:15 WARNING Database connection slow  ',
 '2024-01-15 09:00:32 ERROR File not found: config.xml',
 '2024-01-15 09:01:05 INFO Backup process started',
 '2024-01-15 09:01:45 INFO Backup process completed',
 'No matches']
```

**Advanced Best Practices:**

1. **Multi-line Commands**: Each line must be self-contained; use `&&` for dependencies
2. **AWK and $**: Always use single quotes: `awk '{print $1}'` not `awk "{print $1}"`
3. **Parameter Substitution**: Single quotes protect AWK syntax while allowing `{file}` substitution
4. **Python Expressions**: Can access any Python module imported in the calling scope
5. **Cross Products**: Scale exponentially; use `dry_run=True` to verify combinations
6. **Shell Variables**: Use shell assignment and conditionals within single-line commands
7. **Error Handling**: Combine with `|| echo "fallback"` for robust pipelines

## Troubleshooting & Best Practices

Avoid common pitfalls and optimize your `parallel_zip` workflows with these proven patterns and solutions.

### Common Pitfalls and Solutions

#### Reserved Parameter Names
```python
# WRONG - Using reserved parameter names
parallel_zip("""echo '{command}'""",
    command="test",  # 'command' is reserved!
    dry_run=True)
# This will cause unexpected behavior

# CORRECT - Use different parameter names
parallel_zip("""echo '{cmd}'""",
    cmd="test",
    dry_run=True)
```

**Reserved parameters**: `command`, `cross`, `verbose`, `lines`, `dry_run`, `strict`, `java_memory`

#### Mismatched Parameter List Lengths
```python
# WRONG - Lists of different lengths
try:
    parallel_zip("""echo '{input} -> {output}'""",
        input=["a", "b", "c"],  # Length 3
        output=["x", "y"],      # Length 2 - will fail
        dry_run=True)
except ValueError as e:
    print("Error:", e)
# Error: All named parameters must have the same length or be single values for broadcasting

# CORRECT - Use broadcasting or matching lengths
parallel_zip("""echo '{input} -> {output}'""",
    input=["a", "b", "c"],      # Length 3
    output="default",           # Single value broadcasts
    dry_run=True)
```

#### Shell Variable Expansion Issues
```python
# WRONG - Double quotes let shell expand $NF (becomes empty)
pz("""echo "Field count: $NF" """)
# Returns: ['Field count: ']

# CORRECT - Single quotes protect $ from shell expansion  
pz("""echo 'Field count: $NF'""")
# Returns: ['Field count: $NF']
```

### Architecture Guidelines

#### Choose the Right Tool
- **`pz()`**: Simple commands, one-off operations, data exploration
- **`parallel_zip()`**: Parameter substitution, multiple files, cross products
- **Raw shell**: When neither adds value

#### Parameter Design Patterns
- **Zipped parameters**: Related values that should stay together
- **Broadcast parameters**: Common values applied to all iterations  
- **Cross parameters**: Every combination needed for testing/analysis

#### Command Structure Best Practices
- **Each line self-contained**: No multi-line shell constructs
- **Use semicolons**: Separate shell statements on the same line
- **Single quotes for AWK/sed**: Protect `$` and special characters
- **Error handling**: Use `|| echo "fallback"` for expected failures

### Debugging Checklist

1. **Start with `dry_run=True`** to see generated commands
2. **Test with small datasets** before scaling up
3. **Use `verbose=True`** during development
4. **Check parameter list lengths** match or use broadcasting
5. **Verify shell quoting** for `$` and special characters
6. **Test error conditions** with missing files/tools
7. **Monitor cross product sizes** to avoid command explosion

### Performance Guidelines

- **Parallel execution scales with CPU cores** - more cores = better performance
- **I/O-bound tasks** may not see linear speedup
- **Network operations** have natural bottlenecks
- **Memory usage scales with output capturing** - use `verbose=False` for large outputs
- **Cross products grow exponentially** - 10×10×10 = 1000 commands!

**Rule of thumb**: If you find yourself writing complex shell logic or deeply nested parameters, consider breaking the problem into simpler `parallel_zip` calls or using traditional Python with subprocess for that portion.

## Dependencies

### Python Dependencies
- **Python 3.6+** (tested up to 3.12)
- Standard library only (no external Python packages required)

### System Dependencies
- **GNU parallel** (required)
- Standard Unix tools (bash, etc.)

## Options Reference

### Core Parameters
- `command`: Command template string with `{parameter}` placeholders
- `dry_run`: If `True`, return list of commands instead of executing them
- `verbose`: If `True`, print commands as they're executed
- `cross`: List of dictionaries for cross-product parameter generation

Note: As of v1.1.0, commands without parameters are supported. Running `parallel_zip("ls", verbose=True)` will execute the command once.

### Helper Functions
- `Cross(**kwargs)`: Create cross-product parameter structure
- `pz(command, lines=True)`: Quick shell command execution
- `zipper()`: Lower-level interface for more control
- `parse_command()`: Parse command templates
- `execute_command()`: Execute individual commands

## Error Handling

`parallel_zip` inherits GNU parallel's robust error handling:

- Failed commands don't stop the entire job
- Exit codes are preserved
- stderr/stdout are captured separately
- Partial results are available even if some jobs fail

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0), consistent with GNU parallel which this tool depends upon and extends.

### GNU Parallel Citation

When using `parallel_zip` for academic publications, please cite GNU parallel as requested:

```
O. Tange (2018): GNU Parallel 2018, March 2018, https://doi.org/10.5281/zenodo.1146014
```

You can also get the citation notice by running:
```bash
parallel --citation
```

## Testing

To run the test suite, first install ward:

```bash
pip install ward
```

Then run tests using:

```bash
# Run all tests
ward

# Run specific test file
ward --path test_parallel_zip.py
ward --path test_pz.py
```

Future tests will follow the naming convention `test_<module>.py`.

## FAQ

**Q: Why not just use GNU parallel directly?**
A: While GNU parallel is excellent, `parallel_zip` provides a more intuitive Python interface with parameter substitution, cross-products, and integration with Jupyter notebooks. It's designed specifically for the iterative, experimental nature of bioinformatics workflows.

**Q: Can I use this outside of bioinformatics?**
A: Absolutely! While developed for bioinformatics, `parallel_zip` works with any shell commands and is useful for data processing, file manipulation, or any scenario where you need to run commands with varying parameters.

**Q: Does this work on Windows?**
A: `parallel_zip` requires GNU parallel, which is primarily designed for Unix-like systems. It may work under WSL (Windows Subsystem for Linux) or Cygwin, but this is not officially supported.

**Q: How does this compare to Python's multiprocessing?**
A: `parallel_zip` is designed for shell command execution and provides higher-level abstractions for parameter handling. Use Python's multiprocessing for pure Python code parallelization.

**Q: Can I control the number of parallel jobs?**
A: Yes! You can set GNU parallel options by setting the `PARALLEL` environment variable or by modifying the underlying command. Full control over GNU parallel options will be added in a future version.

**Q: When should I use pz() vs parallel_zip()?**
A: Use `pz()` for simple commands or when you need the output for further Python processing. Use `parallel_zip()` when you need parallelization, parameter substitution across multiple values, or cross-products.

**Q: How do I handle AWK commands with $ variables?**
A: Always use single quotes around AWK commands: `pz("awk '{print $1}' file.txt")`. Double quotes allow shell expansion of `$` variables.

**Q: My cross product is generating too many commands, what should I do?**
A: Cross products multiply: 10×10×10 = 1000 commands! Use `dry_run=True` first to see how many will be generated. Consider breaking large cross products into smaller chunks or using broadcasting for some parameters.

## Changelog

### v1.2.0 (Current)
- Changed quick shell function from `sh()` to `pz()` for clarity
- Added dedicated test suite for `pz()` function (pz_test.sh)
- All previous v1.1.0 changes included

### v1.1.0
- Added `pz()` function for simple shell command execution
- Fixed: Commands without parameters now work (e.g., `parallel_zip("ls", verbose=True)`)
- Removed misleading "warning" messages in verbose mode
- Added comprehensive documentation about shell quoting with $
- Enhanced test suite with edge cases

### v1.0.0
- Initial release
- Core parameter substitution and cross-product functionality
- GNU parallel integration
- Comprehensive test suite
- Cross helper function

## Roadmap

- [ ] PyPI package release
- [ ] Conda-forge package
- [ ] Direct GNU parallel options control
- [ ] Progress bars and job monitoring
- [ ] Integration with Slurm and other job schedulers
- [ ] Advanced error handling and retry mechanisms

---

*Developed with ❤️ for the bioinformatics community*
