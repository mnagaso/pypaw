#!/usr/bin/env pythoiin
# -*- coding: utf-8 -*-
"""Script for paired windows filtering

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
    GNU Lesser General Public License, version 3 (LGPLv3)
    (http://www.gnu.org/licenses/lgpl-3.0.en.html)
"""
from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals


import argparse
from pytomo3d.doubledifference.windows import (component_based_windows_data,
                                               filter_paired_windows,
                                               convert_to_sta_based_windows)

from .utils import load_json, dump_json


def main():
    parser = argparse.ArgumentParser(
        description="Filter windows file by selecting only paired ones")
    parser.add_argument("windows_file")
    parser.add_argument("pairs_file")

    args = parser.parse_args()
    sta_windows = load_json(args.windows_file)
    windows = component_based_windows_data(sta_windows)
    pairs = load_json(args.pairs_file)

    paired_filename = args.windows_file.replace(".json", ".paired.json")
    single_filename = args.windows_file.replace(".json", ".single.json")

    paired_windows, single_windows = filter_paired_windows(windows, pairs)

    dump_json(convert_to_sta_based_windows(paired_windows),
              paired_filename)
    dump_json(convert_to_sta_based_windows(single_windows),
              single_filename)

if __name__ == "__main__":
    main()
