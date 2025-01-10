#!/usr/bin/env python3

from pathlib import Path
from typing import Optional

import acts
import argparse
import geometry_gen1
import geometry_gen2
import particle_generation
import acts.examples
from acts.examples.simulation import (
    addParticleGun,
    EtaConfig,
    ParticleConfig,
    MomentumConfig,
)


u = acts.UnitConstants

def runDigitization(
    trackingGeometry: acts.TrackingGeometry,
    args: argparse.Namespace,
    outputDir: Path,
    digiConfigFile: Path,
    particlesInput: Optional[Path] = None,
    outputRoot: bool = True,
    outputCsv: bool = True,
    s: Optional[acts.examples.Sequencer] = None,
    doMerge: Optional[bool] = None,
) -> acts.examples.Sequencer:
    from acts.examples.simulation import (
        addParticleGun,
        EtaConfig,
        PhiConfig,
        ParticleConfig,
        addFatras,
        addDigitization,
    )


    # Common (to all modes): Evoke the sequence
    rnd = acts.examples.RandomNumbers(seed=args.seed)

    # Commom: Build the sequencer
    s = acts.examples.Sequencer(events=args.events, numThreads=args.threads)

    # field value
    field = acts.ConstantBField(acts.Vector3(0, 0, 2 * u.T))

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

    outputDir = Path(outputDir)
    if args.sim_mode == "fatras":
        addFatras(
            s,
            trackingGeometry,
            field,
            rnd=rnd,
        )
    elif args.sim_mode == "geant4":
        raise NotImplementedError("Geant4 simulation mode is not implemented yet")

    addDigitization(
        s,
        trackingGeometry,
        field,
        digiConfigFile=digiConfigFile,
        outputDirCsv=None,
        outputDirRoot=outputDir if outputRoot else None,
        rnd=rnd,
        doMerge=doMerge,
    )

    return s


if "__main__" == __name__:

    # Start of argument parsing #########################################
    p = argparse.ArgumentParser()

    p.add_argument("-n", "--events", type=int, default=1000, help="Number of Events")

    p.add_argument("-j", "--threads", type=int, default=1, help="Number of Threads for parallel execution")

    # Add Gen2 related arguments
    geometry_gen2.add_arguments(p)

    # Add Particle generation related arguments
    particle_generation.add_arguments(p)

    # The geometry modes are
    # gen1: Gen1 detector with Gen1 navigator and propagator
    # gen2: Gen2 detector with Gen2 navigator and propagator
    p.add_argument(
        "--geo-mode",
        type=str,
        default="gen1",
        choices=["gen1"],
        help="Convert to detray detector and run detray navigation and propagation",
    )

    # The simulation modes are
    # fatras: run fatras simulation
    # geant4: run geant4 simulation
    p.add_argument(
        "--sim-mode",
        type=str,
        default="fatras",
        choices=["fatras", "geant4"],
        help="Simulation mode",
    )

    p.add_argument("--digi-config", type=str, default="", help="Digitization configuration file location.")

    p.add_argument(
        "-s", "--seed", type=int, default=221177, help="Random number seed"
    )

    args = p.parse_args()
    # End of argument parsing #########################################

    digiConfigFile = (
        Path(args.digi_config)
    )

    assert digiConfigFile.exists()

    materialDecorator = None
    logLevel = acts.logging.INFO
    gContext = acts.GeometryContext()

    if "gen1" in args.geo_mode:
        # Build the detector for Gen1
        actsGeometry, detectorStore = geometry_gen1.build(args, gContext, logLevel, materialDecorator)

        runDigitization(actsGeometry, args, outputDir=Path.cwd(), digiConfigFile=digiConfigFile).run()
