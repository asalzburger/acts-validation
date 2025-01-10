#!/usr/bin/env python3
from datetime import datetime
import uproot
import pandas as pd
import numpy as np
import logging
import argparse
import hist
from hist import Hist
import matplotlib
import matplotlib.pyplot as plt
import json
import os
import copy

from pathlib import Path


# OBJ: TLeafI	event_nr	event_nr
# OBJ: TLeafI	volume_id	volume_id
# OBJ: TLeafI	layer_id	layer_id
# OBJ: TLeafI	surface_id	surface_id
# OBJ: TLeafI	surface_id	extra_id
# OBJ: TLeafF	rec_loc0	rec_loc0
# OBJ: TLeafF	rec_loc1	rec_loc1
# OBJ: TLeafF	rec_time	rec_time
# OBJ: TLeafF	var_loc0	var_loc0
# OBJ: TLeafF	var_loc1	var_loc1
# OBJ: TLeafF	var_time	var_time
# OBJ: TLeafI	clus_size	clus_size
# OBJ: TLeafElement	channel_value	channel_value
# OBJ: TLeafElement	channel_loc0	channel_loc0
# OBJ: TLeafI	clus_size_loc0	clus_size_loc0
# OBJ: TLeafElement	channel_loc1	channel_loc1
# OBJ: TLeafI	clus_size_loc1	clus_size_loc1
# OBJ: TLeafF	true_loc0	true_loc0
# OBJ: TLeafF	true_loc1	true_loc1
# OBJ: TLeafF	true_phi	true_phi
# OBJ: TLeafF	true_theta	true_theta
# OBJ: TLeafF	true_qop	true_qop
# OBJ: TLeafF	true_time	true_time
# OBJ: TLeafF	true_x	true_x
# OBJ: TLeafF	true_y	true_y
# OBJ: TLeafF	true_z	true_z
# OBJ: TLeafF	true_incident_phi	true_incident_phi
# OBJ: TLeafF	true_incident_theta	true_incident_theta
# OBJ: TLeafF	residual_loc0	residual_loc0
# OBJ: TLeafF	residual_loc1	residual_loc1
# OBJ: TLeafF	residual_time	residual_time
# OBJ: TLeafF	pull_loc0	pull_loc0
# OBJ: TLeafF	pull_loc1	pull_loc1
# OBJ: TLeafF	pull_time	pull_time


# encode the variable and ids into a string
def encode(var, volume_id, layer_id, extra_id, cluster_size):
    # If the layer_id is -1, we are dealing with a volume
    bname = (
        f"{var}_vol{volume_id}"
        if layer_id == -1
        else f"{var}_vol{volume_id}_lay{layer_id}"
    )
    # If the extra_id is -1, no splitting into extra bits
    bname = f"{bname}_ext{extra_id}" if extra_id > -1 else bname
    return f"{bname}_csize{cluster_size}" if cluster_size > 0 else f"{bname}"


# recreate the variable and ids from the string
def decode(volkey):
    parts = volkey.split("_")
    vtype = parts[0]
    var = parts[1]
    volume_id = int(parts[2][3:])
    next_part = 3
    layer_id = -1
    if "lay" in volkey:
        layer_id = int(parts[next_part][3:])
        next_part = 4
    extra_id = -1
    if "ext" in volkey:
        extra_id = int(parts[next_part][3:])
        next_part += 1
    cluster_size = int(parts[next_part][5:]) if len(parts) > next_part else 0
    return vtype + "_" + var, volume_id, layer_id, extra_id, cluster_size


