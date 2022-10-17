import subprocess as sp

from docutils import nodes
from docutils.parsers.rst import Directive

__version__ = "0.0.0"


class REPLopen(sp.Popen):
    def __init__(self) -> None:
        super().__init__(
            ["python", "-i", "-q"],
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            universal_newlines=True,
            bufsize=0,
        )
        self.stdout.read(4)

    def communicate(self, lines):
        out_lines = []  # doctest_block lines to output
        out = ">>> "  # last read output

        def try_read_prompt():
            """read until 4-character Python prompt string is obtained"""

            # receive 4 bytes (if no output, it is either '>>> ' or '... ')
            out = self.stdout.read(4)

            # if output line is shorter than 4 bytes, split
            eol = out.rfind("\n") + 1
            while eol:
                out_lines.append(out[: eol - 1])
                out = out[eol:] + self.stdout.read(eol)
                eol = out.rfind("\n") + 1

            return out

        def read_next():
            """read output lines (If any) until encounters the next prompt"""

            out = try_read_prompt()

            # enter the loop only if line produced an output
            while out not in (">>> ", "... "):
                # output line found
                out += self.stdout.readline()  # get the rest of the line
                out_lines.append(out[:-1])

                # read the next 4-characters
                out = try_read_prompt()

            return out

        for line in lines:
            # submit a new line to REPL
            self.stdin.write(f"{line}\n")
            out_lines.append(f"{out}{line}")

            # get any output it produced
            out = read_next()

        # insert empty lines if Python prompt is not shown
        while out != ">>> ":
            # submit a new line to REPL
            self.stdin.write(f"\n")
            out_lines.append(out)

            # get any output it produced
            out = read_next()

        # return out_lines
        return out_lines


def _option_boolean(arg):
    """Copied from matplotlib plot_directive."""
    if not arg or not arg.strip():
        # no argument given, assume used as a flag
        return True
    elif arg.strip().lower() in ("no", "0", "false"):
        return False
    elif arg.strip().lower() in ("yes", "1", "true"):
        return True
    else:
        raise ValueError('"%s" unknown boolean' % arg)


# per-document repl processes
repl_procs = {}


def get_repl(directive):
    # Get the source file and if it has changed, then reset the context.
    docpath = directive.state_machine.document.attributes["source"]
    proc = repl_procs.get(docpath, None)
    if proc is None:
        proc = repl_procs[docpath] = REPLopen()
    return proc


class REPL(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    option_spec = {}

    def run(self):
        # run the content on REPL
        liens = get_repl(self).communicate(self.content)
        s = "\n".join(liens)
        return [nodes.doctest_block(s, s, language="python")]


class REPL_Quiet(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self):
        # dump the content on REPL & ignore what's printed on the interpreter
        get_repl(self).communicate(self.content)
        return []


def kill_repl(app, doctree):
    key = doctree.settings._source
    if key in repl_procs:
        repl_procs[key].kill()
        del repl_procs[key]


def kill_all(*_):
    """kill all repl processes (build-finished event)

    This is a safeguard function. All processes should have already been terminated at this point.
    """
    for p in repl_procs.values():
        p.kill()
    repl_procs.clear()


def setup(app):

    app.add_directive("repl", REPL)
    app.add_directive("repl-quiet", REPL_Quiet)

    app.connect("doctree-read", kill_repl)
    app.connect("build-finished", kill_all)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
