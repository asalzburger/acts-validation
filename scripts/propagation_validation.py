import acts
import argparse
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

    p.add_argument(
        "-o",
        "--output",
        type=str,
        default="propagation",
        help="Output file(s) base name",
    )

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

    p.add_argument(
        "--mode",
        type=str,
        default="gen2",
        choices=["gen1", "gen2", "detray"],
        help="Convert to detray detector and run detray navigation and propagation",
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

    args = p.parse_args()

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    materialDecorator = None
    if args.map != "":
        print(">>> Loading a material decorator from file:", args.map)
        materialDecorator = acts.IMaterialDecorator.fromFile(args.map)

    # The propagator
    propagatorImpl = None
    stepper = acts.StraightLineStepper()

    # Timing measurement is run if neither output in on
    sterileRun = False
    if not args.output_summary and not args.output_steps:
        print(">> Timing measurement is enabled, no output is written")
        sterileRun = True

    # Build the detector for Gen1
    if args.mode == "gen1":
        # Build the detector for Gen1
        from acts.examples.odd import getOpenDataDetector
        detector, trackingGeometry, decorators = getOpenDataDetector()
        # Set up the navigator - Gen1
        navigator = acts.Navigator(trackingGeometry=trackingGeometry)
        propagator = acts.Propagator(stepper, navigator)
        propagatorImpl = acts.examples.ConcretePropagator(propagator)
    else:
        # Build the detector for Gen2 (also detray)
        detector, storage = geometry_gen2.build(args, gContext, logLevel, materialDecorator)
        if args.mode == "gen2":
            # Set up the navigator - Gen2
            navigatorConfig = acts.DetectorNavigator.Config()
            navigatorConfig.detector = detector
            navigator = acts.DetectorNavigator(navigatorConfig, logLevel)
            propagator = acts.Propagator(stepper, navigator)
            # And finally the propagtor implementation
            propagatorImpl = acts.examples.ConcretePropagator(propagator)

        elif args.mode == "detray":
            # Translate the Gen2 detector to detray and compare that
            detrayOptions = acts.detray.DetrayConverter.Options()
            detrayStore = acts.examples.traccc.convertDetectorHost(gContext, detector, detrayOptions)
            propagatorImpl = acts.examples.traccc.createPropagatorHost(detrayStore)

    # Evoke the sequence
    rnd = acts.examples.RandomNumbers(seed=args.seed)

    # Build the sequencer
    s = acts.examples.Sequencer(events=args.events, numThreads=args.threads)

    # Add the particle gun from ACTS
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

    # Run particle smearing
    trackParametersGenerator = acts.examples.ParticleSmearing(
        level=acts.logging.INFO,
        inputParticles="particles_input",
        outputTrackParameters="start_parameters",
        randomNumbers=rnd,
        sigmaD0=0.0,
        sigmaZ0=0.0,
        sigmaPhi=0.0,
        sigmaTheta=0.0,
        sigmaPtRel=0.0,
    )
    s.addAlgorithm(trackParametersGenerator)

    propagationAlgorithm = acts.examples.PropagationAlgorithm(
        propagatorImpl=propagatorImpl,
        level=acts.logging.INFO,
        sterileLogger=sterileRun,
        inputTrackParameters="start_parameters",
        outputSummaryCollection="propagation_summary",
    )
    s.addAlgorithm(propagationAlgorithm)

    # Write the summary
    if args.output_summary:
        s.addWriter(
            acts.examples.RootPropagationSummaryWriter(
                level=acts.logging.INFO,
                inputSummaryCollection="propagation_summary",
                filePath=args.output + "_propagation_summary.root",
            )
        )

    # Write the steps
    if args.output_steps:
        s.addWriter(
            acts.examples.RootPropagationStepsWriter(
                level=acts.logging.INFO,
                collection="propagation_summary",
                filePath=args.output + "_propagation_steps.root",
            )
        )

    # Run the sequence
    s.run()

if "__main__" == __name__:
    main()
