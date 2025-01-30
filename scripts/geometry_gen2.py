import argparse
import acts


""" This adds the geometry related arguments to the parser"""
def add_arguments(p : argparse.ArgumentParser):
    p.add_argument(
        "-q",
        "--queries",
        type=str,
        nargs="+",
        default=["ITk"],
        help="List of Queries for Published full phys volumes",
    )

    p.add_argument(
        "--table-name",
        type=str,
        default="ActsBlueprint",
        help="Name of the blueprint table",
    )

    p.add_argument(
        "--top-node",
        type=str,
        default="ITk",
        help="Name of the top node in the blueprint tree",
    )

    p.add_argument(
        "--top-node-bounds",
        type=str,
        default="",
        help="Table entry string overriding the top node bounds",
    )

def build( args : argparse.Namespace,
           gContext : acts.GeometryContext,
           logLevel : acts.logging.Level,
           materialDecorator = None):

    detector = None
    storage = {}

    if args.input != "":
        # GeoModel import necessary
        from acts import geomodel as gm
        print(">>> Reading the geometry model from GeoModel file:", args.input)
        # Read the geometry model from the database
        gmTree = acts.geomodel.readFromDb(args.input)

        gmFactoryConfig = gm.GeoModelDetectorObjectFactory.Config()
        gmFactory = gm.GeoModelDetectorObjectFactory(gmFactoryConfig, logLevel)

        # The options
        gmFactoryOptions = gm.GeoModelDetectorObjectFactory.Options()
        gmFactoryOptions.queries = args.queries
        # The Cache & construct call
        gmFactoryCache = gm.GeoModelDetectorObjectFactory.Cache()
        gmFactory.construct(gmFactoryCache, gContext, gmTree, gmFactoryOptions)

        # All surfaces from GeoModel
        gmSurfaces = [ss[1] for ss in gmFactoryCache.sensitiveSurfaces]

        # Construct the building hierarchy
        gmBlueprintConfig = gm.GeoModelBlueprintCreater.Config()
        gmBlueprintConfig.detectorSurfaces = gmSurfaces
        gmBlueprintConfig.kdtBinning = [acts.AxisDirection.AxisZ, acts.AxisDirection.AxisR]

        gmBlueprintOptions = gm.GeoModelBlueprintCreater.Options()
        gmBlueprintOptions.table = args.table_name
        gmBlueprintOptions.topEntry = args.top_node
        if len(args.top_node_bounds) > 0:
            gmBlueprintOptions.topBoundsOverride = args.top_node_bounds

        gmBlueprintCreater = gm.GeoModelBlueprintCreater(gmBlueprintConfig, logLevel)
        gmBlueprint = gmBlueprintCreater.create(gContext, gmTree, gmBlueprintOptions)

        gmCylindricalBuilder = gmBlueprint.convertToBuilder(logLevel)

        # Top level geo id generator
        gmGeoIdConfig = acts.GeometryIdGenerator.Config()
        gmGeoIdGenerator = acts.GeometryIdGenerator(
            gmGeoIdConfig, "GeoModelGeoIdGenerator", logLevel
        )

        # Create the detector builder
        gmDetectorConfig = acts.DetectorBuilder.Config()
        gmDetectorConfig.name = args.top_node + "_DetectorBuilder"
        gmDetectorConfig.builder = gmCylindricalBuilder
        gmDetectorConfig.geoIdGenerator = gmGeoIdGenerator
        gmDetectorConfig.materialDecorator = materialDecorator
        gmDetectorConfig.auxiliary = (
            "GeoModel based Acts::Detector from '" + args.input + "'"
        )

        gmDetectorBuilder = acts.DetectorBuilder(gmDetectorConfig, args.top_node, logLevel)
        detector = gmDetectorBuilder.construct(gContext)
        storage["GeoModelCache"] = gmFactoryCache
        storage["GeoModelTree"] = gmTree
    else :
        print(">>> Building OpenDataDetector")
        from acts.examples.odd import getOpenDataDetectorDirectory
        import acts.examples.dd4hep as acts_dd4hep

        odd_xml = getOpenDataDetectorDirectory() / "xml" / "OpenDataDetector.xml"

        print("Using the following xml file: ", odd_xml)

        # Create the dd4hep geometry service and detector
        dd4hepConfig = acts_dd4hep.DD4hepGeometryService.Config()
        dd4hepConfig.logLevel = acts.logging.INFO
        dd4hepConfig.xmlFileNames = [str(odd_xml)]
        dd4hepGeometryService = acts_dd4hep.DD4hepGeometryService(dd4hepConfig)
        dd4hepDetector = acts_dd4hep.DD4hepDetector(dd4hepGeometryService)

        cOptions = acts_dd4hep.DD4hepDetectorOptions(logLevel=acts.logging.INFO,
                                                     emulateToGraph="",
                                                     materialDecorator=materialDecorator)

        # Context and options
        geoContext = acts.GeometryContext()
        [detector, contextors, store] = dd4hepDetector.finalize(geoContext, cOptions)
        # Keep track of the storage
        storage["Contextors"] = contextors
        storage["DD4hepStore"] = store
        storage["Detector"] = dd4hepDetector

    # Create the hightest Tracking volume
    storage["Volume"] = detector.cylindricalVolumeRepresentation(gContext)

    surfaceByIdentifier = {}
    for volume in detector.volumes():
        for surface in volume.surfaces():
            surfaceByIdentifier[surface.geometryId()] = surface

    storage["SurfaceByIdentifier"] = surfaceByIdentifier

    return detector, storage

