import acts
import argparse
import geometry_gen2

def main():
    p = argparse.ArgumentParser()

    p.add_argument("-i", "--input", type=str, default="", help="Input SQL file")

    p.add_argument(
        "-o", "--output", type=str, default="GeoModel", help="Output file(s) base name"
    )

    p.add_argument(
        "-m", "--map", type=str, default="", help="Input file for the material map"
    )

    # Add Gen2 related arguments
    geometry_gen2.add_arguments(p)

    args = p.parse_args()

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    materialDecorator = None
    if args.map != "":
        print("Loading a material decorator from file:", args.map)
        materialDecorator = acts.IMaterialDecorator.fromFile(args.map)

    detector, storage = geometry_gen2.build(args, gContext, logLevel, materialDecorator)

if "__main__" == __name__:
    main()