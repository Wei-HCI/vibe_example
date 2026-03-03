"""
rcode.utils - Core utility functions.

Ports of R helper functions: ``%!in%``, ``na.zero``, ``pathPrep``,
``n_fun``, ``havingIP``, ``normalize``, ``stat_sum_df``, etc.
"""

from __future__ import annotations

import os
import re
import socket
from typing import Any, Callable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# not-in operator                                                              #
# --------------------------------------------------------------------------- #

def not_in(x: Any, y: Sequence) -> bool:
    """Return True if *x* is **not** in *y* (R's ``%!in%``)."""
    return x not in y


# --------------------------------------------------------------------------- #
# na_zero                                                                      #
# --------------------------------------------------------------------------- #

def na_zero(x: Union[pd.Series, np.ndarray, list]) -> Union[pd.Series, np.ndarray]:
    """Replace NaN / None values with 0 (R's ``na.zero``)."""
    if isinstance(x, pd.Series):
        return x.fillna(0)
    arr = np.asarray(x, dtype=float)
    arr[np.isnan(arr)] = 0
    return arr


# --------------------------------------------------------------------------- #
# path_prep                                                                    #
# --------------------------------------------------------------------------- #

def path_prep(
    path: Optional[str] = None,
    copy_to_clipboard: bool = True,
) -> str:
    """Convert a Windows-style backslash path to forward slashes.

    If *path* is ``None``, attempts to read from the clipboard.

    Parameters
    ----------
    path : str or None
        A filesystem path. If ``None``, reads from clipboard.
    copy_to_clipboard : bool
        If True, writes the converted path back to the clipboard.

    Returns
    -------
    str
        The path with forward slashes.
    """
    if path is None:
        try:
            import pyperclip

            path = pyperclip.paste()
        except Exception:
            raise RuntimeError("Clipboard not available. Provide a path directly.")

    converted = path.replace("\\", "/")

    if copy_to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(converted)
        except Exception:
            pass

    return converted


# --------------------------------------------------------------------------- #
# n_fun                                                                        #
# --------------------------------------------------------------------------- #

def n_fun(x: Union[pd.Series, np.ndarray, list]) -> dict:
    """Return a dict with the median and a count label (R's ``n_fun``).

    Returns
    -------
    dict
        ``{"y": <median>, "label": "n = <count>"}``
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    return {"y": float(np.median(x)), "label": f"n = {len(x)}"}


# --------------------------------------------------------------------------- #
# having_ip                                                                    #
# --------------------------------------------------------------------------- #

def having_ip() -> bool:
    """Check whether an Internet connection is available."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# normalize                                                                    #
# --------------------------------------------------------------------------- #

def normalize(
    x: Union[np.ndarray, list, pd.Series],
    old_min: float,
    old_max: float,
    new_min: float = 0.0,
    new_max: float = 1.0,
) -> np.ndarray:
    """Linearly rescale *x* from ``[old_min, old_max]`` to ``[new_min, new_max]``."""
    x = np.asarray(x, dtype=float)
    return new_min + (x - old_min) / (old_max - old_min) * (new_max - new_min)


# --------------------------------------------------------------------------- #
# check_package_versions (informational)                                       #
# --------------------------------------------------------------------------- #

def check_package_versions() -> None:
    """Print version info for key dependencies."""
    import sys

    print(f"Python {sys.version}")

    for pkg_name in ["numpy", "pandas", "scipy", "matplotlib", "seaborn", "pingouin", "statsmodels"]:
        try:
            mod = __import__(pkg_name)
            print(f"  {pkg_name}: {mod.__version__}")
        except ImportError:
            print(f"  {pkg_name}: NOT INSTALLED")


# --------------------------------------------------------------------------- #
# not_empty assertion                                                          #
# --------------------------------------------------------------------------- #

def not_empty(x: Any, name: str = "input") -> None:
    """Raise ``ValueError`` if *x* is empty or ``None``."""
    if x is None:
        raise ValueError(f"{name} must not be None.")
    if isinstance(x, (pd.DataFrame, pd.Series)) and x.empty:
        raise ValueError(f"{name} must not be empty.")
    if isinstance(x, (list, tuple, np.ndarray)) and len(x) == 0:
        raise ValueError(f"{name} must not be empty.")
    if isinstance(x, str) and x.strip() == "":
        raise ValueError(f"{name} must not be an empty string.")
