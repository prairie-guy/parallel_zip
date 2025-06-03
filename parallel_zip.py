import itertools, subprocess, re, inspect, os

def Cross(**kwargs):
    """Create a cross-product parameter structure for zipper and parallel_zip.

    This is syntactic sugar to make cross-product parameters more intuitive and readable.
    Instead of passing a list of single-key dictionaries to the 'cross' parameter,
    you can use this helper function with keyword arguments.

    Args:
        **kwargs: Keyword arguments where each key is a parameter name and each value
                 is the list of values to include in the cross product.

    Returns:
        list: A list of single-key dictionaries in the format expected by zipper and
              parallel_zip's 'cross' parameter.

    Examples:
        # Basic zipper example:
        result = zipper(
            a=["x", "y"],
            b="constant",
            cross=Cross(
                sample=["A", "B", "C"],
                mode=["fast", "thorough"]
            )
        )
        # Equivalent to:
        result = zipper(
            a=["x", "y"],
            b="constant",
            cross=[
                {"sample": ["A", "B", "C"]},
                {"mode": ["fast", "thorough"]}
            ]
        )

        # Using Cross with parallel_zip:
        commands = parallel_zip('''
        hisat-3n --index {ref} -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
        ''',
            ref='human.fa',
            R1=[f'{sample}_R1' for sample in ['U', 'E']],
            R2=[f'{sample}_R2' for sample in ['U', 'E']],
            cross=Cross(
                sample=['U', 'E'],
                in_path=["trim", "raw"],
                out_path=["map", "results"]
            ),
            dry_run=True
        )
    """
    return [{key: vals} for key, vals in kwargs.items()]

def zipper(cross=None, **named_vals):
    """Creates combinations from named values and cross products.

    This function takes named parameters and optional cross product parameters and generates
    all combinations according to specific rules. The named parameters are zipped together
    (processed in lockstep like Python's zip function), while the cross product parameters
    generate all possible combinations.

    Args:
        cross: Optional parameter for cross-product combinations. Should be either:
               - None (default): No cross product is performed
               - A single-key dict: The key-value pair is expanded as a cross product
               - A list of single-key dictionaries: Each dict is treated as a separate group
                 of values for cross product expansion

        **named_vals: Named arguments that will be zipped together (processed in lockstep).
                      All non-singleton lists must have the same length.
                      Single values or single-item lists are automatically broadcast to
                      match the length of other arguments.

    Returns:
        A list of dictionaries with string-converted values where:
        - Each dict contains one combination of values
        - Values from named_vals are processed in lockstep (like zip)
        - Values from cross are expanded as a cross product
        - All values are converted to strings
        - Each dict has the exact same keys

    Raises:
        ValueError: If named parameters contain multiple lists of different lengths
        TypeError: If cross parameter is not None, a single-key dictionary, or a list of
                  single-key dictionaries

    Examples:
        >>> zipper(a=[1, 2], b=['x', 'y'])
        [{'a': '1', 'b': 'x'}, {'a': '2', 'b': 'y'}]

        >>> zipper(a=[1, 2], b='x')
        [{'a': '1', 'b': 'x'}, {'a': '2', 'b': 'x'}]

        >>> zipper(a=[1, 2], cross=[{'sample': ['A', 'B']}])
        [{'a': '1', 'sample': 'A'}, {'a': '1', 'sample': 'B'},
         {'a': '2', 'sample': 'A'}, {'a': '2', 'sample': 'B'}]

        >>> zipper(in_path=['file1.txt', 'file2.txt'],
        ...        out_path=['out1.txt', 'out2.txt'],
        ...        cross=[{'sample': ['A', 'B', 'C']}])
        # This will create 6 combinations: 2 files × 3 samples
    """
    def isiter(values):
        try:
            iter(values)
            return not isinstance(values, str)
        except TypeError:
            return False

    def process_named_vals(named_vals):
        if not named_vals: return (), [()]
        proc = {key: list(values) if isiter(values) else [values] for key, values in named_vals.items()}
        lengths = {key: len(values) for key, values in proc.items() if len(values) > 1}
        if lengths and len(set(lengths.values())) > 1:
            raise ValueError("All named parameters must have the same length or be single values for broadcasting")
        maxlen = max(len(values) for values in proc.values())
        proc = {key: values * maxlen if len(values) == 1 and maxlen > 1 else values for key, values in proc.items()}
        keys,vals = zip(*proc.items())
        zipped = list(zip(*vals))
        return keys, zipped

    def process_cross(cross_vals):
        if cross_vals is None: return [{}]
        if isinstance(cross_vals, dict): cross_vals = [cross_vals]
        if isinstance(cross_vals, list) and all(isinstance(item, dict) for item in cross_vals):
            result = [{}]
            for cross_dict in cross_vals:
                cross_items = [{key: str(val)} for key, val in cross_dict.items()] if not isiter(list(cross_dict.values())[0]) else [{key: str(item)} for key, val in cross_dict.items() for item in val]
                result = [dict(r, **ci) for r in result for ci in cross_items]
            return result
        return [{}]


    if not named_vals and cross is None: return("Usage: zipper(name1=val1, name2=val2, ..., cross={'k':vs} | [{'k1':vs1} ...] )")
    if cross is not None:
        if isinstance(cross, dict) and len(cross) > 1:
            raise TypeError("Cross parameter as a dictionary must contain only one key. For multiple keys, use a list of single-key dictionaries: cross=[{'key1': values}, {'key2': values}]")
        elif isinstance(cross, list) and not all(isinstance(item, dict) and len(item) == 1 for item in cross):
            raise TypeError("Cross parameter as a list must contain only dictionaries with exactly one key each")
        elif not isinstance(cross, dict) and not isinstance(cross, list):
            raise TypeError("Cross parameter must be None, a dictionary, or a list of dictionaries")

    keys, zipped  = process_named_vals(named_vals)
    crossed       = process_cross(cross)
    final         = [{key: str(z[i]) for i, key in enumerate(keys)} | c for z in zipped for c in crossed]
    return final

