""" This module provides a function to plot a profile plot and their ratios

    It also allows for decorations such as range plots and scatter plots as
    shown in underlying patterns.
"""

import pandas as pd
import numpy as np
from plotting import style

def plot(
    axs: list,
    dframe: pd.DataFrame,
    xval: str,
    bins: int,
    brange: list,
    yvals: list,
    pstyle: style.style = style.style(),
    decos: list = [],
    legend: bool = False,
    labelx: bool = True,
    labely: bool = True,
) -> pd.DataFrame:
    """Plot a profile plot"""

    # Check axes versus yval length
    if len(axs) != len(yvals):
        raise ValueError("Number of axes must match number of yvals")

    # Prepare the binning
    bin_ls = np.linspace(brange[0], brange[1], bins)
    bin_centers = 0.5 * (bin_ls[:-1] + bin_ls[1:])
    bin_width = (bin_ls[1:] - bin_ls[:-1]) / bins

    dframe["bin_idx"] = np.digitize(dframe[xval], bins=bin_ls)

    # grouby bin, so we can calculate stuff
    dframe_binned = dframe.groupby("bin_idx")

    dframe_r = pd.DataFrame()
    dframe_r[xval] = bin_centers
    dframe_r[xval + "_err"] = bin_width / 2

    for ax, yval in zip(axs, yvals):
        y_binned = dframe_binned[yval].agg(["mean", "sem"])
        y_binned["bin_center"] = bin_centers
        y_binned["xerr"] = bin_width / 2

        dframe_r[yval] = y_binned["mean"]
        dframe_r[yval + "_err"] = y_binned["sem"]

        # decorate with range
        if "range" in decos:
            rstyle = decos["range"]
            y_min_max = dframe_binned[yval].agg(["min", "max"])
            ax.fill_between(
                y_binned["bin_center"],
                y_min_max["min"],
                y_min_max["max"],
                alpha=rstyle.get_alpha(),
                color=rstyle.get_color(),
                linewidth=rstyle.get_linewidth(),
            )

        # decorate with scatter
        if "scatter" in decos:
            sstyle = decos["scatter"]
            ax.scatter(
                x = dframe[xval],
                y = dframe[yval],
                alpha=sstyle.get_alpha(),
                color=sstyle.get_color(),
                marker=sstyle.get_marker(),
                linewidth=sstyle.get_linewidth(),
            )

        # plot as errorbar
        ax.errorbar(
            x=y_binned["bin_center"],
            y=y_binned["mean"],
            yerr=np.abs(y_binned["sem"]),
            xerr=y_binned["xerr"],
            label=yval,
            color=pstyle.get_color(),
            fmt=pstyle.get_marker(),
            alpha=pstyle.get_alpha()
        )
        if labelx:
            ax.set_xlabel(xval)
        if labely:
            ax.set_ylabel(yval)

        if legend:
            ax.legend()

    return dframe_r


# Overlay a reference frame on top of a target frame
#
# ax: the axis to plot on
# dframes: the dataframes to plot
# xval: the x value to plot
# yval: the y value to plot
# bins: the number of bins
# brange: the range of the bins
# dstyles: the styles for each frame
# ddecos: the decorations for each frame
# rax: the axis for the ratio plot
#
def overlay(
    ax,
    dframes,
    xval: str,
    yval: str,
    bins: int,
    brange: list,
    dstyles=None,
    ddecos=None,
    rax=None,
):
    """Overlay profile plots, eventually with ratio"""

    lframe = None

    for idf, dframe in enumerate(dframes):
        # set the style
        if dstyles is not None and idf in dstyles:
            dstyle = dstyles[idf]
        else:
            dstyle = style.style()
        # set the decoration
        if ddecos is not None and idf in ddecos:
            ddeco = ddecos[idf]
        else:
            ddeco = {}

        pframe = plot(
            axs=[ax],
            dframe=dframe,
            xval=xval,
            bins=bins,
            brange=brange,
            yvals=[yval],
            pstyle=dstyle,
            decos=ddeco,
            labelx=rax is None,
        )

        if idf == 0:
            lframe = pframe

        # plot the ratio plot
        if rax is not None and idf > 0:
            rvals = pframe[yval] / lframe[yval]
            rax.errorbar(
                x=lframe[xval],
                y=rvals,
                yerr=np.abs(pframe[yval + "_err"] / lframe[yval]),
                xerr=lframe[xval + "_err"],
                label=yval,
                color=dstyle.get_color(),
                fmt=dstyle.get_marker(),
                linewidth=dstyle.get_linewidth(),
                alpha=dstyle.get_alpha(),
            )
            rax.set_xlabel(xval)
            rax.set_ylabel("Ratio")
            rax.axhline(1, color="black", linewidth=0.5)
            rax.set_ylim(0.9 * np.min(rvals), 1.1 * np.max(rvals))
            rax.set_xlim(brange[0], brange[1])
