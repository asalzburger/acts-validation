import acts
import argparse
import geometry_gen2


def main():
    p = argparse.ArgumentParser()

    p.add_argument("-i", "--input", type=str, default="", help="Input SQL file")

    p.add_argument(
        "-o", "--output", type=str, default="detector", help="Output file(s) base name"
    )

    p.add_argument(
        "--output-internals",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Write out the internal objects")

    p.add_argument(
        "-m", "--map", type=str, default="", help="Input file for the material map"
    )

    p.add_argument(
        "--surface-rgb",
        nargs=3,
        type=int,
        default=[66, 182, 245],
        help="Color RGB for surfaces",
    )

    p.add_argument(
        "--surface-opacity",
        type=float,
        default=0.75,
        help="Color RGB opacity for surfaces",
    )

    p.add_argument(
        "--surface-highlight-rgb",
        nargs=3,
        type=int,
        default=[245, 182, 66],
        help="Color Highlight RGB for surfaces",
    )

    p.add_argument(
        "--surface-stroke-rgb",
        nargs=3,
        type=int,
        default=[33, 120, 245],
        help="Color RGB for surface strokes",
    )

    # Add Gen2 related arguments
    geometry_gen2.add_arguments(p)

    p.add_argument(
        "--rz-view-box",
        type=float,
        nargs="+",
        default=[],
        help="Vie box in rz (if configured)",
    )

    p.add_argument(
        "--eta-z-max",
        type=float,
        default=4000.0,
        help="Maximum z value for eta lines",
    )

    p.add_argument(
        "--eta-r-max",
        type=float,
        default=1000.0,
        help="Maximum r value for eta lines",
    )

    p.add_argument(
        "--eta-main-lines",
        nargs="+",
        type=float,
        default=[],
        help="Draw the main eta lines",
    )

    p.add_argument(
        "--eta-main-label-size",
        type=float,
        default=20,
        help="Draw the main eta lines",
    )

    p.add_argument(
        "--eta-main-stroke-width",
        type=float,
        default=2,
        help="Draw the main eta lines",
    )

    p.add_argument(
        "--eta-sub-lines",
        nargs="+",
        type=float,
        default=[],
        help="Draw the main eta lines",
    )

    p.add_argument(
        "--eta-sub-stroke-width",
        type=float,
        default=2,
        help="Draw the main eta lines",
    )

    p.add_argument(
        "--eta-sub-stroke-dash",
        nargs="+",
        type=int,
        default=[4, 4],
        help="Draw the main eta lines",
    )

    args = p.parse_args()

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    materialDecorator = None

    print(">>> Building the detector in ACTS Gen2 format")
    detector, storage = geometry_gen2.build(args, gContext, logLevel, materialDecorator)

    if detector is not None:
        # SVG style output
        surfaceStyle = acts.svg.Style()
        surfaceStyle.fillColor = args.surface_rgb
        surfaceStyle.fillOpacity = args.surface_opacity
        surfaceStyle.highlightColor = args.surface_highlight_rgb
        surfaceStyle.strokeColor = args.surface_stroke_rgb

        surfaceOptions = acts.svg.SurfaceOptions()
        surfaceOptions.style = surfaceStyle

        viewRange = acts.Extent([])
        volumeOptions = acts.svg.DetectorVolumeOptions()
        volumeOptions.surfaceOptions = surfaceOptions

        # X-y view
        xyRange = acts.Extent([[acts.BinningValue.binZ, [-50, 50]]])
        xyView = acts.svg.drawDetector(
            gContext,
            detector,
            "odd",
            [[ivol, volumeOptions] for ivol in range(detector.numberVolumes())],
            [["xy", ["sensitives"], xyRange]])

        # ZR view
        zrRange = acts.Extent([[acts.BinningValue.binPhi, [-0.1, 0.1]]])
        zrView = acts.svg.drawDetector(
            gContext,
            detector,
            "odd",
            [[ivol, volumeOptions] for ivol in range(detector.numberVolumes())],
            [["zr", ["sensitives", "portals"], zrRange]])

        etaLines = acts.svg.drawEtaLines("eta_lines",
                                         args.eta_z_max, args.eta_r_max,
                                         args.eta_main_lines,
                                         args.eta_main_stroke_width,
                                         args.eta_main_label_size, True,
                                         args.eta_sub_lines,
                                         args.eta_sub_stroke_width,
                                         args.eta_sub_stroke_dash,
                                         10, False)

        # Create the z r file
        zrFile = acts.svg.file()
        zrFile.addObjects(zrView)
        zrFile.addObject(etaLines)
        # Clip if configured
        if len(args.rz_view_box) == 4 :
            zrFile.clip(args.rz_view_box)
        # Write it out
        zrFile.write(args.output+"_zr.svg")


        if args.output_internals :

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
                    identification = "IndexedSurfaces_vol"+str(ivol)
                    protoVolume, protoIndexedGrid = acts.svg.convertDetectorVolume(gContext, volume, volumeOptions)
                    xyIndexedSurfaces = acts.svg.drawIndexedSurfaces(protoIndexedGrid, identification)
                    xyFile = acts.svg.file()
                    xyFile.addObject(xyIndexedSurfaces)
                    xyFile.write(args.output + "_" + identification + ".svg")

                #volumeFile = acts.svg.file()
                #volumeFile.addObjects(acts.svg.drawVolume(volume, surfaceOptions))
                #volumeFile.write(args.output + "_" + volume.name() + ".svg")


if "__main__" == __name__:
    main()