#!/usr/bin/env pythoiin
# -*- coding: utf-8 -*-
"""Script for station pairing

It takes paths and param file as arguments.

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
    GNU Lesser General Public License, version 3 (LGPLv3)
    (http://www.gnu.org/licenses/lgpl-3.0.en.html)
"""




import argparse
from pytomo3d.doubledifference import pairing
from pytomo3d.doubledifference.windows import component_based_windows_data

import pyasdf
from .utils import load_json, load_yaml, dump_json


def main():
    parser = argparse.ArgumentParser(
        description="Pairing script for double difference")
    parser.add_argument('-f', action='store', dest='path_file', required=True,
                        help="path file")
    parser.add_argument('-p', action='store', dest='param_file', required=True,
                        help="param file")
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help="verbose flag")
    args = parser.parse_args()

    params = load_yaml(args.param_file)
    paths = load_json(args.path_file)
    stations = load_json(paths["stations_file"])
    sta_windows = load_json(paths["windows_file"])
    windows = component_based_windows_data(sta_windows)

    obsd_ds = pyasdf.ASDFDataSet(paths["obsd_asdf"])
    obsd_tag = paths["obsd_tag"]
    waveforms = obsd_ds.waveforms.list()
    traces = {}

    for waveform in waveforms:
        try:
            st = obsd_ds.waveforms[waveform][obsd_tag]
            for trace in st:
                traces[trace.id] = trace
        except KeyError:
            pass  # waveform does not have the tag

    pairs = pairing.find_pairs(
        windows, traces,
        locations=stations,
        closeness_on=params["closeness"]["flag"],
        closeness_threshold=params["closeness"]["threshold"],
        similarity_on=params["similarity"]["flag"],
        similarity_threshold=params["similarity"]["threshold"],
        phase_on=params["phase"]["flag"],
        phases=params["phase"]["phases_to_match"])

    dump_json(pairs, paths["output"])

if __name__ == "__main__":
    main()
