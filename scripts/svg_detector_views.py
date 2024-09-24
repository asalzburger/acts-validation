import acts
import argparse
from acts import examples

def main():
    p = argparse.ArgumentParser()

    p.add_argument("-i", "--input", type=str, default="", help="Input SQL file")

    p.add_argument(
        "-o", "--output", type=str, default="GeoModel", help="Output file(s) base name"
    )

    p.add_argument(
        "-q",
        "--queries",
        type=str,
        nargs="+",
        default="GeoModelXML",
        help="List of Queries for Published full phys volumes",
    )

    p.add_argument(
        "--table-name",
        type=str,
        default="ActsBlueprint",
        help="Name of the blueprint table",
    )

    p.add_argument(
        "-t",
        "--top-node",
        type=str,
        default="",
        help="Name of the top node in the blueprint tree",
    )

    p.add_argument(
        "-b",
        "--top-node-bounds",
        type=str,
        default="",
        help="Table entry string overriding the top node bounds",
    )

    args = p.parse_args()

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    materialDecorator = None
    detector = None

    print (">>> Building the detector in ACTS Gen2 format")
    if args.input != "":
        # GeoModel import necessary
        from acts import geomodel as gm
        print(">>> Reading the geometry model from GeoModel file:", args.input)
        # Read the geometry model from the database
        gmTree = acts.geomodel.readFromDb(args.input)

        gmFactoryConfig = gm.GeoModelDetectorObjectFactory.Config()
        gmFactoryConfig.materialList = args.material_list
        gmFactoryConfig.nameList = args.name_list
        gmFactoryConfig.convertSubVolumes = args.convert_subvols
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
        gmBlueprintConfig.kdtBinning = [acts.Binning.z, acts.Binning.r]

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
    else :
        print(">>> Building OpenDataDetector")
        from acts.examples.odd import getOpenDataDetectorDirectory


        odd_xml = getOpenDataDetectorDirectory() / "xml" / "OpenDataDetector.xml"

        print("Using the following xml file: ", odd_xml)

        # Create the dd4hep geometry service and detector
        dd4hepConfig = DD4hepGeometryService.Config()
        dd4hepConfig.logLevel = acts.logging.INFO
        dd4hepConfig.xmlFileNames = [str(odd_xml)]
        dd4hepGeometryService = DD4hepGeometryService(dd4hepConfig)
        dd4hepDetector = DD4hepDetector(dd4hepGeometryService)

        cOptions = DD4hepDetectorOptions(logLevel=acts.logging.INFO, emulateToGraph="")


        # Context and options
        geoContext = acts.GeometryContext()
        [detector, contextors, store] = dd4hepDetector.finalize(geoContext, cOptions)



if "__main__" == __name__:
    main()