def parse_command(command, cross=None, **named_vals):
    """Parse command templates by replacing variables in curly braces with their values.
       where, cross and **named_vals have the same form used by zipper

    Args:
        command (str): The command template string. Variables are specified using {name} syntax.
                       {val} not matched aginst a named_vals are evaluated as python code
                       Use {{text}} for literal braces in the output, useful for awk '{commands]'}
        cross (dict or list, optional): Variables to expand in a cross-product fashion.
                                       Can be a dict or a list of dicts
                                       Each value can be a single item or a list/tuple for combinations.
        **named_vals: Named variables to substitute in the template.
                     List variables will be indexed by result number.

    Returns:
        list: A list of processed command strings with all variables substituted and python code evalueated.
    """
    def eval_zippered(command, val_dict):
        """Replace {key} in command with values from val_dict and evaluate Python expressions."""
        result = command

        # First, replace {key} with values from val_dict
        for key, value in val_dict.items():
            result = result.replace(f"{{{key}}}", value)


        # Next delimit {} by protectin double braces {{}}
        protected = result.replace("{{", "___LEFTBRACE___").replace("}}", "___RIGHTBRACE___")
        pattern = r"\{([^{}]+)\}"
        matches = re.findall(pattern, protected)


        # Remaining {val} are evaluated as python code
        # Gettting  the environment for evaluation from all parent frames in the call stack
        # Variables are scoped to be closest to the caller
        current_frame = inspect.currentframe()
        all_frames = []
        frame = current_frame
        while frame.f_back is not None:
            frame = frame.f_back
            all_frames.append(frame)
            caller_globals = {}
            caller_locals = {}
        for frame in reversed(all_frames):
            caller_globals.update(frame.f_globals)
            caller_locals.update(frame.f_locals)

        # Create combined environment with val_dict values
        combined_locals = {**caller_locals, **val_dict}

        # Evaluate remaining expressions
        for expr in matches:
            try:
                value = str(eval(expr, caller_globals, combined_locals))
                protected = protected.replace(f"{{{expr}}}", value)
            except Exception:
                pass

        # Restore protected braces
        final_result = protected.replace("___LEFTBRACE___", "{").replace("___RIGHTBRACE___", "}")
        return final_result.strip()

    # Generate parameter combinations
    zippered_vals = zipper(cross=cross, **named_vals)

    # Process each combination completely (both substitution and evaluation)
    final_cmds = []
    for val_dict in zippered_vals:
        final_cmds.append(eval_zippered(command, val_dict))

    return final_cmds


