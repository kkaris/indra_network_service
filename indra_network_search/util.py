"""Utility functions for the INDRA Causal Network Search API in api.py"""
import json
import inspect
import logging
import networkx as nx
from os import path
from typing import Callable, Dict, Any, Set
from datetime import datetime
from botocore.exceptions import ClientError

import networkx as nx
from fnvhash import fnv1a_32

from indra.util.aws import get_s3_client
from indra_db.client.readonly.query import FromMeshIds
from indra_db.util.dump_sif import load_db_content, make_dataframe, NS_LIST
from indra.statements import get_all_descendants, Activation, Inhibition, \
    IncreaseAmount, DecreaseAmount, AddModification, RemoveModification, \
    Complex

from depmap_analysis.network_functions import net_functions as nf
from depmap_analysis.util.io_functions import file_opener, dump_it_to_pickle, \
    DT_YmdHMS, RE_YmdHMS_, RE_YYYYMMDD, get_earliest_date, get_date_from_str, \
    strip_out_date
from depmap_analysis.util.aws import dump_json_to_s3, DUMPS_BUCKET, \
    NETS_PREFIX, load_pickle_from_s3, NET_BUCKET, read_json_from_s3
from depmap_analysis.scripts.dump_new_graphs import *

__all__ = ['load_indra_graph', 'list_chunk_gen', 'read_query_json_from_s3',
           'check_existence_and_date_s3', 'dump_result_json_to_s3',
           'dump_query_json_to_s3', 'get_query_hash',
           'dump_query_result_to_s3', 'NS_LIST', 'get_queryable_stmt_types',
           'load_pickled_net_from_s3', 'get_earliest_date', 'get_s3_client',
           'CACHE', 'INDRA_DG', 'INDRA_SEG', 'INDRA_SNG', 'INDRA_DG_CACHE',
           'INDRA_SEG_CACHE',  'INDRA_SNG_CACHE', 'TEST_DG_CACHE',
           'get_default_args', 'get_mandatory_args']

logger = logging.getLogger(__name__)

API_PATH = path.dirname(path.abspath(__file__))
CACHE = path.join(API_PATH, '_cache')
STATIC = path.join(API_PATH, 'static')
JSON_CACHE = path.join(API_PATH, '_json_res')

TEST_MDG_CACHE = path.join(CACHE, 'test_mdg_network.pkl')
INDRA_MDG_CACHE = path.join(CACHE, INDRA_MDG)
TEST_DG_CACHE = path.join(CACHE, 'test_dir_network.pkl')
INDRA_DG_CACHE = path.join(CACHE, INDRA_DG)
INDRA_SNG_CACHE = path.join(CACHE, INDRA_SNG)
INDRA_SEG_CACHE = path.join(CACHE, INDRA_SEG)
INDRA_PBSNG_CACHE = path.join(CACHE, INDRA_PBSNG)
INDRA_PBSEG_CACHE = path.join(CACHE, INDRA_PBSEG)


def get_query_resp_fstr(query_hash):
    qf = path.join(JSON_CACHE, 'query_%s.json' % query_hash)
    rf = path.join(JSON_CACHE, 'result_%s.json' % query_hash)
    return qf, rf


def list_chunk_gen(lst, size=1000):
    """Given list, generate chunks <= size"""
    n = max(1, size)
    return (lst[k:k+n] for k in range(0, len(lst), n))


def sorted_json_string(json_thing):
    """Produce a string that is unique to a json's contents."""
    if isinstance(json_thing, str):
        return json_thing
    elif isinstance(json_thing, (tuple, list)):
        return '[%s]' % (','.join(sorted(sorted_json_string(s)
                                         for s in json_thing)))
    elif isinstance(json_thing, dict):
        return '{%s}' % (','.join(sorted(k + sorted_json_string(v)
                                         for k, v in json_thing.items())))
    elif isinstance(json_thing, (int, float)):
        return str(json_thing)
    elif json_thing is None:
        return json.dumps(json_thing)
    else:
        raise TypeError('Invalid type: %s' % type(json_thing))


