#!/usr/bin/env python
""" This script allows to investigate the mapping structure of
    the Acts material mapping
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
    "-i", "--input", type=str, default="", help="Input file with material tracks"
)

p.add_argument(
    "-t", "--tree", type=str, default="material-tracks", help="Tree name of the output files"
)

args = p.parse_args()

urf = uproot.open(args.input+":"+args.tree)

df = pd.DataFrame({"mat_z" : urf["mat_z"].array(library="np"),
                    "mat_r" : urf["mat_r"].array(library="np")})

fig, ax = plt.subplots()

df.scatter(x="mat_z", y="mat_r", color="blue", marker=".", dpi=100, ax=ax)