def execute_command(commands, dry_run, verbose):
    """Execute commands using GNU Parallel.
    
    Args:
        commands (list): List of commands to execute in parallel.
    Returns:
        proc, str:
        {args, returncode, stdout, stderr}, processed_commnd
    """
    processed_commands = []
    for cmd in commands:
        lines = [line.strip() for line in cmd.splitlines() if line.strip()]
        if not lines:
            continue
            
        joined_lines = []
        for line in lines:
            if joined_lines and not joined_lines[-1].endswith('&&') and not line.startswith('&&'):
                joined_lines[-1] += ' && ' + line
            else:
                joined_lines.append(line)
                
        processed_command = ' '.join(joined_lines)
        processed_commands.append(processed_command)

    if dry_run: return [], processed_commands
    if verbose: proc = subprocess.run(["parallel", "--verbose", ":::", *processed_commands], capture_output=True, text=True)
    else: proc = subprocess.run(["parallel", ":::", *processed_commands], capture_output=True, text=True)
    return proc, processed_commands

def parallel_zip(command, cross=None, verbose=False, dry_run=False, java_memory=None,  **named_vals):
    """Runs commands in parallel by constructing commands from arguments.

    This function creates multiple command variations from templates and executes them in
    parallel using GNU Parallel. Command templates contain variables in {name} syntax that
    are replaced with values from named parameters and cross products. Python expressions
    in curly braces are also evaluated.

    Args:
        command (str): Command template with variables in {name} syntax.
                      Multi-line commands are automatically joined with '&&'.
                      Python expressions in {expr} are evaluated if not matching parameter names.
                      Use double braces {{text}} for literal braces in output.
        cross (dict or list, optional): Variables to expand in a cross-product fashion.
                                       Should be either:
                                       - None (default): No cross product is performed
                                       - A single-key dict: The key-value pair is expanded as a cross product
                                       - A list of single-key dictionaries: Each dict is treated as a separate
                                         group of values for cross product expansion
        verbose (bool, optional): If True, returns the stdout of the executed commands.
        dry_run (bool, optional): If True, returns the commands that would be executed without running them.
        java_memory (str, optional): Set max java memory: '4g', '8g', '16g' ...
        **named_vals: Named variables to substitute in the template.
                     List variables are processed in lockstep (like zip).
                     Single values are broadcast to match the length of lists.

    Returns:
        str or None: If dry_run is True, returns the commands that would be executed.
                    If verbose is True, returns the stdout of GNU Parallel.
                    Otherwise, returns None.

    Raises:
        TypeError: If cross parameter is not properly formatted.
        ValueError: If named parameters contain multiple lists of different lengths.

    Examples:
        >>> parallel_zip("ls {dir}", dir="/tmp", verbose=True)
        # Lists contents of /tmp directory

        >>> parallel_zip("ls {dir}", dir=["/tmp", "/home"], verbose=True)
        # Lists contents of both directories sequentially

        >>> parallel_zip("echo 'File: {file}, Mode: {mode}'",
        ...              file=["file1.txt", "file2.txt"],
        ...              cross=[{"mode": ["read", "write"]}],
        ...              verbose=True)
        # Outputs all combinations of files and modes:
        # File: file1.txt, Mode: read
        # File: file1.txt, Mode: write
        # File: file2.txt, Mode: read
        # File: file2.txt, Mode: write

        >>> commands = parallel_zip("cat {file} | grep {pattern} > {output}",
        ...                        file=["data.csv"],
        ...                        cross=[{"pattern": ["apple", "banana"]},
        ...                               {"output": ["apple.txt", "banana.txt"]}],
        ...                        dry_run=True)
        # Returns: ['cat data.csv | grep apple > apple.txt',
        #           'cat data.csv | grep apple > banana.txt',
        #           'cat data.csv | grep banana > apple.txt',
        #           'cat data.csv | grep banana > banana.txt']

        >>> # Multi-line commands are joined with &&
        >>> complex_cmd = '''
        ...     mkdir -p {dir}
        ...     echo "Created directory" > {dir}/info.txt
        ...     ls -la {dir}
        ... '''
        >>> parallel_zip(complex_cmd, dir=["test1", "test2"], verbose=True)
        # Creates directories, writes info files, and lists contents

        >>> # Python expressions are evaluated
        >>> parallel_zip("echo 'Double of {num} is {int(num)*2}'",
        ...              num=[10, 20, 30],
        ...              verbose=True)
        # Outputs: Double of 10 is 20
        #          Double of 20 is 40
        #          Double of 30 is 60

        >>> # Motivating example: simplifying complex nested loops
        >>> samples = ['U', 'E']
        >>> refs = ['28SrRNA', '18SrRNA']
        >>> ref_path = '~/reference'
        >>> in_path = 'trim'
        >>> out_path = 'map'
        >>>
        >>> # Traditional approach with nested loops:
        >>> for R1, R2 in zip([f'{sample}_R1.fq.gz'for sample in samples], [f'{sample}_R2.fq.gz'for sample in samples]):
        ...     for sample in samples:
        ...         for ref in refs:
        ...             print(f'hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1} -2 {in_path}/{R2} -S {out_path}/{sample}.sam')
        ...
        hisat-3n --index ~/reference//28SrRNA.fa -p 6 --base-change C,T  -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/U.sam
        hisat-3n --index ~/reference//18SrRNA.fa -p 6 --base-change C,T  -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/U.sam
        hisat-3n --index ~/reference//28SrRNA.fa -p 6 --base-change C,T  -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/E.sam
        hisat-3n --index ~/reference//18SrRNA.fa -p 6 --base-change C,T  -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/E.sam
        hisat-3n --index ~/reference//28SrRNA.fa -p 6 --base-change C,T  -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/U.sam
        hisat-3n --index ~/reference//18SrRNA.fa -p 6 --base-change C,T  -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/U.sam
        hisat-3n --index ~/reference//28SrRNA.fa -p 6 --base-change C,T  -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/E.sam
        hisat-3n --index ~/reference//18SrRNA.fa -p 6 --base-change C,T  -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/E.sam

        >>> # Simplified with parallel_zip:
        >>> parallel_zip('''
        ... hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam
        ... ''',
        ...              R1=[f'{sample}_R1' for sample in samples],
        ...              R2=[f'{sample}_R2' for sample in samples],
        ...              cross=[{'sample': samples}, {'ref': refs}],
        ...              dry_run=True)
        # This generates all 8 command combinations in a single call
    """

    if java_memory:
        old_setting = os.environ.get('_JAVA_OPTIONS', '')
        os.environ['_JAVA_OPTIONS'] = f'-Xmx{java_memory}'

    proc, proc_cmds = execute_command(
        parse_command(command, cross=cross, **named_vals), dry_run=dry_run, verbose=verbose)

    if java_memory:
        if old_setting:
            os.environ['_JAVA_OPTIONS'] = old_setting
        else:
            os.environ.pop('_JAVA_OPTIONS', None)

    if dry_run: return proc_cmds

    if proc.returncode:
        print(f'parallel_zip: error with return code {proc.returncode}')
        if proc.stderr: print(f'Error details:\n{proc.stderr}')
        return None

    if verbose and proc.stderr: print(f'parallel_zip warning:\n{proc.stderr}')

    if verbose: return proc.stdout

    return None
