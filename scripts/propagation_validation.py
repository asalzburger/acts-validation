import acts
import argparse
import geometry_gen1
import geometry_gen2
import particle_generation
from acts.examples.simulation import (
    addParticleGun,
    EtaConfig,
    ParticleConfig,
    MomentumConfig,
)

u = acts.UnitConstants

def main():
    p = argparse.ArgumentParser()

    p.add_argument("-n", "--events", type=int, default=1000, help="Number of Events")

    p.add_argument("-j", "--threads", type=int, default=1, help="Number of Threads for parallel execution")

    p.add_argument("-i", "--input", type=str, default="", help="Input SQL file")

    p.add_argument("-o", "--output", type=str, default="", help="Output prefix")

    p.add_argument(
        "-m", "--map", type=str, default="", help="Input file for the material map"
    )

    p.add_argument(
        "-s", "--seed", type=int, default=221177, help="Random number seed"
    )

    # Add Gen2 related arguments
    geometry_gen2.add_arguments(p)

    # Add Particle generation related arguments
    particle_generation.add_arguments(p)

    # The geometry modes are
    # gen1: Gen1 detector with Gen1 navigator and propagator
    # gen2: Gen2 detector with Gen2 navigator and propagator
    # detray_gen2: Gen2 detector with detray navigator and propagator
    # geant4_gen1: Geant4 navigator and propagator with gen1 surface matching
    # geant4_gen2: Geant4 navigator and propagator with gen2 surface matching
    p.add_argument(
        "--geo-mode",
        type=str,
        default="gen2",
        choices=["gen1", "gen2", "detray_gen2", "geant4_gen1", "geant4_gen2"],
        help="Convert to detray detector and run detray navigation and propagation",
    )

    p.add_argument("--detray-surface-grids",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Convert detray surface grids",
    )

    p.add_argument(
        "--output-summary",
        action=argparse.BooleanOptionalAction,
        help="Write out the summary objects",
    )

    p.add_argument(
        "--output-steps",
        action=argparse.BooleanOptionalAction,
        help="Write out the step objects",
    )

    p.add_argument(
        "--output-material",
        action=argparse.BooleanOptionalAction,
        help="Write out the recorded",
    )

    p.add_argument(
        "--output-sim-hits",
        action=argparse.BooleanOptionalAction,
        help="Write out sim hits, only makes sense for Geant4",
    )

    args = p.parse_args()

    prfx = args.output + "_" if args.output != "" else ""

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    # Common (to all modes): Evoke the sequence
    rnd = acts.examples.RandomNumbers(seed=args.seed)

    # Commom: Build the sequencer
    s = acts.examples.Sequencer(events=args.events, numThreads=args.threads)

    # Common: Add the particle gun from ACTS
    addParticleGun(
        s,
        ParticleConfig(
            num=args.tracks, pdg=acts.PdgParticle.eMuon, randomizeCharge=True
        ),
        EtaConfig(args.eta_range[0], args.eta_range[1]),
        MomentumConfig(
            args.pt_range[0] * u.GeV, args.pt_range[1] * u.GeV, transverse=True
        ),
        rnd=rnd,
    )

    # Timing measurement is run if neither output in on
    sterileRun = False
    if not args.output_summary and not args.output_steps and not args.output_material:
        print(">> Timing measurement is enabled, no output is written")
        sterileRun = True

    # Material decoration for reconstruction geometry
    materialDecorator = None
    if args.map != "":
        print(">>> Loading a material decorator from file:", args.map)
        materialDecorator = acts.IMaterialDecorator.fromFile(args.map)

    # Build the acts geometry
    actsGeometry = None
    detectorStore = {}
    if "gen1" in args.geo_mode:
        # Build the detector for Gen1
        actsGeometry, detectorStore = geometry_gen1.build(args, gContext, logLevel, materialDecorator)
    elif "gen2" in args.geo_mode:
        # Build the detector for Gen2 (also detray)
        actsGeometry, detectorStore = geometry_gen2.build(args, gContext, logLevel, materialDecorator)


    # Check the mode
    print(">>> Test mode is :", args.geo_mode)
    # check if the mode does not contain geant4
    if not "geant4" in args.geo_mode:
        # The propagator
        propagatorImpl = None
        stepper = acts.StraightLineStepper()

        # Build the detector for Gen1
        if args.geo_mode == "gen1":
            # Set up the navigator - Gen1
            navigator = acts.Navigator(trackingGeometry=actsGeometry)
            propagator = acts.Propagator(stepper, navigator)
            propagatorImpl = acts.examples.ConcretePropagator(propagator)
        else:
            if args.geo_mode == "gen2":
                # Set up the navigator - Gen2
                navigatorConfig = acts.DetectorNavigator.Config()
                navigatorConfig.detector = actsGeometry
                navigator = acts.DetectorNavigator(navigatorConfig, logLevel)
                propagator = acts.Propagator(stepper, navigator)
                # And finally the propagtor implementation
                propagatorImpl = acts.examples.ConcretePropagator(propagator)

            elif args.geo_mode == "detray_gen2":
                # Translate the Gen2 detector to detray and compare that
                detrayOptions = acts.detray.DetrayConverter.Options()
                detrayOptions.convertSurfaceGrids = args.detray_surface_grids
                detrayStore = acts.examples.traccc.convertDetectorHost(gContext, actsGeometry, detrayOptions)
                propagatorImpl = acts.examples.traccc.createSlPropagatorHost(detrayStore, sterileRun)

        # Run particle smearing
        trkParamExtractor = acts.examples.ParticleTrackParamExtractor(
            level=acts.logging.INFO,
            inputParticles="particles_generated",
            outputTrackParameters="start_parameters",
        )
        s.addAlgorithm(trkParamExtractor)

        propagationAlgorithm = acts.examples.PropagationAlgorithm(
            propagatorImpl=propagatorImpl,
            level=acts.logging.INFO,
            sterileLogger=sterileRun,
            inputTrackParameters="start_parameters",
            outputSummaryCollection="propagation_summary",
            outputMaterialCollection="material_tracks"
        )
        s.addAlgorithm(propagationAlgorithm)
    else :
        from acts import examples
        from acts.examples import geant4 as acts_g4
        print(">>> Running Geant4 simulation, buckle up...")
        # The sensitive surface mapper
        smmConfig = acts_g4.SensitiveSurfaceMapper.Config()
        smmConfig.volumeMappings = []
        smmConfig.materialMappings = ['Silicon']
        sensitiveMapper = acts_g4.SensitiveSurfaceMapper.create(
            smmConfig, logLevel, actsGeometry
        )

        detectorConstruction = None
        detector = detectorStore["Detector"]

        from acts import geomodel as gm
        from acts.examples.dd4hep import DD4hepDetector

        if type(detector) is DD4hepDetector:
            from acts.examples.geant4.dd4hep import DDG4DetectorConstructionFactory
            detectorConstruction =  DDG4DetectorConstructionFactory(detector, [])
        elif type(detector) is gm.GeoModelTree :
            # The GeoModel detector
            from acts.examples.geant4.geomodel import GeoModelDetectorConstructionFactory
            detectorConstruction = GeoModelDetectorConstructionFactory(detector, [])

        #  Simulation
        physicsList = "MaterialPhysicsList"
        killVolume = detectorStore["Volume"]
        killAfterTime = float("inf")

        bfield = None

        geant4Simulation = acts_g4.Geant4Simulation(
            level=logLevel,
            detectorConstructionFactory=detectorConstruction,
            randomNumbers=rnd,
            inputParticles="particles_input",
            outputParticlesInitial="particales_initial",
            outputParticlesFinal="particles_final",
            outputSimHits="sim_hits",
            sensitiveSurfaceMapper=sensitiveMapper,
            magneticField=bfield,
            physicsList=physicsList,
            killVolume=killVolume,
            killAfterTime=killAfterTime,
            killSecondaries=True,
            recordHitsOfNeutrals=True,
            recordHitsOfSecondaries=False,
            keepParticlesWithoutHits=False,
        )
        s.addAlgorithm(geant4Simulation)

        # Convert the sim hits to propagation summary objects
        simHitsToSummary = acts.examples.SimHitToSummaryConversion(
            level=logLevel,
            inputSimHits="sim_hits",
            inputParticles="particales_initial",
            outputSummaryCollection="propagation_summary",
            surfaceByIdentifier=detectorStore["SurfaceByIdentifier"],
        )
        s.addAlgorithm(simHitsToSummary)

        # Optionally: Write the sim hits
        if args.output_sim_hits:
            simHits = "sim_hits"
            s.addWriter(
                acts.examples.RootSimHitWriter(
                    level=logLevel,
                    inputSimHits=simHits,
                    filePath=prfx+args.geo_mode+"_sim_hits.root"),
            )

    # Common: Write the summary
    if args.output_summary:
        s.addWriter(
            acts.examples.RootPropagationSummaryWriter(
                level=acts.logging.INFO,
                inputSummaryCollection="propagation_summary",
                filePath=prfx+args.geo_mode + "_propagation_summary.root",
            )
        )

    # Common: Write the steps
    if args.output_steps:
        s.addWriter(
            acts.examples.RootPropagationStepsWriter(
                level=acts.logging.INFO,
                collection="propagation_summary",
                filePath=prfx+args.geo_mode + "_propagation_steps.root",
            )
        )

    # Common: Write the material
    if args.output_material:
        s.addWriter(
            acts.examples.RootMaterialTrackWriter(
                level=acts.logging.INFO,
                inputMaterialTracks="material_tracks",
                filePath=args.geo_mode + "_material_tracks.root",
                storeSurface=False,
                storeVolume=False,
            )
        )

    # Run the sequence
    s.run()

if "__main__" == __name__:
    main()
