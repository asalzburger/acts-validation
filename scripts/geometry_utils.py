import acts

def geometry_id2dict(geoId : acts.GeometryIdentifier) -> dict:
    """ Convert a GeometryIdentifier to a dictionary """
    geoDict = {}
    geoDict["volume"] = geoId.volume()
    geoDict["layer"] = geoId.layer()
    geoDict["portal"] = geoId.boundary()
    geoDict["sensitive"] = geoId.sensitive()
    geoDict["passive"] = geoId.approach()
    geoDict["extra"] = geoId.extra()
    return geoDict

def geometry_id2str(geoId : acts.GeometryIdentifier, tags = list[str], appr : int = -1) -> str:
    """ Create a string representation of a GeometryIdentifier according to tags """
    geoDict = geometry_id2dict(geoId)
    geoStr = ""
    for itg, tag in enumerate(tags):
        if tag in geoDict:
            atag = tag[:appr]
            geoStr += atag+str(geoDict[tag])
            if itg < len(tags)-1:
                geoStr += "_"
    return geoStr
