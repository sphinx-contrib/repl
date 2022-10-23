from matplotlib.backend_bases import _Backend, FigureManagerBase
from matplotlib._pylab_helpers import Gcf
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib import rcParams


@_Backend.export
class ReplBackend(_Backend):
    FigureCanvas = FigureCanvasSVG
    FigureManager = FigureManagerBase

    fig_count = 0

    @classmethod
    def show(cls, *, block=None):
        """
        "show" all figures.

        """

        prefix = rcParams["savefig.directory"]
        format = rcParams["savefig.format"]

        for figno, fig in Gcf.figs.items():
            fname = f"{prefix}{cls.fig_count}_{figno}.{format}"
            fig.canvas.figure.savefig(fname, format=format)
            # notify the repl extension
            print(f"#repl:img:{fname}")

        cls.fig_count += 1

        # close all figures
        Gcf.destroy_all()
