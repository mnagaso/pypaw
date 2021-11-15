#!/usr/bin/env pythoiin
# -*- coding: utf-8 -*-
"""Script for filtering out rejected pairs

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
    GNU Lesser General Public License, version 3 (LGPLv3)
    (http://www.gnu.org/licenses/lgpl-3.0.en.html)
"""

import argparse

from .utils import load_json, dump_json


def filter_pairs(pairs, rejects):
    filtered_pairs = {}
    for comp in pairs:
        filtered_pairs[comp] = []
        reject_indices = []
        for reject in rejects[comp]:
            for i, pair in enumerate(pairs[comp]):
                if pair["window_id_i"] == reject[0] and \
                   pair["window_id_j"] == reject[1]:
                    reject_indices.append(i)
                    break
        for i, pair in enumerate(pairs[comp]):
            if i not in reject_indices:
                filtered_pairs[comp].append(pair)
    return filtered_pairs


def main():
    parser = argparse.ArgumentParser(
        description="Filter out rejected pairs")
    parser.add_argument("pairs_file")
    parser.add_argument("rejection_file")

    args = parser.parse_args()
    pairs = load_json(args.pairs_file)
    rejections = load_json(args.rejection_file)

    filtered_pairs_filename = args.pairs_file.replace(".json", ".filter.json")

    filtered_pairs = filter_pairs(pairs, rejections)

    dump_json(filtered_pairs,
              filtered_pairs_filename)


if __name__ == "__main__":
    main()
