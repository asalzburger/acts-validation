import argparse
import acts

def build( args : argparse.Namespace,
           gContext : acts.GeometryContext,
           logLevel : acts.logging.Level,
           materialDecorator = None):

    storage = {}

    # Build the detector for Gen1 - for the moment only ODD
    from acts.examples.odd import getOpenDataDetector
    detector = getOpenDataDetector(None)
    trackingGeometry = detector.trackingGeometry()
    storage["Detector"] = detector
    storage["Volume"] = trackingGeometry.highestTrackingVolume
    storage["SurfaceByIdentifier"] = trackingGeometry.geoIdSurfaceMap()

    return trackingGeometry, storage