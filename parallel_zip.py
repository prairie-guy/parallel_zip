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
        zipper(a=[1, 2], b=['x', 'y'])
        [{'a': '1', 'b': 'x'}, {'a': '2', 'b': 'y'}]

        zipper(a=[1, 2], b='x')
        [{'a': '1', 'b': 'x'}, {'a': '2', 'b': 'x'}]

        zipper(a=[1, 2], cross=[{'sample': ['A', 'B']}])
        [{'a': '1', 'sample': 'A'}, {'a': '1', 'sample': 'B'},
         {'a': '2', 'sample': 'A'}, {'a': '2', 'sample': 'B'}]

        zipper(in_path=['file1.txt', 'file2.txt'],
                out_path=['out1.txt', 'out2.txt'],
                cross=[{'sample': ['A', 'B', 'C']}])
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

    if not named_vals and cross is None: return [{}]
    #if not named_vals and cross is None: return("Usage: zipper(name1=val1, name2=val2, ..., cross={'k':vs} | [{'k1':vs1} ...] )")
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

    # gnu
    #if verbose: proc = subprocess.run(["parallel", "--verbose", ":::", *processed_commands], capture_output=True, text=True)
    #else: proc = subprocess.run(["parallel", ":::", *processed_commands], capture_output=True, text=True)

    # rust orig
    #if verbose: proc = subprocess.run(["rust-parallel", "/bin/bash", "-c", ":::", *processed_commands], capture_output=True, text=True)
    #else: proc = subprocess.run(["rust-parallel", "/bin/bash", "-c", ":::", *processed_commands], capture_output=True, text=True)

    # rust new
    if verbose: proc = subprocess.run(["rust-parallel", "-s", ":::", *processed_commands], capture_output=True, text=True)
    else: proc = subprocess.run(["rust-parallel", "-s" , ":::", *processed_commands], capture_output=True, text=True)

    return proc, processed_commands

