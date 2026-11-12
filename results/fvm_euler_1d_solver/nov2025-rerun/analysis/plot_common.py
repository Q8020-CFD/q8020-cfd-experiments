"""Shared names, colors and helpers for the qiskit-version comparison figures."""
import matplotlib
matplotlib.use('Agg')
from matplotlib.ticker import FuncFormatter, NullFormatter

# results folder -> (display name, color); the qiskit version is what differs between them
VERSIONS = {
    'nov_pkgs': ('qiskit 1.2.4', '#1f77b4'),
    'new_pkgs': ('qiskit 2.5.2', '#d62728'),
    'latest_pkgs': ('qiskit 2.6.2', '#8c1a8c'),
}
MARKERS = {'nov_pkgs': 'o', 'new_pkgs': 's', 'latest_pkgs': 'D'}
LEVEL_NOTE = ("HHL transpile uses qiskit's default settings (no optimization level set): "
              "level 1 on qiskit 1.2.4, level 2 on 2.5.2 and 2.6.2")


def finish(fig, path, note=LEVEL_NOTE):
    """tight_layout with room for a one-line footnote, save, close."""
    import textwrap
    text = textwrap.fill(note, width=int(fig.get_figwidth() * 13)) if note else ''
    lines = text.count('\n') + 1 if text else 0
    fig.tight_layout(rect=(0, 0.012 + 0.028 * lines, 1, 1))
    if text:
        fig.text(0.01, 0.008, text, fontsize=7.5, color='#555555', ha='left', va='bottom')
    fig.savefig(path, dpi=140)
    matplotlib.pyplot.close(fig)


def commas(ax, axis='y'):
    fmt = FuncFormatter(lambda v, _: f'{v:,.0f}')
    getattr(ax, f'{axis}axis').set_major_formatter(fmt)
    getattr(ax, f'{axis}axis').set_minor_formatter(NullFormatter())


def tidy(ax, grid_axis='y'):
    ax.grid(alpha=.3, axis=grid_axis); ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