def book_histograms(args, batch):

    batch["volume_layer_extra_id"] = list(
        zip(batch.volume_id, batch.layer_id, batch.extra_id)
    )

    # the unique volume/layer ids
    unique_ids = np.unique(batch["volume_layer_extra_id"])
    process_unique_ids = np.unique(batch["volume_layer_extra_id"])
    num_unique_ids = len(unique_ids)
    # post processing with respecting the layer split
    for i, (volume_id, layer_id, extra_id) in enumerate(unique_ids):
        unique_ids[i] = (volume_id, layer_id, extra_id)
        # now set
        layer_id = layer_id if volume_id in args.volumes_with_layersplit else -1
        extra_id = extra_id if volume_id in args.volumes_with_extrabit else -1
        process_unique_ids[i] = (volume_id, layer_id, extra_id)
    # Make them unique again
    process_unique_ids = np.unique(process_unique_ids)
    unique_ids = np.unique(unique_ids)

    logging.info(f"Found {num_unique_ids} unique volume IDs: {unique_ids}")
    logging.info(
        f"Processing {len(process_unique_ids)} unique volume IDs: {process_unique_ids}"
    )

    histograms = {}
    histograms_overview = {}

    residuals = ["loc0", "loc1", "time"]

    for i, (volume_id, layer_id, extra_id) in enumerate(process_unique_ids):
        # In two steps avoids reindexing warning
        vbatch = batch[batch["volume_id"] == volume_id]
        if layer_id > 0:
            vbatch = vbatch[vbatch["layer_id"] == layer_id]
        if extra_id > 0:
            vbatch = vbatch[vbatch["extra_id"] == extra_id]
        # Get Min/Max  values for residuals
        hist_ranges = {
            res: vbatch["residual_" + res].agg(["min", "max"]) for res in residuals
        }

        local_ranges = {
            res: (vbatch["rec_" + res].min(), vbatch["rec_" + res].max())
            for res in residuals
        }

        channel_ranges = {
            "loc0" : (0, vbatch["channel_loc0"].max())
        }

        channel_ranges = {
            "loc1" : (0, vbatch["channel_loc1"].max())
        }

        # Get the max cluster sizes
        cluster_sizes = {
            "loc0": vbatch["clus_size_loc0"].max(),
            "loc1": (
                vbatch["clus_size_loc1"].max()
                if args.max_clustersize is None
                else (
                    args.max_clustersize
                    if args.max_clustersize < vbatch["clus_size_loc1"].max()
                    else vbatch["clus_size_loc1"].max()
                )
            ),
            "time": 0,
        }

        # Book the histograms: loc0_vs_loc1
        loc_2D_name = encode("loc0_vs_loc1", volume_id, layer_id, extra_id, 0)
        logging.info(f"Booking 2D histogram {loc_2D_name}")
        histograms_overview[loc_2D_name] = [
            Hist(
                hist.axis.Regular(
                    bins=args.bins,
                    start=local_ranges["loc0"][0],
                    stop=local_ranges["loc0"][1],
                    name="loc0",
                ),
                hist.axis.Regular(
                    bins=args.bins,
                    start=local_ranges["loc1"][0],
                    stop=local_ranges["loc1"][1],
                    name="loc1",
                ),
            ),
            0.0,
        ]

        # Book the histograms: channel_loc0 and channel_loc1
        #for res in ["loc0", "loc1"]:
        #    hist_channel_name = encode(
        #        "channel_" + res, volume_id, layer_id, extra_id, 0
        #    )
        #    logging.debug(f"Booking histogram {hist_channel_name}")
        #    histograms[hist_channel_name] = [
        #        Hist(
        #            hist.axis.Regular(
        #                bins=args.bins,
        #                start=channel_ranges[res][0],
        #                stop=channel_ranges[res][1],
        #                name=res,
        #            )
        #        ),
        #        0.0,
        #    ]

        # Create the histograms
        for res in residuals:
            hrange = hist_ranges[res]
            # Check if the histogram ranges are not NaN
            if not np.isnan(hrange["min"]) and not np.isnan(hrange["max"]):
                # Now do the loop over the cluster sizes
                for c_size in range(0, cluster_sizes[res] + 1):

                    hist_residual_name = encode(
                        "residual_" + res, volume_id, layer_id, extra_id, c_size
                    )
                    logging.debug(f"Booking histogram {hist_residual_name}")

                    # Book the histogram
                    histograms[hist_residual_name] = [
                        Hist(
                            hist.axis.Regular(
                                bins=args.bins,
                                start=hrange["min"],
                                stop=hrange["max"],
                                name=res,
                            )
                        ),
                        0.0,
                    ]

                    # Book the pull histograms if configured
                    if args.pulls:
                        hist_pull_name = encode(
                            "pull_" + res, volume_id, layer_id, extra_id, c_size
                        )
                        logging.debug(f"Booking histogram {hist_pull_name}")

                        # Book the histogram
                        histograms[hist_pull_name] = [
                            Hist(
                                hist.axis.Regular(
                                    bins=args.bins,
                                    start=-5,
                                    stop=5,
                                    name="pull (" + res + ")",
                                )
                            ),
                            0.0,
                        ]
        # Clear the histogram ranges
        hist_ranges.clear()

    return histograms, histograms_overview, unique_ids, process_unique_ids


