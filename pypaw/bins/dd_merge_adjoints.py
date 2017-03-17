#!/usr/bin/env pythoiin
# -*- coding: utf-8 -*-
"""Adjoint merge script

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
   GPL
"""
from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals


import argparse
import pyasdf
from pytomo3d.doubledifference.adjoint import (add_adjoint_sources,
                                               asdf_adj_to_adjoint,
                                               multiply_adjoint_source)

from pytomo3d.doubledifference.windows import component_based_windows_data

import os
from .utils import load_json


def write_to_asdf(adj, loc, ds):
    params = {
        "adjoint_source_type": adj.adj_src_type,
        "component": adj.component.replace("BH", "MX"),
        "depth_in_m": loc["local_depth"],
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "elevation_in_m": loc["elevation"],
        "dt": adj.dt,
        "location": adj.location,
        "max_period": adj.max_period,
        "min_period": adj.min_period,
        "misfit": adj.misfit,
        "starttime": str(adj.starttime),
        "station_id": ".".join([adj.network, adj.station]),
        "units": "m"
    }
    ds.add_auxiliary_data(data=adj.adjoint_source,
                          data_type="AdjointSources",
                          path="_".join([adj.network, adj.station,
                                         adj.component.replace("BH", "MX")]),
                          parameters=params)


def find_normalization_factor(pairs, windows, single_weight, dd_weight):
    # TODO: Find sum of weights
    # if name is not seen sum the weight value

    # TODO: Find number of non-paired measurements.  we can find
    # unique entries of pairings and find the total measurement count
    # from a window file and find the difference.
    norm = {}

    for comp in pairs:
        dd_total_weight = 0
        unique_dd_measurements = set()
        for pair in pairs[comp]:
            dd_total_weight += pair["weight_i"]
            dd_total_weight += pair["weight_j"]
            unique_dd_measurements.add(pair["window_id_i"])
            unique_dd_measurements.add(pair["window_id_j"])
        dd_total_weight *= dd_weight
        n_dd_meas = len(unique_dd_measurements)
        n_single_meas = len(windows[comp])
        n_meas = n_dd_meas + n_single_meas

        # Each single window has weight of 1
        single_total_weight = n_single_meas*single_weight
        total_weight = dd_total_weight + single_total_weight
        norm[comp] = n_meas/total_weight
        # print(comp, dd_total_weight, len(unique_dd_measurements))
    return norm


def get_adj_src_list(adj_ds):
    # This allows for adjoint file to be empty. This covers for two
    # extreme cases: all measurements are paired and none of the
    # measurements are paired.
    if hasattr(adj_ds.auxiliary_data, "AdjointSources"):
        return adj_ds.auxiliary_data.AdjointSources.list()
    return []


def sum_adjoints(adj_a, adj_b, weight_b):
    adj_b = multiply_adjoint_source(weight_b, adj_b)
    if adj_a is None:
        return adj_b
    return add_adjoint_sources(adj_a, adj_b)


def merge_adjoints(paths):
    single_weight = paths["single_weight"]
    dd_weight = paths["dd_weight"]

    pairs = load_json(paths["pair_file"])
    windows = component_based_windows_data(
        load_json(paths["single_window_file"]))
    norm = find_normalization_factor(pairs, windows, single_weight, dd_weight)

    output_file = paths["output_file"]

    if os.path.isfile(output_file):
        print("Output file exists. Deleting...")
        os.remove(output_file)
    output = pyasdf.ASDFDataSet(output_file)

    single_ds = pyasdf.ASDFDataSet(paths["single_adj"])
    single_adjs = get_adj_src_list(single_ds)

    dd_ds = pyasdf.ASDFDataSet(paths["dd_adj"])
    dd_adjs = get_adj_src_list(dd_ds)

    srcs_all = set()
    srcs_all = srcs_all.union(set(single_adjs))
    srcs_all = srcs_all.union(set(get_adj_src_list(dd_ds)))

    for src in srcs_all:
        adj, loc = None, None
        comp = src[-1]
        if src in single_adjs:
            single_adj, loc = asdf_adj_to_adjoint(
                single_ds.auxiliary_data.AdjointSources[src])
            adj = sum_adjoints(adj, single_adj, norm[comp]*single_weight)
        if src in dd_adjs:
            dd_adj, loc = asdf_adj_to_adjoint(
                dd_ds.auxiliary_data.AdjointSources[src])
            adj = sum_adjoints(adj, dd_adj, norm[comp]*dd_weight)
        write_to_asdf(adj, loc, output)

    for event in dd_ds.events:
        output.add_quakeml(event)


def main():
    parser = argparse.ArgumentParser(
        description="Merge two adjoint files")
    parser.add_argument('-f', action='store', dest='path_file', required=True,
                        help="path file")
    args = parser.parse_args()

    paths = load_json(args.path_file)
    merge_adjoints(paths)

if __name__ == "__main__":
    main()
