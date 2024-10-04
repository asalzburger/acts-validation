import acts
from acts import examples
import argparse
import geometry_gen2
import geometry_gen1


def main():
    p = argparse.ArgumentParser()

    p.add_argument("-i", "--input", type=str, default="", help="Input SQL file")

    p.add_argument(
        "-o", "--output", type=str, default="GeoModel", help="Output file(s) base name"
    )

    p.add_argument(
        "-m", "--map", type=str, default="", help="Input file for the material map"
    )

    p.add_argument("--material-surfaces-only",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Plot only material surfaces",
    )

    p.add_argument(
        "--surface-rgb",
        nargs=3,
        type=int,
        default=[5, 150, 245],
        help="Color RGB for surfaces",
    )

    p.add_argument(
        "--surface-opacity",
        type=float,
        default=0.5,
        help="Color RGB opacity for surfaces",
    )

    # Add Gen2 related arguments
    geometry_gen2.add_arguments(p)

    # The modes are
    # gen1: Gen1 detector
    # gen2: Gen2 detector
    # detray_gen2: Gen2 detector converted to detray
    p.add_argument(
        "--mode",
        type=str,
        default="gen2",
        choices=["gen1", "gen2", "detray_gen2" ],
        help="Convert to detray detector and run detray navigation and propagation",
    )

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

    # The material decorator
    materialDecorator = None


    # Build the acts geometry
    actsGeometry = None
    detectorStore = {}
    materialSurfaces = None
    if "gen1" in args.mode:
        print(">>> Building the detector for Gen1")
        # Build the detector for Gen1
        actsGeometry, detectorStore = geometry_gen1.build(args, gContext, logLevel, materialDecorator)
        if not args.material_surfaces_only:
            eventStore = acts.examples.WhiteBoard(name=f"EventStore#0", level=logLevel)
            context =  acts.examples.AlgorithmContext(0, 0, eventStore)
            actsSvgConfig = acts.examples.SvgTrackingGeometryWriter.Config()
            actsSvgWriter = acts.examples.SvgTrackingGeometryWriter(actsSvgConfig, logLevel)
            actsSvgWriter.write(context,actsGeometry)
        else :
            materialSurfaces = actsGeometry.extractMaterialSurfaces()

    elif "gen2" in args.mode:
        print(">>> Building the detector for Gen2")
        # Build the detector for Gen2 (also detray)
        actsGeometry, detectorStore = geometry_gen2.build(args, gContext, logLevel, materialDecorator)
        if not args.material_surfaces_only:
            # SVG style output
            surfaceStyle = acts.svg.Style()
            surfaceStyle.fillColor = args.surface_rgb
            surfaceStyle.fillOpacity = args.surface_opacity

            surfaceOptions = acts.svg.SurfaceOptions()
            surfaceOptions.style = surfaceStyle

            viewRange = acts.Extent([])
            volumeOptions = acts.svg.DetectorVolumeOptions()
            volumeOptions.surfaceOptions = surfaceOptions

            # X-y view
            xyRange = acts.Extent([[acts.BinningValue.binZ, [-50, 50]]])
            xyView = acts.svg.drawDetector(
                gContext,
                actsGeometry,
                "odd",
                [[ivol, volumeOptions] for ivol in range(actsGeometry.numberVolumes())],
                [["xy", ["sensitives"], xyRange]])

            # ZR view
            zrRange = acts.Extent([[acts.BinningValue.binPhi, [-0.1, 0.1]]])
            zrView = acts.svg.drawDetector(
                gContext,
                actsGeometry,
                "odd",
                [[ivol, volumeOptions] for ivol in range(actsGeometry.numberVolumes())],
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
        else :
            materialSurfaces = actsGeometry.extractMaterialSurfaces()

    if materialSurfaces is not None:
        print(">>> Drawing the material surfaces only")

        # Check drawing the material surfaces
        surfaceStyle = acts.svg.Style()
        surfaceStyle.fillColor = args.surface_rgb
        surfaceStyle.fillOpacity = args.surface_opacity

        surfaceOptions = acts.svg.SurfaceOptions()
        surfaceOptions.style = surfaceStyle

        protoMaterialSurfaces = [ acts.svg.convertSurface(gContext,
                                                          surface,
                                                          surfaceOptions)
                                  for surface in materialSurfaces ]

        materialSurfaces = [ acts.svg.viewSurface(pSurface, "material_surface_"+str(ip), "zr")
                             for ip, pSurface in enumerate(protoMaterialSurfaces) ]


        materialEtaLines = acts.svg.drawEtaLines("eta_lines",
                                            args.eta_z_max, args.eta_r_max,
                                            args.eta_main_lines,
                                            args.eta_main_stroke_width,
                                            args.eta_main_label_size, True,
                                            args.eta_sub_lines,
                                            args.eta_sub_stroke_width,
                                            args.eta_sub_stroke_dash,
                                            10, False)
        zrFile = acts.svg.file()
        zrFile.addObjects(materialSurfaces)
        zrFile.addObject(materialEtaLines)
        # Clip if configured
        if len(args.rz_view_box) == 4 :
            zrFile.clip(args.rz_view_box)
        # Write it out
        zrFile.write(args.output+"_material_surfaces_zr.svg")



if "__main__" == __name__:
    main()