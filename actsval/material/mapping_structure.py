#!/usr/bin/env python
""" This script allows to investigate the mapping structure of
    the Acts material mapping
"""

import argparse
import math
import uproot
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import alive_progress

from plotting import style
from plotting import profile
from utils import acts_utils, algebra_utils

p = argparse.ArgumentParser()

p.add_argument(
    "-i", "--input", type=str, default="", help="Input file with material tracks"
)

p.add_argument(
    "-o", "--output", type=str, default="mapping_structure", help="Output file name (base)"
)

p.add_argument(
    "--dist-threshold", type=float, default=50, help="Distance threshold for the mapping"
)


p.add_argument(
    "-t", "--tree", type=str, default="material-tracks", help="Tree name of the output files"
)

p.add_argument(
    "-e", "--entries", type=int, default="100000", help="Number of entries shown in the histograms"
)

p.add_argument(
    "--pickle", action="store_true", help="Save the data to a pickle file"
)


args = p.parse_args()

dframe = None

# If the input is a pickle file, load it
if args.input.endswith(".pkl") or args.input.endswith(".pickle"):
    dframe = pd.read_pickle(args.input)
    print(">>> Loaded the data from", args.input)
elif args.input.endswith(".root"):
    urf = uproot.open(args.input+":"+args.tree)
    print(">>> Preparing the data for", args.entries, "entries")

    # material positions
    with alive_progress.alive_bar(10) as bar:
        mat_x = np.concatenate(urf["mat_x"].array(library="np")[0:args.entries])
        bar()
        mat_y = np.concatenate(urf["mat_y"].array(library="np")[0:args.entries])
        bar()
        mat_z = np.concatenate(urf["mat_z"].array(library="np")[0:args.entries])
        bar()
        mat_r = np.concatenate(urf["mat_r"].array(library="np")[0:args.entries])
        bar()

        # mapping positions
        sur_x = np.concatenate(urf["sur_x"].array(library="np")[0:args.entries])
        bar()
        sur_y = np.concatenate(urf["sur_y"].array(library="np")[0:args.entries])
        bar()
        sur_z = np.concatenate(urf["sur_z"].array(library="np")[0:args.entries])
        bar()
        sur_r = np.concatenate(urf["sur_r"].array(library="np")[0:args.entries])
        bar()

        sur_id = np.concatenate(urf["sur_id"].array(library="np")[0:args.entries])
        bar()

        diff = algebra_utils.np_distance(mat_x, mat_y, mat_z, sur_x, sur_y, sur_z)
        bar()

        dframe = pd.DataFrame({"mat_x": mat_x,
                       "mat_y": mat_y,
                       "mat_z": mat_z,
                       "mat_r": mat_r,
                       "sur_x": sur_x,
                       "sur_y": sur_y,
                       "sur_z": sur_z,
                       "sur_r": sur_r,
                       "sur_id": sur_id,
                       "diff": diff})
        if args.pickle:
            dframe.to_pickle(args.output+".pkl")
            print(">>> Saved the data to", args.output+".pkl")

        print(">>> Found",np.unique_counts(sur_id), "geo ids int the mapping dataset")
else:
    print(">>> The input file is not a ROOT file or a pickle file")
    print(">>> Please provide a ROOT file or a pickle file")
    exit(1)

print(">>> Found", len(dframe), "entries in the dataset")

fig, axs = plt.subplots(1, 2, dpi=100, figsize=(13,6))

# z/r view
for usid in np.unique(dframe["sur_id"]):
    axs[0].scatter(dframe["mat_z"][dframe["sur_id"] == usid][0:args.entries],
                   dframe["mat_r"][dframe["sur_id"] == usid][0:args.entries],
                   alpha=0.05, s=0.1, linewidths=0)

    axs[0].scatter(dframe["sur_z"][dframe["sur_id"] == usid][0:args.entries],
                   dframe["sur_r"][dframe["sur_id"] == usid][0:args.entries],
                   s=0.2, linewidths=0, color="black")
    axs[0].set_xlabel("z [mm]")
    axs[0].set_ylabel("r [mm]")

axs[0].scatter(dframe["mat_z"][dframe["diff"] > args.dist_threshold][0:args.entries],
                dframe["mat_r"][dframe["diff"] > args.dist_threshold][0:args.entries],
                s=0.1, color='red')

# mapping distance
axs[1].hist(dframe["diff"][0:args.entries], bins=100, range=(0,200))
axs[1].set_yscale("log")
axs[1].set_xlabel("Mapping distance [mm]")
axs[1].set_ylabel("Entries/bin")

# Plot, however, limit the number of entries
#
fig.show()