def get_query_hash(query_json, ignore_keys=None):
    """Create an FNV-1a 32-bit hash from the query json

    Parameters
    ----------
    query_json : dict
        A json compatible query dict
    ignore_keys : set|list
        A list or set of keys to ignore in the query_json. By default,
        no keys are ignored. Default: None.

    Returns
    -------
    int
        An FNV-1a 32-bit hash of the query json ignoring the keys in
        ignore_keys
    """
    if ignore_keys:
        if set(ignore_keys).difference(query_json.keys()):
            missing = set(ignore_keys).difference(query_json.keys())
            logger.warning(
                'Ignore key(s) "%s" are not in the provided query_json and '
                'will be skipped...' %
                str('", "'.join(missing)))
        query_json = {k: v for k, v in query_json.items()
                      if k not in ignore_keys}
    return fnv1a_32(sorted_json_string(query_json).encode('utf-8'))


def check_existence_and_date(indranet_date, fname, in_name=True):
    """With in_name True, look for a datestring in the file name, otherwise
    use the file creation date/last modification date.

    This function should return True if the file exists and is (seemingly)
    younger than the network that is currently in cache
    """
    if not path.isfile(fname):
        return False
    else:
        if in_name:
            try:
                # Try YYYYmmdd
                fdate = get_date_from_str(strip_out_date(fname, RE_YYYYMMDD),
                                          DT_YmdHMS)
            except ValueError:
                # Try YYYY-mm-dd-HH-MM-SS
                fdate = get_date_from_str(strip_out_date(fname, RE_YmdHMS_),
                                          DT_YmdHMS)
        else:
            fdate = datetime.fromtimestamp(get_earliest_date(fname))

        # If fdate is younger than indranet, we're fine
        return indranet_date < fdate


def _todays_date():
    return datetime.now().strftime('%Y%m%d')


# Copied from emmaa_service/api.py
def get_queryable_stmt_types():
    """Return Statement class names that can be used for querying."""
    def _get_sorted_descendants(cls):
        return sorted(_get_names(get_all_descendants(cls)))

    def _get_names(classes):
        return [s.__name__ for s in classes]

    stmt_types = \
        _get_names([
            Activation, Inhibition, IncreaseAmount, DecreaseAmount, Complex
        ]) + \
        _get_sorted_descendants(AddModification) + \
        _get_sorted_descendants(RemoveModification)
    return stmt_types


def load_indra_graph(dir_graph_path=None, multi_digraph_path=None,
                     sign_node_graph_path=None, sign_edge_graph_path=None,
                     update=False, belief_dict=None, strat_ev_dict=None,
                     include_entity_hierarchies=True, verbosity=0):
    """Return a nx.DiGraph and nx.MultiDiGraph representation an INDRA DB dump

    If update is True, make a fresh snapshot from the INDRA DB.
    WARNING: this typically requires a lot of RAM and might slow down your
    system significantly.
    """
    global INDRA_DG_CACHE, INDRA_MDG_CACHE, INDRA_SNG_CACHE, INDRA_SEG_CACHE
    indra_dir_graph = nx.DiGraph()
    indra_multi_digraph = nx.MultiDiGraph()
    indra_signed_edge_graph = nx.MultiDiGraph()
    indra_signed_node_graph = nx.DiGraph()

    if update:  # Todo: Download from db dumps instead
        df = make_dataframe(True, load_db_content(True, NS_LIST))
        options = {'df': df,
                   'belief_dict': belief_dict,
                   'strat_ev_dict': strat_ev_dict,
                   'include_entity_hierarchies': include_entity_hierarchies,
                   'verbosity': verbosity}
        indra_dir_graph = nf.sif_dump_df_to_digraph(**options)
        dump_it_to_pickle(dir_graph_path, indra_dir_graph)
        INDRA_DG_CACHE = path.join(CACHE, dir_graph_path)
        if multi_digraph_path:
            indra_multi_digraph = nf.sif_dump_df_to_digraph(
                graph_type='multidigraph', **options)
            dump_it_to_pickle(multi_digraph_path, indra_multi_digraph)
            INDRA_MDG_CACHE = path.join(CACHE, multi_digraph_path)
        if sign_node_graph_path or sign_edge_graph_path:
            indra_signed_edge_graph, indra_signed_node_graph = \
                nf.sif_dump_df_to_digraph(graph_type='signed', **options)
    else:
        logger.info('Loading indra network representations from pickles')
        if dir_graph_path:
            indra_dir_graph = file_opener(dir_graph_path)
        if multi_digraph_path:
            indra_multi_digraph = file_opener(multi_digraph_path)
        if sign_edge_graph_path:
            indra_signed_edge_graph = file_opener(sign_edge_graph_path)
        if sign_node_graph_path:
            indra_signed_node_graph = file_opener(sign_node_graph_path)
        logger.info('Finished loading indra networks.')
    return indra_dir_graph, indra_multi_digraph, indra_signed_edge_graph,\
        indra_signed_node_graph


