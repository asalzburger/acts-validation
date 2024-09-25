import argparse
import math

""" Add specific arguments for particle generation"""
def add_arguments( p : argparse.ArgumentParser):

    p.add_argument("-t", "--tracks", type=int, default=100, help="Number of Tracks per event")

    p.add_argument("--eta-range", nargs=2, type=float, default=(-4.,4.), help="Eta range")

    p.add_argument("--phi-range", nargs=2, type=float, default=(-math.pi,math.pi), help="Phi range")

    p.add_argument("--pt-range", nargs=2, type=float, default=(0.1, 100.), help="Transverse momentum range [GeV]")
