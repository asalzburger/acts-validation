#!/usr/bin/env python
""" This script is used to compare profiles
"""

import argparse
import math
import uproot
import matplotlib.pyplot as plt
import pandas as pd

from plotting import style
from plotting import profile

p = argparse.ArgumentParser()

p.add_argument(
    "-i", "--input", nargs="+", type=str, default="", help="Input file(s) with material tracks"
)

p.add_argument(
    "-t", "--tree", type=str, default="", help="Input tree"
)

p.add_argument(
    "-x", "--x-variables", nargs="+", type=str, default="", help="x values"
)

p.add_argument(
    "-y", "--y-variables", nargs="+", type=str, default="", help="y values"
)

p.add_argument(
    "-c", "--color", nargs="+", type=str, default="", help="Colors for the different materials"
)

p.add_argument(
    "-d", "--decorators", nargs="+", type=str, default="", help="Plot decorators"
)

p.add_argument(
    "-m", "--marker", nargs="+", type=str, default="", help="Marker sequence"
)

p.add_argument(
     "--figsize", nargs=2, type=float, default=(8,8), help="Figure size overwrite"
)

p.add_argument(
     "--eta-bins", type=int, default=60, help="Number of bins in eta"
)

p.add_argument(
     "--eta-range", nargs=2, type=float, default=(-4,4), help="Range of eta"
)

p.add_argument(
     "--phi-bins", type=int, default=60, help="Number of bins ein phi"
)

p.add_argument(
     "--phi-range", nargs=2, type=float, default=(-math.pi,math.pi), help="Range of phi plottint"
)

p.add_argument(
        "-o", "--output", type=str, default="", help="Output file (core) name"
)

args = p.parse_args()


# Prepare the data
dframes = []
dstyles = {}
ddecos  = {}



# Loop to load the data
for i, (input_file, color) in enumerate(zip(args.input, args.color)):
    urf = uproot.open(input_file+":"+args.tree)

    ddict = {}
    for x in args.x_variables:
        ddict[x] = urf[x].array(library="np")
    for y in args.y_variables:
        ddict[y] = urf[y].array(library="np")

    # Load the data as dataframe
    df =  pd.DataFrame(ddict)

    dframes.append(df)

    dstyles[i] = style.Style(color=color, marker=args.marker[i])
    decos = {}
    for d in args.decorators:
        if d == "range":
            decos[d] = style.Style(alpha=0.2, color=color)
        elif d == "scatter":
            decos[d] = style.Style(alpha=0.1, color=color)
    if len(decos) > 0:
        ddecos[i] = decos

# Eta plots
for x in args.x_variables:
    for y in args.y_variables:
        fig_eta, axs_eta = plt.subplots(2, 1,
                                figsize=args.figsize,
                                sharex=True,
                                gridspec_kw={'height_ratios': [2, 1]})
        fig_eta.subplots_adjust(hspace=0.05)

        profile.overlay(ax=axs_eta[0],
                dframes=dframes,
                xval=x,
                yval=y,
                bins=args.eta_bins,
                brange=args.eta_range,
                dstyles=dstyles,
                ddecos=ddecos,
                rax=axs_eta[1])
        axs_eta[0].grid(axis="x", linestyle="dotted")
        axs_eta[1].grid(axis="x", linestyle="dotted")
        fig_eta.show()