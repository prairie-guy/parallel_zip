# parallel_zip

A Python wrapper for GNU parallel that provides an elegant interface for running shell commands with parameter substitution and cross-product functionality. Originally developed for bioinformatics workflows in Jupyter notebooks, `parallel_zip` makes it easy to parallelize command-line tools across multiple files, parameters, and conditions.

## Features

- **Simple parameter substitution**: Use `{param}` syntax in shell commands
- **Cross-product parameters**: Generate all combinations of multiple parameter sets
- **Broadcasting**: Single values are automatically broadcasted across multiple inputs
- **Python expression evaluation**: Embed Python expressions in command templates
- **Multi-line command support**: Commands spanning multiple lines are automatically joined
- **Dry run capability**: Preview commands before execution
- **Quick shell execution**: New `sh()` function for simple command execution
- **Leverages GNU parallel**: Inherits all the performance and reliability benefits of GNU parallel

## Installation

### Prerequisites

**GNU parallel** is required and must be installed on your system:

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install parallel
```

#### Linux (CentOS/RHEL/Fedora)
```bash
sudo yum install parallel          # CentOS/RHEL
sudo dnf install parallel          # Fedora
```

#### macOS
```bash
brew install parallel
```

#### Other platforms
See the [GNU parallel installation guide](https://www.gnu.org/software/parallel/) for your platform.

### Installing parallel_zip

This is a single-file module. The simplest way to install:

```bash
# Clone and copy the module to your project
git clone https://github.com/prairie-guy/parallel_zip.git
cp parallel_zip/parallel_zip.py /path/to/your/project/
```

#### Alternative: Install with pip 
```bash
git clone https://github.com/prairie-guy/parallel_zip.git
cd parallel_zip
pip install .
```

### Uninstalling: Uninstall with pip
```bash
pip uninstall parallel_zip
# If that fails, manually remove:
rm -rf $(pip show parallel_zip | grep Location | cut -d' ' -f2)/parallel_zip*
rm -rf parallel_zip.egg-info/  # if in project directory
```

## Quick Start

```python
from parallel_zip import parallel_zip, Cross

# Basic usage - run a command on multiple files
result = parallel_zip("wc -l {file}", file=["file1.txt", "file2.txt"])

# Cross-product parameters - run all combinations
result = parallel_zip(
    "echo 'Processing {file} with {tool}'",
    file=["data1.txt", "data2.txt"],
    cross=[{"tool": ["grep", "sed", "awk"]}]
)

# Dry run to see what commands would be executed
commands = parallel_zip(
    "hisat-3n --index {ref} -1 {r1} -2 {r2} -S {sample}.sam",
    r1=["sample1_R1.fq", "sample2_R1.fq"],
    r2=["sample1_R2.fq", "sample2_R2.fq"], 
    cross=[{"ref": ["genome1", "genome2"]}],
    dry_run=True
)

# NEW: Simple shell command execution with sh()
from parallel_zip import sh

# Quick shell commands with automatic line splitting
files = sh("ls -la")  # Returns list of lines
sizes = sh("ls -la | awk '{print $5}'")  # Note: use single quotes for $

# Get raw string output
output = sh("find . -name '*.txt'", lines=False)
```

## Basic Usage

### Parameter Substitution

Use `{parameter_name}` syntax in your command template:

```python
# Single parameter
parallel_zip("ls {directory}", directory="/tmp")

# Multiple parameters
parallel_zip(
    "head -{lines} {file} | cut -d, -f{columns}",
    file="data.csv",
    lines=10,
    columns="1,2"
)
```

### Multiple Values

Pass lists for parameters you want to iterate over:

```python
# Process multiple files
parallel_zip(
    "gzip {file}",
    file=["file1.txt", "file2.txt", "file3.txt"]
)

# Multiple files with corresponding outputs
parallel_zip(
    "convert {input} {output}",
    input=["image1.png", "image2.png"],
    output=["thumb1.jpg", "thumb2.jpg"]
)
```

### Broadcasting

Single values are automatically broadcasted across multiple inputs:

```python
parallel_zip(
    "echo 'Processing {file} with version {version}'",
    file=["file1.txt", "file2.txt", "file3.txt"],
    version="v2.0"  # Same version used for all files
)
```

### The `sh` Function - Quick Shell Commands

For simple shell command execution, use the `sh` wrapper:

```python
from parallel_zip import sh

# Basic usage - returns list of lines by default
files = sh("ls")
print(files)  # ['file1.txt', 'file2.txt', ...]

# Get raw string output
output = sh("cat file.txt", lines=False)

# Use with pipes and shell features
sh("ps aux | grep python | head -5")

# Environment variable substitution still works
home_files = sh("ls {HOME}")
```

## Advanced Features

### Cross-Product Parameters

Generate all combinations of parameter sets using the `cross` parameter:

```python
# Test all tools on all files
parallel_zip(
    "echo 'Running {tool} on {file}'",
    file=["data1.txt", "data2.txt"],
    cross=[{"tool": ["grep", "sed", "awk"]}]
)

