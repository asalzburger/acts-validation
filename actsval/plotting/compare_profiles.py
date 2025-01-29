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


def add_argumens(p: argparse.ArgumentParser):
    """Method to attach armens to the parser object"""

    p.add_argument(
        "-i",
        "--input",
        nargs="+",
        type=str,
        default="",
        help="Input file(s) with material tracks",
    )

    p.add_argument("-t", "--tree", type=str, default="", help="Input tree")

    p.add_argument(
        "-x", "--x-variables", nargs="+", type=str, default="", help="x values"
    )

    p.add_argument(
        "-y", "--y-variables", nargs="+", type=str, default="", help="y values"
    )

    p.add_argument("--x-labels", nargs="+", type=str, default="", help="x labels")

    p.add_argument("--x-label-size",  type=int, default=14, help="x label font size")

    p.add_argument("--y-labels", nargs="+", type=str, default="", help="y labels")

    p.add_argument("--y-label-size",  type=int, default=14, help="y label font size")

    p.add_argument(
        "-c",
        "--color",
        nargs="+",
        type=str,
        default="",
        help="Colors for the different materials",
    )

    p.add_argument(
        "-l", "--legends", nargs="+", type=str, default="", help="Plot legends"
    )

    p.add_argument(
        "-d", "--decorators", nargs="+", type=str, default="", help="Plot decorators"
    )

    p.add_argument(
        "-m", "--marker", nargs="+", type=str, default="", help="Marker sequence"
    )

    p.add_argument(
        "--figsize", nargs=2, type=float, default=(8, 8), help="Figure size overwrite"
    )

    p.add_argument(
        "--x-bins", nargs="+", type=int, default=[], help="Number of bins in x"
    )

    p.add_argument(
        "--x-ranges-min", nargs="+", type=float, default=[], help="Range min of x axes"
    )

    p.add_argument(
        "--x-ranges-max",
        nargs="+",
        type=float,
        default=[4, math.pi],
        help="Range max of x axes",
    )

    p.add_argument(
        "-o", "--output", type=str, default="", help="Output file (core) name"
    )


def run_comparison(args: argparse.Namespace):
    """Body of the script, taking the main arguments"""

    xlabel = args.x_labels
    ylabel = args.y_labels
    if len(args.x_variables) != len(args.x_labels):
        print(">> No x labels provided, using the variable names")
        xlabel = args.x_variables
    if len(args.y_variables) != len(args.y_labels):
        print(">> No y labels provided, using the variable names")
        ylabel = args.y_variables
    # No ranges given or no bins given
    if (
        len(args.x_ranges_min) != len(args.x_variables)
        or len(args.x_ranges_max) != len(args.x_variables)
        or len(args.x_bins) != len(args.x_variables)
    ):
        print(">> Ranges are not matching the variables")
        return

    # Prepare the data
    dframes = []
    dstyles = {}
    ddecos = {}

    # Loop to load the data
    for i, (input_file, color) in enumerate(zip(args.input, args.color)):
        urf = uproot.open(input_file + ":" + args.tree)
        print(">> Loading data from", input_file)
        ddict = {}
        for x in args.x_variables:
            ddict[x] = urf[x].array(library="np")
        for y in args.y_variables:
            ddict[y] = urf[y].array(library="np")

        # Load the data as dataframe and append
        df = pd.DataFrame(ddict)
        df.name = args.legends[i] if i < len(args.legends) else ""
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

    # The plots
    for ix, x in enumerate(args.x_variables):
        for y in args.y_variables:
            print(">> Profile for", x, "vs", y)
            fig, axs = plt.subplots(
                2,
                1,
                figsize=args.figsize,
                sharex=True,
                gridspec_kw={"height_ratios": [2, 1]},
            )
            fig.subplots_adjust(hspace=0.05)

            profile.overlay(
                ax=axs[0],
                dframes=dframes,
                xval=x,
                yval=y,
                bins=args.x_bins[ix],
                brange=(args.x_ranges_min[ix], args.x_ranges_max[ix]),
                dstyles=dstyles,
                ddecos=ddecos,
                rax=axs[1],
            )
            axs[0].grid(axis="x", linestyle="dotted")
            axs[0].set_ylabel(ylabel[ix], fontsize=args.y_label_size)
            if (args.legends is not None) and (len(args.legends) > 0):
                axs[0].legend(loc="best", fontsize=args.y_label_size)

            axs[1].grid(axis="x", linestyle="dotted")
            axs[1].set_xlabel(xlabel[ix], fontsize=args.x_label_size)
            axs[1].set_ylabel("Ratio", fontsize=args.y_label_size)
            fig.show()
            fig.savefig(args.output + "_" + x + "_vs_" + y + ".png")
            fig.savefig(args.output + "_" + x + "_vs_" + y + ".svg")
            


# The main function
if __name__ == "__main__":

    p_args = argparse.ArgumentParser(description=__doc__)
    add_argumens(p_args)
    t_args = p_args.parse_args()

    run_comparison(t_args)
