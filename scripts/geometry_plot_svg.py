import acts
from acts import examples
import argparse
import geometry_gen2
import geometry_gen1
import geometry_utils

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

    p.add_argument("--material-surfaces-only",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Plot only material surfaces",
    )

    p.add_argument("--material-info-title-size",
        default=48,
        type=int,
        help="Size of the title of the material info box",
    )

    p.add_argument("--material-info-body-size",
        default=36,
        type=int,
        help="Size of the body of the material info box",
    )

    p.add_argument("--material-info-pos",
        default=(200,200),
        nargs=2,
        type=int,
        help="Position of the material info box",
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

    # The geometry modes are
    # gen1: Gen1 detector
    # gen2: Gen2 detector
    # detray_gen2: Gen2 detector converted to detray
    p.add_argument(
        "--geo-mode",
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
    if "gen1" in args.geo_mode:
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

    elif "gen2" in args.geo_mode:
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

            viewRange = acts.Extent(acts.ExtentEnvelope())
            volumeOptions = acts.svg.DetectorVolumeOptions()
            volumeOptions.surfaceOptions = surfaceOptions

            # X-y view
            xyRange = acts.Extent(acts.ExtentEnvelope())
            xyRange.setRange(acts.AxisDirection.AxisX, [-50, 50])
            xyView = acts.svg.drawDetector(
                gContext,
                actsGeometry,
                "odd",
                [[ivol, volumeOptions] for ivol in range(actsGeometry.numberVolumes())],
                [["xy", ["sensitives"], xyRange]])

            # ZR view
            zrRange = acts.Extent(acts.ExtentEnvelope())
            zrRange.setRange(acts.AxisDirection.AxisPhi, [-0.1, 0.1])
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

        # Make an list of surface geometry id tags
        surfaceTags = [ geometry_utils.geometry_id2str(
                                surface.geometryId(),
                                ["volume", "layer", "portal", "passive"],
                                3)
                        for surface in materialSurfaces ]

        # Check drawing the material surfaces
        surfaceStyle = acts.svg.Style()
        surfaceStyle.fillColor = args.surface_rgb
        surfaceStyle.fillOpacity = args.surface_opacity
        surfaceStyle.strokeWidth = 5
        surfaceStyle.highlightStrokeWidth = 10
        surfaceStyle.highlightStrokeColor = [0, 0, 255]

        surfaceOptions = acts.svg.SurfaceOptions()
        surfaceOptions.style = surfaceStyle

        protoMaterialSurfaces = [ acts.svg.convertSurface(gContext,
                                                          surface,
                                                          surfaceOptions)
                                  for surface in materialSurfaces ]

        materialSurfacesZr = [ acts.svg.viewSurface(pSurface, "material_surface_"+surfaceTags[ip], "zr")
                             for ip, pSurface in enumerate(protoMaterialSurfaces) ]

        zrFile = acts.svg.file()
        zrFile.addObjects(materialSurfacesZr)

        # Draw the eta lines
        if len(args.eta_main_lines) > 0:
            materialEtaLines = acts.svg.drawEtaLines("eta_lines",
                                            args.eta_z_max, args.eta_r_max,
                                            args.eta_main_lines,
                                            args.eta_main_stroke_width,
                                            args.eta_main_label_size, True,
                                            args.eta_sub_lines,
                                            args.eta_sub_stroke_width,
                                            args.eta_sub_stroke_dash,
                                            10, False)
            zrFile.addObject(materialEtaLines)

        # Connect info boxes with the information of the surface
        for ims, mSurface in enumerate(materialSurfaces):
            tText = surfaceTags[ims]
            sMaterial = mSurface.surfaceMaterial()
            if type(sMaterial) in [acts.ProtoSurfaceMaterial, acts.ProtoGridSurfaceMaterial]:
                bText =  sMaterial.toString()
                # split the text at new lines
                bTextMultiLine = bText.split("\n")
                tStyle = acts.svg.Style()
                tStyle.fillColor = [0, 0, 255]
                tStyle.fillOpacity = 1
                tStyle.fontColor = [255, 255, 255]
                tStyle.fontSize=args.material_info_title_size
                bStyle = acts.svg.Style()
                bStyle.fontSize=args.material_info_body_size
                mInfoBox = acts.svg.drawInfoBox(
                            args.material_info_pos[0],
                            args.material_info_pos[1],
                            tText, tStyle,
                            bTextMultiLine, bStyle,
                            materialSurfacesZr[ims],
                            ["mousedown", "mouseup"])
                zrFile.addObject(mInfoBox)

        # Clip if configured
        if len(args.rz_view_box) == 4 :
            zrFile.clip(args.rz_view_box)
        # Write it out
        zrFile.write(args.output+"_material_surfaces_zr.svg")




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