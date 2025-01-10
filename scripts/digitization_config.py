#!/usr/bin/env python3
import argparse
import json
import logging

# Main function
if "__main__" == __name__:
    # Parse the command line arguments
    p = argparse.ArgumentParser(description="Digitization configuration")

    p.add_argument(
        "--digi-config-in", type=str, help="Digitization configuration file location."
    )

    p.add_argument(
        "--digi-config-out",
        type=str,
        help="(Patched) Digitization configuration file location.",
    )

    p.add_argument(
        "--volumes",
        type=int,
        nargs="+",
        help="List of volumes to be updated.",
    )

    p.add_argument(
        "--layers",
        type=int,
        nargs="+",
        help="List of layers to be updated.",
    )

    p.add_argument(
        "--extra-bits",
        type=int,
        nargs="+",
        help="List of extra bits to be updated.",
    )

    p.add_argument(
        "--bins-x",
        type=int,
        help="Number of bins in x to be overwritten.",
    )

    p.add_argument(
        "--range-x",
        type=int,
        nargs=2,
        help="Range in x to be overwritten.",
    )

    p.add_argument(
        "--bins-y",
        type=int,
        help="Number of bins in y to be overwritten.",
    )

    p.add_argument(
        "--range-y",
        type=int,
        nargs=2,
        help="Range in y to be overwritten.",
    )

    args = p.parse_args()

    # Logging configuration
    logging.basicConfig(encoding="utf-8", level=logging.INFO)

    # Read the digitization configuration file
    with open(args.digi_config_in, "r") as f:
        digi_config = json.load(f)
        digi_entries = digi_config["entries"]

        for digi_entry in digi_entries:
            if digi_entry["volume"] in args.volumes:
                if args.layers is None or ("layer" in digi_entry and digi_entry["layer"] in args.layers):
                    layer = digi_entry["layer"] if "layer" in digi_entry else "all"
                    if args.extra_bits is None or ("extra" in digi_entry and  digi_entry["extra"] in args.extra_bits):
                        extra = digi_entry["extra"] if "extra" in digi_entry else "all"
                        logging.info(f"Updating volume {digi_entry['volume']}, layer: {layer}, extra: {extra}")
                        # Get the parameterisation
                        digi_entry_value = digi_entry["value"]
                        if "geometric" in digi_entry_value:
                            digi_entry_value = digi_entry_value["geometric"]
                            digi_entry_segmentation = digi_entry_value["segmentation"]
                            digi_entry_binning = digi_entry_segmentation["binningdata"]
                            if args.bins_x is not None or args.range_x is not None or args.bins_y is not None or args.range_y is not None:
                                for single_binningvalue in digi_entry_binning:
                                    # Update x
                                    if single_binningvalue["value"] == "binX":
                                        if args.bins_x is not None:
                                            logging.info(f"-> Update number of bins in x from {single_binningvalue["bins"]} to {args.bins_x}")
                                            single_binningvalue["bins"] = args.bins_x
                                        if args.range_x is not None:
                                            logging.info(f"-> Update range in x from [{single_binningvalue["min"]}, {single_binningvalue["max"]} to {args.range_x}")
                                            single_binningvalue["min"] = args.range_x[0]
                                            single_binningvalue["max"] = args.range_x[1]
                                    # Update y
                                    if single_binningvalue["value"] == "binY":
                                        if args.bins_y is not None:
                                            logging.info(f"-> Update number of bins in y from {single_binningvalue["bins"]} to {args.bins_y}")
                                            single_binningvalue["bins"] = args.bins_y
                                        if args.range_y is not None:
                                            logging.info(f"-> Update range in y from [{single_binningvalue["min"]}, {single_binningvalue["max"]}] to {args.range_y}")
                                            single_binningvalue["min"] = args.range_y[0]
                                            single_binningvalue["max"] = args.range_y[1]