# Multiple cross-product parameters
parallel_zip(
    "echo 'File: {file}, Tool: {tool}, Mode: {mode}'",
    file=["data.txt"],
    cross=[
        {"tool": ["hammer", "screwdriver"]},
        {"mode": ["fast", "thorough"]}
    ]
)
```

### Using the Cross Helper Function

For cleaner syntax with cross-products:

```python
from parallel_zip import parallel_zip, Cross

parallel_zip(
    "echo 'Testing {tool} on {platform} with {option}'",
    cross=Cross(
        tool=["hammer", "screwdriver", "wrench"],
        platform=["wood", "metal"],
        option=["fast", "precise"]
    )
)
```

### Python Expression Evaluation

Embed Python expressions in your commands:

```python
# Mathematical operations
parallel_zip(
    "echo 'Double of {num} is {int(num) * 2}'",
    num=[10, 20, 30]
)

# String operations
parallel_zip(
    "echo 'Uppercase: {name.upper()}'",
    name=["alice", "bob", "charlie"]
)
```

### Multi-line Commands

Commands spanning multiple lines are automatically joined with `&&`:

```python
parallel_zip("""
mkdir -p output_{sample}
hisat-3n --index {ref} -1 {r1} -2 {r2} -S output_{sample}/aligned.sam
samtools sort output_{sample}/aligned.sam -o output_{sample}/sorted.bam
""",
    sample=["sample1", "sample2"],
    ref="genome.fa",
    r1=["sample1_R1.fq", "sample2_R1.fq"],
    r2=["sample1_R2.fq", "sample2_R2.fq"]
)
```

### Important: Shell Quoting with $

When using commands that contain `$` (like awk, sed, perl, regex), use single quotes to prevent shell expansion:

```python
# CORRECT - $ is protected by single quotes
parallel_zip("awk '{print $5}' {file}", file=["data.txt"], verbose=True)
sh("grep 'end$' file.txt")  # $ as regex anchor
sh("sed 's/^$/blank/' file.txt")  # $ in sed pattern

# WRONG - $ gets expanded by shell (becomes empty)
parallel_zip('awk "{print $5}" {file}', file=["data.txt"], verbose=True)
```

This applies to any tool that uses `$` in its syntax: awk, sed, grep, perl, regex patterns, etc.

## Bioinformatics Examples

### RNA-seq Pipeline

```python
# Map RNA-seq reads to multiple reference genomes
samples = ['treated', 'control']
references = ['hg38', 'mm10']

parallel_zip("""
hisat2 --index {ref_path}/{ref} -1 {input_path}/{r1}.fq.gz -2 {input_path}/{r2}.fq.gz -S {output_path}/{sample}_{ref}.sam
""",
    r1=[f'{sample}_R1' for sample in samples],
    r2=[f'{sample}_R2' for sample in samples], 
    cross=Cross(sample=samples, ref=references),
    ref_path='~/references',
    input_path='trimmed_reads',
    output_path='alignments'
)

# For simpler cases without parallelization, you can also use:
# sh("hisat2 --index genome.fa -1 sample_R1.fq -2 sample_R2.fq -S output.sam")
```

### Variant Calling

```python
# Run variant calling with different parameters
parallel_zip("""
bcftools mpileup -f {reference} {bam} | 
bcftools call -mv -Oz -o {output_dir}/{sample}_q{quality}_d{depth}.vcf.gz
""",
    bam=["sample1.bam", "sample2.bam", "sample3.bam"],
    sample=["sample1", "sample2", "sample3"],
    cross=[
        {"quality": [20, 30]},
        {"depth": [5, 10]}
    ],
    reference="genome.fa",
    output_dir="variants"
)
```

### Quality Control

```python
# Run FastQC on multiple files with different options
parallel_zip(
    "fastqc {input} --outdir {outdir} --threads {threads} {options}",
    input=["sample1_R1.fq.gz", "sample1_R2.fq.gz", "sample2_R1.fq.gz", "sample2_R2.fq.gz"],
    cross=[{"options": ["--noextract", "--extract"]}],
    outdir="qc_results",
    threads=4
)
```

## Performance and Parallelization

`parallel_zip` leverages GNU parallel for job execution, which provides:

- **Automatic CPU detection**: By default runs as many jobs as you have CPU cores
- **Efficient job scheduling**: Optimal load balancing across available cores  
- **Memory management**: Prevents system overload
- **Output handling**: Maintains output order and prevents interleaving
- **Error handling**: Continues processing other jobs if one fails

The performance characteristics depend on GNU parallel's implementation. For CPU-bound tasks, expect near-linear speedup with the number of cores. For I/O-bound tasks, performance will depend on your storage system.

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
- `sh(command, lines=True)`: Quick shell command execution
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone or download parallel_zip.py
# Install in development mode
pip install -e /path/to/parallel_zip/directory
python -m pytest tests/  # Run tests (if available)
```

### Running Tests

```bash
# Run the comprehensive test suite
bash parallel_zip_test.sh

# Or run individual tests
python -c "from parallel_zip import parallel_zip; print('Import successful')"
```

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

**Q: When should I use sh() vs parallel_zip()?**
A: Use `sh()` for simple commands or when you need the output for further Python processing. Use `parallel_zip()` when you need parallelization, parameter substitution across multiple values, or cross-products.

## Changelog

### v1.1.0 (Current)
- Added `sh()` function for simple shell command execution
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
