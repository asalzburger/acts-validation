
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
         legend: bool = False,
         labelx: bool = True,
         labely: bool = True) -> pd.DataFrame:

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
                    yerr=np.abs(y_binned["sem"]), 
                    xerr=y_binned["xerr"],
                    label=yval,
                    color = style.get_color(), 
                    fmt = style.get_marker(), 
                    alpha = style.get_alpha())
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
# dStyles: the styles for each frame
# dDecos: the decorations for each frame
# rAx: the axis for the ratio plot
#
def overlay(ax, 
            dframes,
            xval : str, 
            yval : str, 
            bins : int, 
            brange : list,
            dStyles = {},
            dDecos = {},
            rAx = None) :
    
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
                      decos=dDeco,
                      labelx = rAx is None)
        
        if idf == 0 :
            lframe = pframe

        # plot the ratio plot
        if rAx is not None and idf > 0:
            rvals = pframe[yval] / lframe[yval]
            rAx.errorbar(x=lframe[xval], 
                              y=rvals,
                              yerr=np.abs(pframe[yval + "_err"] / lframe[yval]),
                              xerr=lframe[xval + "_err"],
                              label=yval,
                              color = dStyle.get_color(), 
                              fmt = dStyle.get_marker(), 
                              linewidth = dStyle.get_linewidth(), 
                              alpha = dStyle.get_alpha())
            rAx.set_xlabel(xval)
            rAx.set_ylabel("Ratio")
            rAx.axhline(1, color='black', linewidth=0.5)
            rAx.set_ylim(0.9*np.min(rvals),1.1*np.max(rvals))
            rAx.set_xlim(brange[0], brange[1])

    pass

     