def parallel_zip(command, cross=None, verbose=False, lines=False, dry_run=False, strict=False, java_memory=None,  **named_vals):
    '''Execute shell commands in parallel with parameter substitution.

    Transform command templates into multiple commands by substituting parameters,
    then execute them in parallel using GNU parallel. Perfect for batch processing,
    parameter sweeps, and avoiding nested loops in data pipelines.

    Parameters
    ----------
    command : str
        Command template with {parameter} placeholders. Multi-line commands are
        automatically joined with &&. Python expressions in {expr} are evaluated.
        Use {{text}} for literal braces (e.g., awk '{{print $1}}').

    cross : dict, list of dicts, or Cross() result, optional
        Parameters for cross-product expansion. Every combination is generated.
        Example: cross=[{"mode": ["fast", "slow"]}, {"size": [1, 2]}]

    verbose : bool, default False
        If True, return command output. Otherwise, run silently.

    lines : bool, default False
        If True and verbose=True, return output as list of lines.
        If False and verbose=True, return output as string.
        Only applies when verbose=True.

    dry_run : bool, default False
        If True, return list of commands without executing them.

    strict : bool, default False
        If True, treat any non-zero exit code as an error and stop.
        If False, continue silently even if some commands fail.
        Many Unix tools (grep, diff, test) use exit codes for information.

    java_memory : str, optional
        Set Java heap size (e.g., '4g', '8g') for Java-based tools.

    **named_vals : keyword arguments
        Parameters to substitute. Lists are processed in parallel (like zip).
        Single values are broadcast to match list lengths.

    Returns
    -------
    str, list, or None
        - If dry_run=True: List of commands that would be executed
        - If verbose=True and lines=True: List of output lines
        - If verbose=True and lines=False: Output as string
        - Otherwise: None (commands run silently)


    Motivating Example
    -----------------
    # Python for-loop semantics with 'rational' variable substitution executed in parallel within bash shell

    samples = ['U', 'E']
    refs = ['28SrRNA', '18SrRNA']
    ref_path = '~/reference'
    in_path = 'trim'
    out_path = 'map'
    parallel_zip("""hisat-3n --index {ref_path}/{ref}.fa -p 6 --base-change C,T -1 {in_path}/{R1}.fq.gz -2 {in_path}/{R2}.fq.gz -S {out_path}/{sample}.sam""",
                        R1=[f'{sample}_R1' for sample in samples],
                        R2=[f'{sample}_R2' for sample in samples],
                        cross= Cross(sample=samples, ref=refs),
                    dry_run=True)
    ['hisat-3n --index ~/reference/28SrRNA.fa -p 6 --base-change C,T -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/U.sam',
     'hisat-3n --index ~/reference/18SrRNA.fa -p 6 --base-change C,T -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/U.sam',
     'hisat-3n --index ~/reference/28SrRNA.fa -p 6 --base-change C,T -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/E.sam',
     'hisat-3n --index ~/reference/18SrRNA.fa -p 6 --base-change C,T -1 trim/U_R1.fq.gz -2 trim/U_R2.fq.gz -S map/E.sam',
     'hisat-3n --index ~/reference/28SrRNA.fa -p 6 --base-change C,T -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/U.sam',
     'hisat-3n --index ~/reference/18SrRNA.fa -p 6 --base-change C,T -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/U.sam',
     'hisat-3n --index ~/reference/28SrRNA.fa -p 6 --base-change C,T -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/E.sam',
     'hisat-3n --index ~/reference/18SrRNA.fa -p 6 --base-change C,T -1 trim/E_R1.fq.gz -2 trim/E_R2.fq.gz -S map/E.sam']

    More Examples
    -------------
    # Dry run - see what commands would be executed
    parallel_zip("""
         echo -n '{ext} {fn} ' ; echo {fn} | grep {ext} || echo '*'
     """,
         fn=["A.png", "B.svg", 'C.mat'],
         cross=Cross(ext=['png', 'svg','mat']),
         dry_run=True)
    ["echo -n 'png A.png ' ; echo A.png | grep png || echo '*'",
     "echo -n 'svg A.png ' ; echo A.png | grep svg || echo '*'",
     "echo -n 'mat A.png ' ; echo A.png | grep mat || echo '*'",
     "echo -n 'png B.svg ' ; echo B.svg | grep png || echo '*'",
     "echo -n 'svg B.svg ' ; echo B.svg | grep svg || echo '*'",
     "echo -n 'mat B.svg ' ; echo B.svg | grep mat || echo '*'",
     "echo -n 'png C.mat ' ; echo C.mat | grep png || echo '*'",
     "echo -n 'svg C.mat ' ; echo C.mat | grep svg || echo '*'",
     "echo -n 'mat C.mat ' ; echo C.mat | grep mat || echo '*'"]

    # Execute and get output as string (verbose=True)
    parallel_zip("""
         echo -n '{ext} {fn} ' ; echo {fn} | grep {ext} || echo '*'
     """,
         fn=["A.png", "B.svg", 'C.mat'],
         cross=Cross(ext=['png', 'svg','mat']),
         verbose=True)
    'png A.png A.png\nsvg A.png *\nmat A.png *\npng B.svg *\nsvg B.svg B.svg\nmat B.svg *\npng C.mat *\nsvg C.mat *\nmat C.mat C.mat\n'

    # Execute and get output as list of lines (verbose=True, lines=True)
    parallel_zip("""
         echo -n '{ext} {fn} ' ; echo {fn} | grep {ext} || echo '*'
     """,
         fn=["A.png", "B.svg", 'C.mat'],
         cross=Cross(ext=['png', 'svg','mat']),
         verbose=True, lines=True)
    ['png A.png A.png',
     'svg A.png *',
     'mat A.png *',
     'png B.svg *',
     'svg B.svg B.svg',
     'mat B.svg *',
     'png C.mat *',
     'svg C.mat *',
     'mat C.mat C.mat']

    # Strict mode - stop on any non-zero exit code (strict=True)
    # Note: removed || echo '*' so grep returns exit code 1 when no match
    # With strict=True, any non-zero exit causes error (6 of 9 commands failed)
    parallel_zip("""
         echo -n '{ext} {fn} ' ; echo {fn} | grep {ext}
     """,
         fn=["A.png", "B.svg", 'C.mat'],
         cross=Cross(ext=['png', 'svg','mat']),
         strict=True)
    parallel_zip: error with return code 6

    # Strict mode with verbose shows which commands were attempted (strict=True, verbose=True)
    parallel_zip("""
         echo -n '{ext} {fn} ' ; echo {fn} | grep {ext}
     """,
         fn=["A.png", "B.svg", 'C.mat'],
         cross=Cross(ext=['png', 'svg','mat']),
         strict=True, verbose=True)
    parallel_zip: error with return code 6
    Error details:
    echo -n 'png A.png ' ; echo A.png | grep png
    echo -n 'svg A.png ' ; echo A.png | grep svg
    echo -n 'mat A.png ' ; echo A.png | grep mat
    echo -n 'png B.svg ' ; echo B.svg | grep png
    echo -n 'svg B.svg ' ; echo B.svg | grep svg
    echo -n 'mat B.svg ' ; echo B.svg | grep mat
    echo -n 'png C.mat ' ; echo C.mat | grep png
    echo -n 'svg C.mat ' ; echo C.mat | grep svg
    echo -n 'mat C.mat ' ; echo C.mat | grep mat

    Notes
    -----
    IMPORTANT: When using $ in commands (awk, sed, regex), use single quotes:
        CORRECT:  parallel_zip("awk '{print $1}' {file}", ...)
        WRONG:    parallel_zip('awk "{print $1}" {file}', ...)

    The strict parameter is crucial for commands like grep, rga, diff, test
    that use exit codes to convey information rather than errors. With
    strict=False (default), these commands work as expected.

    '''

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
        if strict:
            print(f'parallel_zip: error with return code {proc.returncode}')
            if proc.stderr:
                print(f'Error details:\n{proc.stderr}')
            return None

    if verbose:
        if lines:
            return proc.stdout.splitlines()
        else:
            return proc.stdout

    return None


def pz(command, lines=True, strict=False):
   """Execute a command with environment variable substitution.

   A simple wrapper around parallel_zip for quick shell command execution.
   Variables in {braces} are substituted from the calling environment.

   IMPORTANT: Use single quotes to protect $ from shell expansion:
       pz("awk '{print $5}'")        # Correct - $ is protected
       pz("grep 'file$'")            # Correct - $ is protected
       pz("sed 's/^$/blank/'")       # Correct - $ is protected
       pz('awk "{print $5}"')        # WRONG - $ gets expanded to empty

   This applies to any tool that uses $ in its syntax: awk, sed, grep,
   perl, regex patterns, etc. The shell will expand $var before the tool
   sees it unless protected by single quotes.

   Args:
       command (str): Command to execute with {var} substitutions
       lines (bool): If True, return output as list of lines. Default True.

   Returns:
       list or str: Command output as list of lines, or string if lines=False
   """
   output = parallel_zip(command, verbose=True, strict=strict)
   if lines and output:
       return output.splitlines()
   return output
