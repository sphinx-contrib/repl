import subprocess as sp
from docutils import nodes

#

lines = [
    "x=5",
    'f"{x=}"',
    "print(x)",
    "if x:",
    ' "if true"',
    "else:",
    ' "if false"',
    " 5+5",
    "",
]

proc = sp.Popen(
    "python -i -q",
    stdin=sp.PIPE,
    stdout=sp.PIPE,
    stderr=sp.STDOUT,
    universal_newlines=True,
    shell=True,
    bufsize=0,
)


def run_repl(lines):
    blocks = []
    code_in = []
    code_out = []

    def flush():
        if len(code_in):
            s = "\n".join(code_in)
            blocks.append(nodes.doctest_block(s, s, language="python"))
            code_in.clear()
        if len(code_out):
            s = "".join(code_out)
            blocks.append(nodes.literal_block(s, s, language="none"))
            code_out.clear()

    out = proc.stdout.read(4)
    for line in lines:
        # submit a new line to REPL
        proc.stdin.write(f"{line}\n")
        code_in.append(f"{out}{line}")

        # receive 4 bytes (if no output, it is either '>>> ' or '... ')
        out = proc.stdout.read(4)

        # if output line is shorter than 4 bytes, split
        eol = out.rfind("\n") + 1
        if eol:
            code_out.append(out[:eol])
            flush()
            out = out[eol:] + proc.stdout.read(eol)

        # enter the loop only if line produced an output
        while out not in (">>> ", "... "):
            out += proc.stdout.readline()  # get the rest of the line
            code_out.append(out)

            # start reading the next line
            out = proc.stdout.read(4)

        if out == ">>> ":
            flush()

    return blocks


print(run_repl(lines))
proc.kill()
