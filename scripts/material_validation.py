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

    # The modes are
    # gen1: Gen1 detector with Gen1 navigator and propagator
    # gen2: Gen2 detector with Gen2 navigator and propagator
    # detray_gen2: Gen2 detector with detray navigator and propagator
    # geant4_gen1: Geant4 navigator and propagator with gen1 surface matching
    # geant4_gen2: Geant4 navigator and propagator with gen2 surface matching
    p.add_argument(
        "--mode",
        type=str,
        default="gen2",
        choices=["gen1", "gen2", "detray_gen2", "geant4_gen1", "geant4_gen2"],
        help="Convert to detray detector and run detray navigation and propagation",
    )

    args = p.parse_args()

    gContext = acts.GeometryContext()
    logLevel = acts.logging.INFO

    # Common (to all modes): Evoke the sequence
    rnd = acts.examples.RandomNumbers(seed=args.seed)

    # Commom: Build the sequencer
    s = acts.examples.Sequencer(events=args.events, numThreads=args.threads)

    # Material decoration for reconstruction geometry
    materialDecorator = None
    if args.map != "":
        print(">>> Loading a material decorator from file:", args.map)
        materialDecorator = acts.IMaterialDecorator.fromFile(args.map)

    # Build the acts geometry
    actsGeometry = None
    detectorStore = {}
    if "gen1" in args.mode:
        # Build the detector for Gen1
        actsGeometry, detectorStore = geometry_gen1.build(args, gContext, logLevel, materialDecorator)
    elif "gen2" in args.mode:
        # Build the detector for Gen2 (also detray)
        actsGeometry, detectorStore = geometry_gen2.build(args, gContext, logLevel, materialDecorator)

    # Assignment setup : Intersection assigner
    materialAssingerConfig = acts.IntersectionMaterialAssigner.Config()
    materialAssingerConfig.surfaces = actsGeometry.extractMaterialSurfaces()
    materialAssinger = acts.IntersectionMaterialAssigner(materialAssingerConfig, logLevel)

    # Validater setup
    materialValidaterConfig =acts.MaterialValidater.Config()
    materialValidaterConfig.materialAssigner = materialAssinger
    materialValidater = acts.MaterialValidater(materialValidaterConfig, logLevel)

    # Validation Algorithm
    materialValidationConfig = acts.examples.MaterialValidation.Config()
    materialValidationConfig.materialValidater = materialValidater
    materialValidationConfig.outputMaterialTracks = "recorded_material_tracks"
    materialValidationConfig.ntracks = args.tracks
    materialValidationConfig.randomNumberSvc = rnd
    materialValidation = acts.examples.MaterialValidation(materialValidationConfig, logLevel)
    s.addAlgorithm(materialValidation)

    # Add the mapped material tracks writer
    s.addWriter(
        acts.examples.RootMaterialTrackWriter(
            level=acts.logging.INFO,
            inputMaterialTracks=materialValidationConfig.outputMaterialTracks,
            filePath=args.mode + "_material_tracks.root",
            storeSurface=True,
            storeVolume=True,
        )
    )

    # Run the sequence
    s.run()

if "__main__" == __name__:
    main()
