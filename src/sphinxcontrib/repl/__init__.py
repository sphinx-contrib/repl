import json
import os
import sys
import subprocess as sp

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.images import Image

__version__ = "0.3.0"


def _option_boolean(arg):
    if not arg or not arg.strip():
        # no argument given, assume used as a flag
        return True
    elif arg.strip().lower() in ("no", "0", "false"):
        return False
    elif arg.strip().lower() in ("yes", "1", "true"):
        return True
    else:
        raise ValueError(f"{arg!r} unknown boolean")


def _validate_json_dict(arg):
    try:
        d = json.loads(arg)
        assert isinstance(d, dict)
        return d
    except:
        raise TypeError("expect JSON encoded dict")


class REPLopen(sp.Popen):
    def __init__(self) -> None:
        super().__init__(
            [sys.executable, "-i", "-q"],
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            universal_newlines=True,
            bufsize=0,
            cwd=os.getcwd(),
        )
        self.stdout.read(4)

    def communicate(self, lines, show_input=True, show_output=True):
        """input command lines one at a time & record interpreter I/O

        :param lines: Python command lines (no new line at the end)
        :type lines: list[str]
        :param show_input: True to show input lines by default, defaults to True
        :type show_input: bool, optional
        :param show_output: True to show output lines by default, defaults to True
        :type show_output: bool, optional
        :return: list of stored interpreter lines
        :rtype: list[str]

        magic comments

        - #repl:hide
        - #repl:show
        - #repl:hide-input
        - #repl:hide-output

        special comment outputs

        - #repl:img:  - path of the output image

        """

        out_lines = []  # doctest_block lines to output
        out = ">>> "  # last read output

        def try_read_prompt(show_out):
            """read until 4-character Python prompt string is obtained"""

            # receive 4 bytes (if no output, it is either '>>> ' or '... ')
            out = self.stdout.read(4)

            # if output line is shorter than 4 bytes, split
            eol = out.rfind("\n") + 1
            while eol:
                if show_out:
                    out_lines.append(out[: eol - 1])
                out = out[eol:] + self.stdout.read(eol)
                eol = out.rfind("\n") + 1

            return out

        def process_magic(magic):

            try:
                cmd, io = magic.split("-")
                is_in = io.startswith("in")
                is_out = io.startswith("out")
            except:
                cmd = magic
                is_in = is_out = True

            show = cmd == "show"  # show/hide
            if (not show and cmd != "hide") or not (is_in or is_out):
                raise self.error(f"{magic} - unknown magic comment")

            return show if is_in else None, show if is_out else None

        def read_next(show_out):
            """read output lines (If any) until encounters the next prompt"""

            out = try_read_prompt(show_out)

            # enter the loop only if line produced an output
            while out not in (">>> ", "... "):
                # output line found
                out += self.stdout.readline()  # get the rest of the line
                if show_out or out.startswith("#repl:"):
                    out_lines.append(out[:-1])

                # read the next 4-characters
                out = try_read_prompt(show_out)

            return out

        for line in lines:

            # check for magic word
            try:
                line, magic = line.rsplit("#repl:", 1)
                show_in, show_out = process_magic(magic)
                if not line or line.isspace():
                    # comment line, set new display modes and done
                    if show_in is not None:
                        show_input = show_in
                    if show_out is not None:
                        show_output = show_out
                    continue

                # how to handle current line
                if show_in is None:
                    show_in = show_input
                if show_out is None:
                    show_out = show_output

            except:
                show_in = show_input
                show_out = show_output

            # submit a new line to REPL
            self.stdin.write(f"{line}\n")
            if show_in:
                out_lines.append(f"{out}{line}")

            # get any output it produced
            out = read_next(show_out)

        # insert empty lines if Python prompt is not shown
        while out != ">>> ":
            # submit a new line to REPL
            self.stdin.write(f"\n")
            if show_in:
                out_lines.append(out)

            # get any output it produced
            out = read_next(show_output)

        # return out_lines
        return out_lines


# per-document repl processes
repl_procs = {}


def get_imgs_dir(app):
    # output_dir: final location in the builder's directory
    return os.path.join(app.builder.outdir, "_images_repl")


def get_repl(directive):

    doc = directive.state_machine.document

    # Get the source file and if it has changed, then reset the context.
    docpath = doc.attributes["source"]
    proc = repl_procs.get(docpath, None)
    if proc is None:
        proc = repl_procs[docpath] = REPLopen()

        # if mpl_disable is not truthy
        env = doc.settings.env
        config = env.config
        if not config.repl_mpl_disable:
            init_mpl(proc, env.app, config.repl_mpl_format)

    return proc


