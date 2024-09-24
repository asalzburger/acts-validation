""" ACTS related utility functions"""

import numpy as np

def geoid_to_vol(volume):
    """Extract the volume information from a 64 bit integer"""
    return (volume & 0xFF00000000000000) >> 56

def geoid_to_portal(value):
    """Extract the portal information from a 64 bit integer"""
    return (value & 0x00FF000000000000) >> 48

def geoid_to_layer(value):
    """Extract the layer information from a 64 bit integer"""
    return (value & 0x0000FFF000000000) >> 36

def geoid_to_approach(value):
    """Extract the approach information from a 64 bit integer"""
    return (value & 0x0000000FF0000000) >> 28

def geoid_to_sensitive(value):
    """Extract the sensitive information from a 64 bit integer"""
    return (value & 0x000000000FFFFF00) >> 8

def geoid_to_extra(value):
    """Extract the extra information from a 64 bit integer"""
    return value & 0x00000000000000FF

def geoid_to_ids(value):
    """Extract the volume, layer, approach, passive, sensitive and extra information from a 64 bit integer"""
    volume = geoid_to_vol(value)
    portal = geoid_to_portal(value)
    layer = geoid_to_layer(value)
    approach = geoid_to_approach(value)
    sensitive = geoid_to_sensitive(value)
    extra = geoid_to_extra(value)

    return volume, portal, layer, approach, sensitive, extra

# Vectorized versions
np_geoid_to_vol = np.vectorize(geoid_to_vol)
np_geoid_to_portal = np.vectorize(geoid_to_portal)
np_geoid_to_layer = np.vectorize(geoid_to_layer)
np_geoid_to_approach = np.vectorize(geoid_to_approach)
np_geoid_to_sensitive = np.vectorize(geoid_to_sensitive)
np_geoid_to_extra = np.vectorize(geoid_to_extra)
np_geoid_to_ids = np.vectorize(geoid_to_ids)
