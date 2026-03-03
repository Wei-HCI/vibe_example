"""
rcode.setup - Environment configuration and citation display.

Equivalent to R's rcode_setup() function.
"""

from __future__ import annotations

import warnings
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt


def rcode_setup(
    set_options: bool = True,
    set_theme: bool = True,
    print_citation: bool = True,
) -> None:
    """Configure the global environment for rcode workflows.

    Parameters
    ----------
    set_options : bool
        If True, adjusts pandas/numpy display defaults.
    set_theme : bool
        If True, sets a clean, publication-ready matplotlib/seaborn theme.
    print_citation : bool
        If True, prints citation information.
    """
    # 1. Global display options
    if set_options:
        try:
            import pandas as pd

            pd.set_option("display.float_format", lambda x: f"{x:.10g}")
            pd.set_option("display.max_columns", 50)
        except ImportError:
            pass

        import numpy as np

        np.set_printoptions(precision=10, suppress=True)

    # 2. Matplotlib / seaborn theme
    if set_theme:
        try:
            import seaborn as sns

            sns.set_theme(style="whitegrid", font_scale=1.2)
        except ImportError:
            pass

        plt.rcParams.update(
            {
                "figure.figsize": (10, 7),
                "axes.titlesize": 28,
                "axes.labelsize": 20,
                "xtick.labelsize": 17,
                "ytick.labelsize": 17,
                "legend.fontsize": 15,
                "figure.titlesize": 28,
                "font.family": "sans-serif",
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        )

    # 3. Citation
    if print_citation:
        _print_citation()


def _print_citation() -> None:
    msg = """
If you use these functions, please cite:

Colley, M. (2024). rCode: Enhanced R Functions for Statistical Analysis and Reporting.
Retrieved from https://github.com/M-Colley/rCode

BibTeX:
@misc{colley2024rcode,
  author       = {Mark Colley},
  title        = {rCode: Enhanced R Functions for Statistical Analysis and Reporting},
  year         = {2024},
  howpublished = {\\url{https://github.com/M-Colley/rCode}},
  doi          = {10.5281/zenodo.16875755}
}
"""
    print(msg)