def init_mpl(proc, app, format):

    # set directory & format
    # config = directive.state_machine.app
    img_dir = get_imgs_dir(app)
    os.makedirs(img_dir, exist_ok=True)

    img_prefix = os.path.join(img_dir, f"mpl_").replace(".", "-")

    if format is None:
        # auto-detect based on the builder's supported type
        supported_image_types = app.builder.supported_image_types
        format = next(
            fmt
            for fmt, mime in {
                "svg": "image/svg+xml",
                "pdf": "application/pdf",
                "png": "image/png",
            }.items()
            if mime in supported_image_types
        )

    # set directory and format on the repl process
    # - if matplotlib not installed, these lines will silently fail
    cmds = [
        "import matplotlib as _mpl",
        '_mpl.use("module://sphinxcontrib.repl.mpl_backend")',
        f'_mpl.rcParams["savefig.directory"] = r"{img_prefix}"',
        f'_mpl.rcParams["savefig.format"] = "{format}"',
    ]
    _ = proc.communicate(cmds, show_input=False, show_output=True)
    if _:
        raise RuntimeError(f"failed to initialize matplotlib:\n\n{_}")


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


def create_image(document, line, image_options):
    imgpath = line[10:]
    confdir = document.settings.env.app.confdir  # source root
    rst_file = document.attributes["source"]  # source file path
    rst_outdir = os.path.join(
        document.settings.env.app.builder.outdir,
        os.path.dirname(os.path.relpath(rst_file, confdir)).lstrip(os.path.sep),
    )
    img_relpath = os.path.relpath(imgpath, rst_outdir)
    uri = directives.uri(img_relpath.replace("\\", "/"))
    return nodes.image(line, uri=uri, **image_options)


def create_mpl_container_node(document, lines, options):
    image_options = {k[6:]: v for k, v in options.items() if k.startswith("image_")}
    return nodes.container(
        "",
        *(
            create_image(document, line, image_options)
            for line in lines
            if line.startswith("#repl:img:")
        ),
    )


# TODO : add following options to Directives
# image option
# option_spec = {'alt': directives.unchanged,
#                 'height': directives.length_or_unitless,
#                 'width': directives.length_or_percentage_or_unitless,
#                 'scale': directives.percentage,
#                 'align': align,
#                 'target': directives.unchanged_required,
#                 'class': directives.class_option,
#                 'name': directives.unchanged}
#
# mpl option
# from matplotlib import rcsetup


def create_image_option_spec():
    return {
        "image_alt": directives.unchanged,
        "image_height": directives.length_or_unitless,
        "image_width": directives.length_or_percentage_or_unitless,
        "image_scale": directives.nonnegative_int,
        "image_align": Image.align,
        "image_class": directives.class_option,
    }


def create_mpl_option_spec():
    try:
        from matplotlib import rcsetup

        _error = None
    except:

        def _raise(arg):
            raise RuntimeError("matplotlib package not found")

        _error = _raise

    return {
        "mpl_figsize": _error
        or rcsetup._listify_validator(rcsetup.validate_float, n=2),
        "mpl_dpi": _error or rcsetup.validate_dpi,
        "mpl_facecolor": _error or rcsetup.validate_color,
        "mpl_edgecolor": _error or rcsetup.validate_color,
        "mpl_bbox": _error or rcsetup.validate_bbox,
        "mpl_pad_inches": _error or rcsetup.validate_float,
        "mpl_transparent": _error or rcsetup.validate_bool,
        "mpl_rc_params": _error or _validate_json_dict,
    }


def modify_mpl_rcparams(proc, options):

    lines = ["import matplotlib as _mpl"]

    # write rc_params options
    for k, v in options.get("mpl_rc_params", {}).items():
        if isinstance(v, str):
            v = f"'{v}'"
        lines.append(f"_mpl.rcParams['{k}']={v}")

    # figure size option needs to be converted from tuple to
    v = options.get("mpl_figsize", None)
    if v is not None:
        lines.append(f"_mpl.rcParams['figure.figsize']={v}")

    # write
    for key in [
        "savefig.dpi",
        "savefig.facecolor",
        "savefig.edgecolor",
        "savefig.bbox",
        "savefig.pad_inches",
        "savefig.transparent",
    ]:
        value = options.get(f'mpl_{key.split(".", 1)[-1]}', None)
        if value is not None:
            if isinstance(value, str):
                value = f"'{value}'"
            lines.append(f"_mpl.rcParams['{key}']={value}")

    if len(lines) > 1:
        _ = proc.communicate(lines, False, True)
        if _:
            raise RuntimeError(f"failed to modify matplotlib rcParams:\n\n{_}")