def run_parametrisation(args, measurements):

    logging.info("*** Measurement error parameterisation ***")

    # Open the json to be updated
    digi_cfg = None
    if (
        args.digi_config_in is not None
        and os.path.isfile(args.digi_config_in)
        and os.access(args.digi_config_in, os.R_OK)
    ):
        jfile = open(args.digi_config_in, "r")
        digi_cfg = json.load(jfile)

    # Define the branches to be plotted
    branches = ["volume_id", "layer_id", "extra_id", "clus_size_loc0", "clus_size_loc1"]
    # Overall 2D histograms
    branches += ["rec_loc0", "rec_loc1", "channel_loc0", "channel_loc1", "rec_time"]
    if args.residuals:
        branches += ["residual_loc0", "residual_loc1", "residual_time"]
    if args.pulls:
        branches += ["pull_loc0", "pull_loc1", "pull_time"]

    histograms = None
    unique_ids = None
    process_unique_ids = None
    n_batches = 0

    # histogram filling per batch
    for ib, batch in enumerate(
        measurements.iterate(
            branches,
            step_size=args.batch_size,
            library="pd",
        )
    ):
        n_batches += 1
        # In batch 0 we create the reference histograms
        if ib == 0:
            histograms, histograms_overview, unique_ids, process_unique_ids = book_histograms(
                args, batch
            )

        # Fill the 2D histograms
        for (volume_id, layer_id, extra_id) in process_unique_ids:
            loc_2D_name = encode("loc0_vs_loc1", volume_id, layer_id, extra_id, 0)
            hist_2D = histograms_overview[loc_2D_name]
            vbatch = batch[batch["volume_id"] == volume_id]
            if layer_id > 0:
                vbatch = vbatch[vbatch["layer_id"] == layer_id]
            if extra_id > 0:
                vbatch = vbatch[vbatch["extra_id"] == extra_id]
            hist_2D[0].fill(vbatch["rec_loc0"], vbatch["rec_loc1"])

        # Fill the histograms per batch
        for volkey, hist_rms in histograms.items():
            hist, rms = hist_rms
            vartype, volume_id, layer_id, extra_id, cluster_size = decode(volkey)
            logging.debug(f"Filling histogram {volkey}")
            # In two steps avoids reindexing warning
            vbatch = batch[batch["volume_id"] == volume_id]
            if layer_id > 0:
                vbatch = vbatch[vbatch["layer_id"] == layer_id]
            if extra_id > 0:
                vbatch = vbatch[vbatch["extra_id"] == extra_id]
            if cluster_size > 0:
                varname = "loc0" if "loc0" in vartype else "loc1"
                vbatch = vbatch[vbatch["clus_size_" + varname] == cluster_size]
            vlpars = vbatch[vartype]
            vlrms = np.sqrt(np.mean(np.square(vlpars)))
            if not np.isnan(vlrms):
                hist.fill(vlpars)
                hist_rms[1] = rms + vlrms

    # Draw the histograms and save them, fill also the rms dictionary
    rms_dict = {}
    for volkey, hist_rms in histograms.items():
        # Get histogram and rms
        hist, rms = hist_rms
        rms /= n_batches
        vartype, volume_id, layer_id, extra_id, cluster_size = decode(volkey)

        # Variable type
        varname = vartype.split("_")[1]

        # Create the volume key
        if volume_id not in rms_dict:
            rms_dict[volume_id] = {}
        if layer_id not in rms_dict[volume_id]:
            rms_dict[volume_id][layer_id] = {}
        if extra_id not in rms_dict[volume_id][layer_id]:
            rms_dict[volume_id][layer_id][extra_id] = {}
        if varname not in rms_dict[volume_id][layer_id][extra_id]:
            rms_dict[volume_id][layer_id][extra_id][varname] = {}
        rms_dict[volume_id][layer_id][extra_id][varname][cluster_size] = rms

        # Coninue if there are no entries
        if hist.sum() < args.min_entries:
            logging.info(
                f"Skipping histogram {volkey} with less than {args.min_entries} entries"
            )
            continue
        logging.debug(f"Drawing histogram {volkey}")

        # Plotting and saving
        plt.figure()
        hist.plot()
        # Prepare the hist ttile
        htitle = f"volume {volume_id}"
        if layer_id > 0:
            htitle += f", layer {layer_id}"
        else:
            htitle += f", all layers"
        if extra_id > 0:
            htitle += f", extra id {extra_id}"
        if cluster_size > 0:
            htitle += f", cluster size {cluster_size}"
        plt.title(f"{htitle}, rms : {rms}")
        plt.xlabel(vartype)
        plt.ylabel("Entries")
        plt.savefig(f"png/hist_{volkey}.png")

    # Update the digi_cfg to include the rms values, this should
    if digi_cfg is not None:
        logging.info("Updating the digitization configuration JSON File")
        digi_entries = digi_cfg["entries"]
        # make a dictionary of the entries
        # digi_dict = {}
        for volume_id in rms_dict:
            logging.info(f"Processing volume {volume_id}")
            # If the volume had extra bit information, we need to enforce layer splitting
            # in the output file, as the extra bit triggers writing of layers
            #
            # In this case you need the layers
            layers = []
            if (
                volume_id in args.volumes_with_extrabit
                or volume_id in args.volumes_with_layersplit
            ):
                logging.info(
                    f"Volume {volume_id} has extra bits or layer split, enforcing layer split"
                )
                for v_l_s_id in unique_ids:
                    if v_l_s_id[0] == volume_id:
                        layers.append(v_l_s_id[1])
            if len(layers) > 0:
                layers = np.unique(layers)
                logging.info(f"-> layers found for this volume: {layers}")

            for layer_id in rms_dict[volume_id]:
                logging.info(f"Processing layer: {layer_id if layer_id > 0 else 'all'}")
                for extra_id in rms_dict[volume_id][layer_id]:
                    # Process and change the entry
                    config_entry = None
                    # Start with a volume entry
                    for entry in digi_entries:
                        current_volume_id = entry["volume"]
                        if current_volume_id == volume_id:
                            config_entry = entry
                            break
                    # If we have a layer entry, update this one
                    if layer_id > 0 and "layer" in entry:
                        for entry in digi_entries:
                            current_volume_id = entry["volume"]
                            current_layer_id = entry["layer"]
                            if (
                                current_volume_id == volume_id
                                and current_layer_id == layer_id
                            ):
                                config_entry = entry
                                break
                        # Make sure the layer_id is set even if the entry didn't have one
                        config_entry["layer"] = layer_id
                    if extra_id > 0 and "layer" in entry and "extra" in entry:
                        for entry in digi_entries:
                            current_volume_id = entry["volume"]
                            current_layer_id = entry["layer"]
                            current_extra_id = entry["extra"]
                            if (
                                current_volume_id == volume_id
                                and current_extra_id == extra_id
                            ):
                                config_entry = entry
                                break
                        # Make sure the extra_id is set even if the entry didn't have one
                        config_entry["extra"] = extra_id
                    # Update the rms values
                    if config_entry is not None:
                        variances = []
                        for iv, varname in enumerate(
                            ["loc0", "loc1", "phi", "theta", "qOverP", "time"]
                        ):
                            if varname in rms_dict[volume_id][layer_id][extra_id]:
                                rms_dict_values = rms_dict[volume_id][layer_id][
                                    extra_id
                                ][varname]
                                # Skip the first
                                rms_local_values = {"index": iv}
                                rms_local_data = []
                                for key in sorted(rms_dict_values.keys()):
                                    if key > 0:
                                        rms_local_data.append(
                                            np.float64(rms_dict_values[key] ** 2)
                                        )
                                # Now add the values
                                rms_local_values["rms"] = rms_local_data
                                variances.append(rms_local_values)
                        # If there is no extra bit set or if layer_id is sensefule, overwrite the variances
                        if len(layers) == 0 or layer_id > 0:
                            config_entry["value"]["geometric"]["variances"] = variances
                        elif len(layers) > 0:
                            logging.info(f"Splitting into layers {layers}")
                            # first make a deep copy of the entry
                            for lid in layers:
                                new_entry = copy.deepcopy(config_entry)
                                new_entry["layer"] = int(lid)
                                if extra_id > 0:
                                    new_entry["extra"] = extra_id
                                new_entry["value"]["geometric"]["variances"] = variances
                                digi_entries.append(new_entry)

        # Control histograms
        for key, (hist, value) in histograms_overview.items():
            plt.figure()
            hist.plot()
            plt.savefig(f"png/hist2d_{key}.png")

        # Update the json
        if args.digi_config_out is not None:
            with open(args.digi_config_out, "w") as outfile:
                json.dump(digi_cfg, outfile, indent=4)


