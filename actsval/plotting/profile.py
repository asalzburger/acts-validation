
#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotting import style

def plot(axs: list,
         dframe: pd.DataFrame,
         xval: str, bins: int, brange: list, 
         yvals: list, 
         style: style = style.style(),
         decos: list = [],
         legend: bool = False):

    # Check axes versus yval length
    if len(axs) != len(yvals):
        raise ValueError("Number of axes must match number of yvals")

    # Prepare the binning
    bin_ls = np.linspace(brange[0], brange[1], bins)
    bin_centers = 0.5 * (bin_ls[:-1] + bin_ls[1:])
    bin_width = (bin_ls[1:] - bin_ls[:-1])/bins

    dframe["bin_idx"] = np.digitize(dframe[xval], bins=bin_ls)

    # grouby bin, so we can calculate stuff
    dframe_binned = dframe.groupby("bin_idx")

    dframe_r = pd.DataFrame()
    dframe_r[xval] = bin_centers
    dframe_r[xval + "_err"] = bin_width / 2

    for i, (ax, yval) in enumerate(zip(axs, yvals)):
        y_binned = dframe_binned[yval].agg(["mean", "sem"])
        y_binned["bin_center"] = bin_centers
        y_binned["xerr"] = bin_width / 2

        dframe_r[yval] = y_binned["mean"]
        dframe_r[yval + "_err"] = y_binned["sem"]

        # decorate with range
        if "range" in decos:
            rstyle = decos["range"]
            y_min_max = dframe_binned[yval].agg(["min", "max"])
            ax.fill_between(y_binned["bin_center"],
                            y_min_max["min"], 
                            y_min_max["max"],
                            alpha=rstyle.get_alpha(), 
                            color=rstyle.get_color(),
                            linewidth = rstyle.get_linewidth())

        # decorate with scatter
        if "scatter" in decos:
            sstyle = decos["scatter"]
            ax.scatter(dframe[xval], 
                       dframe[yval], 
                       alpha=sstyle.get_alpha(), 
                       color=sstyle.get_color(),
                       marker = sstyle.get_marker(),
                       linewidth = sstyle.get_linewidth())

        # plot as errorbar
        ax.errorbar(x=y_binned["bin_center"], 
                    y=y_binned["mean"],
                    yerr=y_binned["sem"], 
                    xerr=y_binned["xerr"],
                    fmt="o", 
                    label=yval,
                    color = style.get_color(), 
                    marker = style.get_marker(), 
                    linewidth = style.get_linewidth(), 
                    alpha = style.get_alpha())
        ax.set_xlabel(xval)
        ax.set_ylabel(yval)

        if legend:
            ax.legend()
    
    return dframe_r


# Overlay a reference frame on top of a target frame
def overlay(ax, 
            dframes,
            xval : str, 
            yval : str, 
            bins : int, 
            brange : list,
            dStyles = {},
            dDecos = {},
            ratio_ax = None) :
    
    for idf, (dframe, dStyle) in enumerate(zip(dframes, dStyles)):
        # set the style
        if idf in dStyles:
            dStyle = dStyles[idf]
        else:
            dStyle = style.style()
        # set the decoration
        if idf in dDecos:
            dDeco = dDecos[idf]
        else:
            dDeco = {}
    
        pframe = plot(axs=[ax], 
                      dframe=dframe, 
                      xval=xval, 
                      bins=bins, 
                      brange=brange, 
                      yvals=[yval], 
                      style = dStyle,
                      decos=dDeco)

    pass

     
