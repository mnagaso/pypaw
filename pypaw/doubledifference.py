# -*- coding: utf-8 -*-
"""Double Difference related methods

:copyright:
   Ridvan Orsvuran (orsvuran@geoazur.unice.fr), 2017
:license:
    GNU Lesser General Public License, version 3 (LGPLv3)
    (http://www.gnu.org/licenses/lgpl-3.0.en.html)
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
from collections import defaultdict
from functools import partial

from mpi4py import MPI

import pyasdf
from .utils import read_json_file
from pyadjoint.config import (ConfigDoubleDifferenceCrossCorrelation,
                              ConfigDoubleDifferenceMultiTaper)
from pytomo3d.adjoint.process_adjsrc import process_adjoint
from pytomo3d.adjoint.utils import reshape_adj
from pytomo3d.doubledifference.adjoint import (add_adjoint_sources,
                                               calculate_adjoint_pair,
                                               calculate_measure_pair)
from pytomo3d.doubledifference.pairing import get_stanames_of_pair
from pytomo3d.doubledifference.windows import component_based_windows_data
import json

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


def get_stations(pairs):
    """Get list of stations in pairs

    :param pairs: pairs
    :type pairs: dict
    :returns: stations list
    :rtype: list
    """
    stations = set()
    for pair in pairs:
        sta_i, sta_j = get_stanames_of_pair(pair)
        stations.add(sta_i)
        stations.add(sta_j)
    return list(stations)


def get_traces(stations, ds, tag, comp):
    """Get traces and inventories of stations

    :param stations: station list
    :type stations: list
    :param ds: ASDFDataSet
    :type ds: pyasdf.ASDFDataSet
    :param tag: waveform tag
    :type tag: str
    :param comp: component
    :type comp: str
    :returns: traces and inventories
    :rtype: tuple
    """
    traces = {}
    inventories = {}
    for station in stations:
        traces[station] = ds.waveforms[station][tag].select(
            component=comp)[0]
        inventories[station] = ds.waveforms[station].StationXML
    return traces, inventories


def calc_adj_pair(pair_id, pairs, adj_src_type, config, windows, obsd, synt):
    """Calculate adjoint pair.

    It is written to be used in parallel.

    :param pair_id: pair id
    :type pair_id: int
    :param pairs: list of pairs
    :type pairs: list
    :param adj_src_type: adjoint source type
    :type adj_src_type: str
    :param config: adjoint config
    :type config: pyadjoint.Config
    :param windows: windows data
    :type windows: dict
    :param obsd: named obsd traces
    :type obsd: dict
    :param synt: named synt traces
    :type synt: dict
    :returns: adjoint sources
    :rtype: dict
    """
    pair = pairs[pair_id]
    return calculate_adjoint_pair(pair, adj_src_type, config, windows,
                                  obsd, synt)


def calc_meas_pair(pair_id, pairs, adj_src_type, config, windows, obsd, synt):
    """Calculate adjoint pair.

    It is written to be used in parallel.

    :param pair_id: pair id
    :type pair_id: int
    :param pairs: list of pairs
    :type pairs: list
    :param adj_src_type: adjoint source type
    :type adj_src_type: str
    :param config: adjoint config
    :type config: pyadjoint.Config
    :param windows: windows data
    :type windows: dict
    :param obsd: named obsd traces
    :type obsd: dict
    :param synt: named synt traces
    :type synt: dict
    :returns: adjoint sources
    :rtype: dict
    """
    pair = pairs[pair_id]
    return calculate_measure_pair(pair, adj_src_type, config, windows,
                                  obsd, synt)


def split(a, n):
    """Job splitter

    :param a: job list
    :param n: number of chunks (processors)
    :returns: splitted jobs
    :rtype: list
    """
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def run_with_mpi(func, objects):
    """MPI helper

    :param func: function to call
    :type func: function
    :param objects: objects to pass to function
    :type objects: list
    :returns: results
    :rtype: dict
    """
    if rank == 0:  # server
        jobs = split(objects, size)
    else:
        jobs = []
    jobs = comm.scatter(jobs, root=0)

    results = {}
    for _i, job in enumerate(jobs, 1):
        results.update(func(job))
        if rank == 0:
            print("~{}% done.".format(
                int(_i/len(jobs)*100)),
                  end="\r")

    results = comm.gather(results, root=0)

    if rank == 0:
        all_results = {}
        for result in results:
            all_results.update(result)
        return all_results


def calc_adj_sources(path, params):
    """Main function for calculating adjoint sources

    :param path: path information
    :type path: dict
    :param params: parameters
    :type params: dict
    """
    src_type = params["adjoint_config"].pop("adj_src_type")
    if not src_type.endswith("_DD"):
        raise Exception("Adjoint source type is not double difference:",
                        src_type)

    if src_type == "multitaper_misfit_DD":
        config = ConfigDoubleDifferenceMultiTaper(**params["adjoint_config"])
    elif src_type == "cc_traveltime_misfit_DD":
        config = ConfigDoubleDifferenceCrossCorrelation(**params["adjoint_config"])  # NOQA
    else:
        raise NotImplementedError()

    pairs = read_json_file(path["pair_file"])
    windows_data = read_json_file(path["window_file"])
    windows = component_based_windows_data(windows_data)

    obsd_ds = pyasdf.ASDFDataSet(path["obsd_asdf"], mpi=False)
    obsd_tag = path["obsd_tag"]
    synt_ds = pyasdf.ASDFDataSet(path["synt_asdf"], mpi=False)
    synt_tag = path["synt_tag"]

    if rank == 0:
        if os.path.isfile(path["output_file"]):
            print("Output file exists. Deleting...")
            os.remove(path["output_file"])
        adj_ds = pyasdf.ASDFDataSet(path["output_file"], mpi=False)
        adj_ds.events = obsd_ds.events

    adj_srcs = {}
    inventories = {}
    for comp, comp_pairs in pairs.iteritems():
        if rank != 0:
            splitted_pairs = list(split(comp_pairs, size))
            comp_rank_pairs = splitted_pairs[rank]
        else:
            comp_rank_pairs = comp_pairs

        comp_stations = get_stations(comp_rank_pairs)
        obsd, comp_invs = get_traces(comp_stations, obsd_ds, obsd_tag, comp)
        synt, _ = get_traces(comp_stations, synt_ds, synt_tag, comp)
        # print(">", comp_invs)
        # raise Exception()

        comp_adj_srcs = {station: None for station in comp_stations}

        calc_pair = partial(calc_adj_pair,
                            pairs=comp_pairs,
                            adj_src_type=src_type,
                            config=config,
                            windows=windows[comp],
                            obsd=obsd,
                            synt=synt)

        results = run_with_mpi(calc_pair,
                               list(range(len(comp_pairs))))

        if results is not None:  # This means rank=0
            for result in results:
                i, j = result
                adj_i, adj_j = results[result]

                if comp_adj_srcs[i] is None:
                    comp_adj_srcs[i] = adj_i
                else:
                    comp_adj_srcs[i] = add_adjoint_sources(comp_adj_srcs[i],
                                                           adj_i)

                if comp_adj_srcs[j] is None:
                    comp_adj_srcs[j] = adj_j
                else:
                    comp_adj_srcs[j] = add_adjoint_sources(comp_adj_srcs[j],
                                                           adj_j)
            # Update adjoint sources
            for staname, adj_src in comp_adj_srcs.iteritems():
                if staname in adj_srcs:
                    adj_srcs[staname].append(adj_src)
                else:
                    adj_srcs[staname] = [adj_src]

                if staname not in inventories:
                    inventories[staname] = comp_invs[staname]

    if rank == 0:
        event = obsd_ds.events[0]
        origin = event.preferred_origin() or event.origins[0]
        focal = event.preferred_focal_mechanism()
        hdr = focal.moment_tensor.source_time_function.duration / 2.0
        # according to SPECFEM starttime convention
        time_offset = -1.5 * hdr
        starttime = origin.time + time_offset

        for station in adj_srcs:
            proc_adjs = process_adjoint(adj_srcs[station],
                                        inventory=inventories[station],
                                        interp_starttime=starttime,
                                        event=event,
                                        **params["process_config"])
            # print(station, inventories[station])
            asdf_srcs = reshape_adj(proc_adjs, inventories[station])
            for asdf_src in asdf_srcs:
                path = asdf_src["path"].split("/")[1]
                adj_ds.add_auxiliary_data(data=asdf_src["object"],
                                          data_type="AdjointSources",
                                          path=path,
                                          parameters=asdf_src["parameters"])


def calc_measures(path, params):
    """Main function for calculating adjoint sources

    :param path: path information
    :type path: dict
    :param params: parameters
    :type params: dict
    """
    src_type = params["adjoint_config"].pop("adj_src_type")
    if not src_type.endswith("_DD"):
        raise Exception("Adjoint source type is not double difference:",
                        src_type)

    if src_type == "multitaper_misfit_DD":
        config = ConfigDoubleDifferenceMultiTaper(**params["adjoint_config"])
    elif src_type == "cc_traveltime_misfit_DD":
        config = ConfigDoubleDifferenceCrossCorrelation(**params["adjoint_config"])  # NOQA
    else:
        raise NotImplementedError()

    pairs = read_json_file(path["pair_file"])
    windows_data = read_json_file(path["window_file"])
    windows = component_based_windows_data(windows_data)

    obsd_ds = pyasdf.ASDFDataSet(path["obsd_asdf"], mpi=False)
    obsd_tag = path["obsd_tag"]
    synt_ds = pyasdf.ASDFDataSet(path["synt_asdf"], mpi=False)
    synt_tag = path["synt_tag"]

    measures = {}
    for comp, comp_pairs in pairs.iteritems():
        splitted_pairs = list(split(comp_pairs, size))
        comp_rank_pairs = splitted_pairs[rank]

        comp_stations = get_stations(comp_rank_pairs)
        obsd, comp_invs = get_traces(comp_stations,
                                     obsd_ds, obsd_tag, comp)
        synt, _ = get_traces(comp_stations,
                             synt_ds, synt_tag, comp)

        comp_measures = defaultdict(lambda: None)

        calc_pair = partial(calc_meas_pair,
                            pairs=comp_pairs,
                            adj_src_type=src_type,
                            config=config,
                            windows=windows[comp],
                            obsd=obsd,
                            synt=synt)

        results = run_with_mpi(calc_pair,
                               list(range(len(comp_pairs))))

        if results is not None:  # This means rank=0
            for result in results:
                i, j = result
                meas_i, meas_j = results[result]

                meas_i["paired_with"] = j
                meas_j["paired_with"] = i

                if comp_measures[i] is None:
                    comp_measures[i] = []
                comp_measures[i].append(meas_i)

                if comp_measures[j] is None:
                    comp_measures[j] = []
                comp_measures[j].append(meas_j)

            measures[comp] = dict(comp_measures)

    if rank == 0:
        with open(path["output_file"], "w") as f:
            json.dump(measures, f, indent=2, sort_keys=True)
