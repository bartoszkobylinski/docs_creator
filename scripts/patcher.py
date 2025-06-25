import re
from textwrap import indent

def apply_docstring_patch(file_path: str, lineno: int, new_doc: str):
    """
    Replaces (or inserts) the triple-quoted docstring for the function/class
    whose def line is at `lineno` in file_path.
    """
    lines = open(file_path, "r").read().splitlines(True)
    i = lineno - 1

    # find the line with def/class
    header = lines[i]
    indent_match = re.match(r"^(\s*)", lines[i])
    base_indent = indent_match.group(1)

    # skip any existing docstring
    j = i + 1
    if j < len(lines) and re.match(rf"{base_indent}\s*['\"]{{3}}", lines[j]):
        # existing triple-quote: skip until closing
        j += 1
        while j < len(lines) and not re.match(rf"{base_indent}\s*['\"]{{3}}", lines[j]):
            j += 1
        if j < len(lines): 
            j += 1

    # build the new docstring block
    block = ['\n',
             f'{base_indent}"""\n']
    for line in new_doc.strip().splitlines():
        block.append(f'{base_indent}{line}\n')
    block.append(f'{base_indent}"""\n')

    # splice it in
    new_lines = lines[:j] + block + lines[j:]
    open(file_path, "w").write("".join(new_lines))
