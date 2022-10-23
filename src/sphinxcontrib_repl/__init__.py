"""
Create default config file in a temp location
$MATPLOTLIBRC if it is a file, else $MATPLOTLIBRC/matplotlibrc

https://matplotlib.org/stable/tutorials/introductory/customizing.html#customizing-with-matplotlibrc-files

create an option for user to add more default values

backend: 'sphixcontrib_repl://ReplBackend'

support environmental options

#figure.figsize:     6.4, 4.8  # figure size in inches
#savefig.dpi:       figure      # figure dots per inch or 'figure'
#savefig.facecolor: auto        # figure face color when saving
#savefig.edgecolor: auto        # figure edge color when saving
#savefig.format:    png         # {png, ps, pdf, svg}
#savefig.bbox:      standard    # {tight, standard}
                                # 'tight' is incompatible with pipe-based animation
                                # backends (e.g. 'ffmpeg') but will work with those
                                # based on temporary files (e.g. 'ffmpeg_file')
#savefig.pad_inches:  0.1       # padding to be used, when bbox is set to 'tight'
#savefig.directory:   ~         # default directory in savefig dialog, gets updated after
                                # interactive saves, unless set to the empty string (i.e.
                                # the current directory); use '.' to start at the current
                                # directory but update after interactive saves
#savefig.transparent: False     # whether figures are saved with a transparent
                                # background by default
#savefig.orientation: portrait  # orientation of saved figure, for PostScript output only

#rcparams:  dict of any other Matplotlib default values

each repl/repl-quiet directives support local-options
dpi = "figure"
bbox_inches = None
pad_inches = 0.1
facecolor = "auto"
edgecolor = "auto"
figsize = (w,h)
captions = None|str|[str]


generating SVG maybe is a challenge??
https://github.com/sphinx-doc/sphinx/issues/2240

.. image:: /images/test-svg.svg

.. raw:: html

  <object data="_images/test-svg.svg" type="image/svg+xml"></object>

https://github.com/forexample/test-sphinx-svg-image

add `disable_mpl` env flag to skip mpl initialization

"""

import os
import sys
import subprocess as sp

from docutils import nodes
from docutils.parsers.rst import Directive, directives

__version__ = "0.1.0"


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


# per-document repl processes
repl_procs = {}

# per-document True if mpl initialized
mpl_init = {}


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
        '_mpl.use("module://sphinxcontrib_repl.mpl_backend")',
        f'_mpl.rcParams["savefig.directory"] = r"{img_prefix}"',
        f'_mpl.rcParams["savefig.format"] = "{format}"',
    ]
    proc.communicate(cmds)


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


def create_image(document, line):
    # TODO : support image options
    imgpath = line[10:]
    confdir = document.settings.env.app.confdir  # source root
    rst_file = document.attributes["source"]  # source file path
    rst_outdir = os.path.join(
        document.settings.env.app.builder.outdir,
        os.path.dirname(os.path.relpath(rst_file, confdir)).lstrip(os.path.sep),
    )
    img_relpath = os.path.relpath(imgpath, rst_outdir)
    uri = directives.uri(img_relpath.replace("\\", "/"))
    return nodes.image(line, uri=uri)


class div(nodes.General, nodes.Element):
    pass


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
# option_spec = {'figsize':     rcsetup.validate_floatlist,  # figure size in inches
# 'dpi':       rcsetup.validate_dpi,      # figure dots per inch or 'figure'
# 'facecolor': rcsetup.validate_color,        # figure face color when saving
# 'edgecolor': rcsetup.validate_color,        # figure edge color when saving
# 'format':    'auto',         # {png, ps, pdf, svg}
# 'bbox':      rcsetup.validate_bbox,    # {tight, standard}
#                                 # 'tight' is incompatible with pipe-based animation
#                                 # backends (e.g. 'ffmpeg') but will work with those
#                                 # based on temporary files (e.g. 'ffmpeg_file')
# 'pad_inches':  rcsetup.validate_float,       # padding to be used, when bbox is set to 'tight'
# 'rc_params': {}      # other rcParams options
# }


class REPL(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self):
        # run the content on REPL and get stdin+stdout+stderr block of lines
        lines = get_repl(self).communicate(self.content)

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
                return nodes.container(
                    "",
                    *(
                        create_image(self.state_machine.document, line)
                        for line in block
                    ),
                )
            else:
                s = "\n".join(block)
                return nodes.doctest_block(s, s, language="python")

        return [to_node(blk) for blk in blocks]


class REPL_Quiet(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self):
        # dump the content on REPL & ignore what's printed on the interpreter
        # do show the matplotlib figures

        # run the content on REPL and get stdin+stdout+stderr block of lines
        lines = get_repl(self).communicate(self.content)

        # only return the image lines
        return [
            nodes.container(
                "",
                *(
                    create_image(self.state_machine.document, line)
                    for line in lines
                    if line.startswith("#repl:img:")
                ),
            )
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
    app.add_config_value("repl_mpl_format", None, "", str)
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