class REPL(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "hide-input": _option_boolean,
        "hide-output": _option_boolean,
        **create_mpl_option_spec(),
        **create_image_option_spec(),
    }

    def run(self):

        proc = get_repl(self)

        # apply if any mpl.rcParams options are given
        modify_mpl_rcparams(proc, self.options)

        # run the content on REPL and get stdin+stdout+stderr block of lines
        lines = proc.communicate(
            self.content,
            show_input=not self.options.get("hide-input", False),
            show_output=not self.options.get("hide-output", False),
        )

        # no lines to show
        if not len(lines):
            return []

        # separate texts and images
        blk = [lines[0]]
        blocks = [blk]
        isfig = lines[0].startswith("#repl:img:")
        for line in lines[1:]:
            if isfig != line.startswith("#repl:img:"):
                blk = [line]
                blocks.append(blk)
                isfig = not isfig
            else:
                blk.append(line)

        def to_node(block):
            if block[0].startswith("#repl:img:"):
                # generated new image
                return create_mpl_container_node(
                    self.state_machine.document, lines, self.options
                )
            else:
                s = "\n".join(block)
                return nodes.doctest_block(s, s, language="python")

        return [to_node(blk) for blk in blocks]


class REPL_Quiet(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {**create_mpl_option_spec(), **create_image_option_spec()}

    def run(self):
        # dump the content on REPL & ignore what's printed on the interpreter
        # do show the matplotlib figures

        proc = get_repl(self)

        # apply if any mpl.rcParams options are given
        modify_mpl_rcparams(proc, self.options)

        # run the content on REPL and get stdin+stdout+stderr block of lines
        lines = proc.communicate(self.content, show_input=False, show_output=False)

        # only return the image lines
        return [
            create_mpl_container_node(self.state_machine.document, lines, self.options)
        ]


def mpl_init(app, config):
    """if mpl support is enabled, create matplotlibrc file and
    set MATPLOTLIBRC env var"""

    if config.repl_mpl_disable:
        # nothing to do
        return

    # create matplot default param
    file = os.path.join(app.doctreedir, "matplotlibrc")
    with open(file, "wt") as f:
        # write rc_params options
        for k, v in config.repl_mpl_rc_params.items():
            f.write(f"{k}: {v}\n")

        # figure size option needs to be converted from tuple to
        v = config["repl_mpl_figsize"]
        if v is not None:
            if not isinstance(v, str):
                v = ",".join((str(vv) for vv in v))
            f.write(f"figure.figsize:{v}\n")

        # write
        for key in [
            "savefig.dpi",
            "savefig.facecolor",
            "savefig.edgecolor",
            "savefig.bbox",
            "savefig.pad_inches",
            "savefig.transparent",
        ]:
            value = config["repl_mpl_" + key.split(".", 1)[-1]]
            if value is not None:
                f.write(f"{key}: {value}\n")

    # set the environmental variable
    os.environ["MATPLOTLIBRC"] = file


def setup(app):

    app.add_config_value("repl_mpl_disable", False, "", [bool])
    app.add_config_value("repl_mpl_figsize", None, "", [tuple])
    app.add_config_value("repl_mpl_dpi", 96, "", [int])
    app.add_config_value("repl_mpl_facecolor", None, "", [str])
    app.add_config_value("repl_mpl_edgecolor", None, "", [str])
    app.add_config_value("repl_mpl_format", None, "", [str])
    app.add_config_value("repl_mpl_bbox", None, "", [tuple, list])
    app.add_config_value("repl_mpl_pad_inches", None, "", [float, int])
    app.add_config_value("repl_mpl_transparent", None, "", [float, int])
    app.add_config_value("repl_mpl_rc_params", {}, "", [dict])

    app.add_directive("repl", REPL)
    app.add_directive("repl-quiet", REPL_Quiet)

    app.connect("config-inited", mpl_init)
    app.connect("doctree-read", kill_repl)
    app.connect("build-finished", kill_all)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


# avoid importing mpl_backend submodule (which should be only used in repl process)
__all__ = [name for name, thing in globals().items() if name != "mpl_backend"]
