""" Unit test for profile plotting"""
#!/usr/bin/env python3
import unittest
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from plotting import profile
from plotting import style

N_TESTS = 100000
brange = (-10, 10 )
xvals = np.random.uniform(brange[0], brange[1], N_TESTS)

def generate_data(noise_level = 10, offset = 2) :
    """ This method generates random test data for the unit tests"""

    # generate some random data
    noise = np.random.normal(0, noise_level, N_TESTS)
    yvals = [ x**2 for x in xvals ]
    yvals = yvals + noise
    noise = np.random.normal(0, noise_level, N_TESTS)
    zvals = [ (x**2 + offset) for x in xvals ]
    zvals = zvals + noise
    bdata = pd.DataFrame({'x': xvals, 'y': yvals, 'z': zvals})
    return bdata

stdata = generate_data(5)
dtdata = generate_data(25)
rtdata = generate_data(5)

class TestProfiles(unittest.TestCase):
    """ Test the profile plotting with a TestCase class """

    # Test a single profile plot
    def test_profile_single(self):
        """ This tests a single profile plot """

        fig, ax = plt.subplots()
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y'],
                     axs= [ax])
        fig.savefig('test_profile_single.png')

    # Test a single profile plot
    def test_profile_single_red(self):
        """ This tests a single profile plot, change the color """

        fig, ax = plt.subplots()
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y'],
                     axs= [ax],
                     pstyle = style.Style(color='red'))
        fig.savefig('test_profile_single_red.png')

    # Test a single profile plot with range
    def test_profile_single_range(self):
        """ This tests a single profile plot, with range decoration """

        fig, ax = plt.subplots()
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y'],
                     axs= [ax],
                     decos={'range' : style.Style(color='green', alpha=0.2)})
        fig.savefig('test_profile_single_range.png')

    # Test a single profile plot with scatter
    def test_profile_single_scatter(self):
        """ This tests a single profile plot, with scatter decoration """

        fig, ax = plt.subplots()
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y'],
                     axs= [ax],
                     decos={'scatter': style.Style(color='red', marker='.', alpha=0.1)})
        fig.savefig('test_profile_single_scatter.png')

    # Test a single profile plot with scatter
    def test_profile_single_ragne_scatter(self):
        """ This tests a single profile plot, with range & scatter decoration """

        fig, ax = plt.subplots()
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y'],
                     axs= [ax],
                     decos={
                         'range': style.Style(color='green', alpha=0.2),
                         'scatter': style.Style(color='red', marker='.', alpha=0.1)})
        fig.savefig('test_profile_single_range_scatter.png')

    # Test a two profile plots
    def test_profile_two_plots(self):
        """ This tests a two profile plots, side by side """

        fig, axs = plt.subplots(1,2, figsize=(10,5))
        profile.plot(dframe = stdata,
                     xval='x',
                     bins=50,
                     brange=brange,
                     yvals=['y', 'z'],
                     axs= axs)
        fig.savefig('test_profile_two_plots.png')

    # Test ratio of two profile plots
    def test_profile_two_overlaid(self):
        """ This tests two profile plots, olverlaid """

        fig, ax = plt.subplots()
        profile.overlay(ax=ax,
                        dframes = [stdata, dtdata],
                        xval='x',
                        yval = 'y',
                        bins=50,
                        brange=brange,
                        dstyles = { 0 : style.Style(color='red'),
                                    1 : style.Style(color='blue')},
                        ddecos = { 0 : {'range' : style.Style(color='red', alpha=0.1)},
                                   1 : {'range' : style.Style(color='blue', alpha=0.1)}})
        fig.savefig('test_profile_two_overlaid.png')

     # Test ratio of two profile plots with ratio plot
    def test_profile_two_overlaid_ratio(self):
        """ This tests two profile plots, olverlaid and ar ratio plot """

        fig, axs = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        fig.subplots_adjust(hspace=0.05)

        profile.overlay(ax=axs[0],
                        dframes = [stdata, rtdata],
                        xval='x',
                        yval = 'y',
                        bins=50,
                        brange=brange,
                        dstyles = { 0 : style.Style(color='red'),
                                    1 : style.Style(color='blue')},
                        ddecos = { 0 : {'range' : style.Style(color='red', alpha=0.1)},
                                   1 : {'range' : style.Style(color='blue', alpha=0.1)}},
                        rax = axs[1])
        fig.savefig('test_profile_two_overlaid_ratio.png')

if __name__ == '__main__':
    unittest.main()