def dump_query_json_to_s3(query_hash, json_obj, get_url=False):
    filename = '%s_query.json' % query_hash
    return dump_query_result_to_s3(filename, json_obj, get_url)


def dump_result_json_to_s3(query_hash, json_obj, get_url=False):
    filename = '%s_result.json' % query_hash
    return dump_query_result_to_s3(filename, json_obj, get_url)


def dump_query_result_to_s3(filename, json_obj, get_url=False):
    download_link = dump_json_to_s3(name=filename, json_obj=json_obj,
                                    public=True, get_url=get_url)
    if get_url:
        return download_link.split('?')[0]
    return None


def find_related_hashes(mesh_ids):
    q = FromMeshIds(mesh_ids)
    result = q.get_hashes()
    return result.json().get('results', [])


def check_existence_and_date_s3(query_hash, indranet_date=None):
    s3 = get_s3_client(unsigned=False)
    key_prefix = 'indra_network_search/%s' % query_hash
    query_json_key = key_prefix + '_query.json'
    result_json_key = key_prefix + '_result.json'
    exits_dict = {}
    if indranet_date:
        # Check 'LastModified' key in results
        # res_query = s3.head_object(Bucket=SIF_BUCKET, Key=query_json_key)
        # res_results = s3.head_object(Bucket=SIF_BUCKET, Key=result_json_key)
        pass
    else:
        try:
            query_json = s3.head_object(Bucket=DUMPS_BUCKET,
                                        Key=query_json_key)
        except ClientError:
            query_json = ''
        if query_json:
            exits_dict['query_json_key'] = query_json_key
        try:
            result_json = s3.head_object(Bucket=DUMPS_BUCKET,
                                         Key=result_json_key)
        except ClientError:
            result_json = ''
        if result_json:
            exits_dict['result_json_key'] = result_json_key
        return exits_dict

    return {}


def load_pickled_net_from_s3(name):
    s3_cli = get_s3_client(False)
    key = NETS_PREFIX + name
    return load_pickle_from_s3(s3_cli, key=key, bucket=NET_BUCKET)


def read_query_json_from_s3(s3_key):
    s3 = get_s3_client(unsigned=False)
    bucket = DUMPS_BUCKET
    return read_json_from_s3(s3=s3, key=s3_key, bucket=bucket)


def get_default_args(func: Callable) -> Dict[str, Any]:
    """Returns the default args of a function as a dictionary

    Returns a dictionary of {arg: default} of the arguments that have
    default values. Arguments without default values and **kwargs type
    arguments are excluded.

    Code copied from: https://stackoverflow.com/a/12627202/10478812

    Parameters
    ----------
    func : Callable
        Function to find default arguments for

    Returns
    -------
    Dict[str, Any]
        A dictionary with the default values keyed by argument name
    """
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def get_mandatory_args(func: Callable) -> Set[str]:
    """Returns the mandatory args for a function as a set

    Returns the set of arguments names of a functions that are mandatory,
    i.e. does not have a default value. **kwargs type arguments are ignored.

    Parameters
    ----------
    func : Callable
        Function to find mandatory arguments for

    Returns
    -------
    Set[str]
        The of mandatory arguments
    """
    signature = inspect.signature(func)
    return {
        k for k, v in signature.parameters.items()
        if v.default is inspect.Parameter.empty
    }