# Main function
if "__main__" == __name__:
    # Parse the command line arguments
    p = argparse.ArgumentParser(description="Hit parameterisation")
    p.add_argument(
        "--root",
        default="measurements.root",
        type=str,
        help="Root input file from the root measurement writer in ACTS.",
    )
    p.add_argument(
        "--tree", default="measurements", type=str, help="Tree name in the root file."
    )
    p.add_argument(
        "--batch-size", default=100000, type=int, help="Batch size for the iteration."
    )
    p.add_argument(
        "--digi-config-in", type=str, help="Digitization configuration file location."
    )
    p.add_argument(
        "--digi-config-out",
        type=str,
        help="(Patched) Digitization configuration file location.",
    )

    p.add_argument(
        "--volumes-with-layersplit",
        default=[],
        nargs="+",
        type=int,
        help="Indicate which volumes should be split in layers",
    )

    p.add_argument(
        "--volumes-with-extrabit",
        default=[],
        nargs="+",
        type=int,
        help="Indicate which volumes should be split with extra bits",
    )

    p.add_argument(
        "--min-entries",
        default=50,
        type=int,
        help="Minimum number of entries for a histogram to be drawn.",
    )

    p.add_argument(
        "--max-clustersize",
        type=int,
        help="Maximum cluster size.",
    )

    p.add_argument(
        "--bins",
        default=100,
        type=int,
        help="Number of bins for the histograms.",
    )

    p.add_argument(
        "--residuals",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Plot the residuals",
    )

    p.add_argument(
        "--pulls",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Plot the pulls",
    )

    args = p.parse_args()

    # Logging configuration
    logging.basicConfig(encoding="utf-8", level=logging.INFO)

    # Open the root file
    measurements = uproot.open(args.root + ":" + args.tree)

    run_parametrisation(args, measurements)
