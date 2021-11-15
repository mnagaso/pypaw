#!/usr/bin/env pythoiin
# -*- coding: utf-8 -*-
"""Script for dd adjoint source calculation

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
    GNU Lesser General Public License, version 3 (LGPLv3)
    (http://www.gnu.org/licenses/lgpl-3.0.en.html)
"""

import argparse
from .utils import load_json, load_yaml

from pypaw.doubledifference import calc_adj_sources


def main():
    parser = argparse.ArgumentParser(
        description="Adjoint source calculation for double difference")
    parser.add_argument('-f', action='store', dest='path_file', required=True,
                        help="path file")
    parser.add_argument('-p', action='store', dest='param_file', required=True,
                        help="param file")
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help="verbose flag")
    args = parser.parse_args()

    params = load_yaml(args.param_file)
    paths = load_json(args.path_file)
    calc_adj_sources(paths, params)


if __name__ == "__main__":
    main()
