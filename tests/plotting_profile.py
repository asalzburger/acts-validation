#!/usr/bin/env python3
import unittest
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import plotting.profile as profile
import plotting.style as style

ntests = 100000
brange = (-10, 10 )
xvals = np.random.uniform(brange[0], brange[1], ntests)

def generateData(noise_level = 10, offset = 2) :

    # generate some random data
    noise = np.random.normal(0, noise_level, ntests)
    yvals = [ x**2 for x in xvals ] 
    yvals = yvals + noise
    noise = np.random.normal(0, noise_level, ntests)
    zvals = [ (x**2 + offset) for x in xvals ] 
    zvals = zvals + noise
    bdata = pd.DataFrame({'x': xvals, 'y': yvals, 'z': zvals})
    return bdata

stdata = generateData(5)
dtdata = generateData(25)
rtdata = generateData(5)

class test_profiles(unittest.TestCase):

    # Test a single profile plot
    def test_profile_single(self):
  
        fig, ax = plt.subplots()
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y'], 
                     axs= [ax])
        fig.savefig('test_profile_single.png')
        pass

    # Test a single profile plot
    def test_profile_single_red(self):
  
        fig, ax = plt.subplots()
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y'], 
                     axs= [ax],
                     style = style.style(color='red'))
        fig.savefig('test_profile_single_red.png')
        pass

    # Test a single profile plot with range
    def test_profile_single_range(self):
  
        fig, ax = plt.subplots()
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y'], 
                     axs= [ax],
                     decos={'range' : style.style(color='green', alpha=0.2)})
        fig.savefig('test_profile_single_range.png')
        pass

    # Test a single profile plot with scatter
    def test_profile_single_scatter(self):
  
        fig, ax = plt.subplots()
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y'], 
                     axs= [ax],
                     decos={'scatter': style.style(color='red', marker='.', alpha=0.1)})
        fig.savefig('test_profile_single_scatter.png')
        pass

    # Test a single profile plot with scatter
    def test_profile_single_ragne_scatter(self):
  
        fig, ax = plt.subplots()
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y'], 
                     axs= [ax],
                     decos={
                         'range': style.style(color='green', alpha=0.2),
                         'scatter': style.style(color='red', marker='.', alpha=0.1)})
        fig.savefig('test_profile_single_range_scatter.png')
        pass

    # Test a two profile plots
    def test_profile_two_plots(self):
  
        fig, axs = plt.subplots(1,2, figsize=(10,5))
        profile.plot(dframe = stdata, 
                     xval='x', 
                     bins=50, 
                     brange=brange, 
                     yvals=['y', 'z'], 
                     axs= axs)
        fig.savefig('test_profile_two_plots.png')
        pass


    # Test ratio of two profile plots
    def test_profile_two_overlaid(self):
  
        fig, ax = plt.subplots()
        profile.overlay(ax=ax, 
                        dframes = [stdata, dtdata], 
                        xval='x', 
                        yval = 'y',
                        bins=50, 
                        brange=brange,
                        dStyles = { 0 : style.style(color='red'),
                                    1 : style.style(color='blue')},
                        dDecos = { 0 : {'range' : style.style(color='red', alpha=0.1)}, 
                                   1 : {'range' : style.style(color='blue', alpha=0.1)}})
        fig.savefig('test_profile_two_overlaid.png')
        pass

     # Test ratio of two profile plots with ratio plot
    def test_profile_two_overlaid_ratio(self):
        fig, axs = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        fig.subplots_adjust(hspace=0.05)

        profile.overlay(ax=axs[0], 
                        dframes = [stdata, rtdata], 
                        xval='x', 
                        yval = 'y',
                        bins=50, 
                        brange=brange,
                        dStyles = { 0 : style.style(color='red'),
                                    1 : style.style(color='blue')},
                        dDecos = { 0 : {'range' : style.style(color='red', alpha=0.1)}, 
                                   1 : {'range' : style.style(color='blue', alpha=0.1)}},
                        rAx = axs[1])
        fig.savefig('test_profile_two_overlaid_ratio.png')
        pass



if __name__ == '__main__':
    unittest.main()
