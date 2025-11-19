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
    
    p.add_argument(
        "--detray", action='store_true'
    )

    p.add_argument(
        "--svg", action='store_true', help="Output SVG visualizations of each layer"
    )
    # indicate a list of integers for volumes to be displayed in SVG
    p.add_argument(
        "--svg-volumes", type=int, nargs='*', default=[], help="List of volume indices to output as SVG"
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
    
    if args.detray :
         from acts import detray
         from acts import examples
         # Translate the Gen2 detector to detray and compare that
         detrayOptions = acts.detray.DetrayConverter.Options()
         detrayOptions.convertSurfaceGrids = True
         detrayOptions.writeToJson = args.output != ""
         detrayStore = acts.examples.traccc.convertDetectorHost(gContext, detector, detrayOptions)
         
    if args.svg :
        from acts import svg

        # SVG style output
        surfaceStyle = acts.svg.Style()
        
        surfaceOptions = acts.svg.SurfaceOptions()
        surfaceOptions.style = surfaceStyle

        volumeOptions = acts.svg.DetectorVolumeOptions()
        volumeOptions.surfaceOptions = surfaceOptions
            
        gridOptions = acts.svg.GridOptions()
        gridOptions.style.fillColor = [0, 0, 0]
        gridOptions.style.fillOpacity = 0.
        gridOptions.style.strokeColor = [255, 0, 0]
        gridOptions.style.strokeWidth = 1

        indexedSurfacesOptions = acts.svg.IndexedSurfacesOptions()
        indexedSurfacesOptions.gridOptions = gridOptions

        volumeOptions.indexedSurfacesOptions = indexedSurfacesOptions

        for ivol, volume in enumerate(detector.volumes()):
            if len(volume.surfaces()) == 0:
                continue
            else :
                if len(args.svg_volumes) > 0 and ivol not in args.svg_volumes :
                    continue    
                # Generate SVG for this volume                
                identification = "IndexedSurfaces_vol"+str(ivol)
                protoVolume, protoIndexedGrid = acts.svg.convertDetectorVolume(gContext, volume, volumeOptions)
                svgIndexedSurfaces = acts.svg.drawIndexedSurfaces(protoIndexedGrid, identification)
                svgFile = acts.svg.file()
                svgFile.add_object(svgIndexedSurfaces)
                svgFile.write(args.output + "_" + identification + ".svg")



if "__main__" == __name__:
    main()