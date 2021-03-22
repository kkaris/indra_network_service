"""Utility functions for the INDRA Causal Network Search API in api.py"""
import json
import inspect
import logging
from os import path
from typing import Callable, Dict, Any, Set, List, Tuple, Optional
from datetime import datetime

from botocore.exceptions import ClientError
import networkx as nx
from fnvhash import fnv1a_32

from indra.util.aws import get_s3_client, get_s3_file_tree
from indra_db.client.readonly.query import FromMeshIds
from indra_db.util.dump_sif import NS_LIST
from indra.statements import get_all_descendants, Activation, Inhibition, \
    IncreaseAmount, DecreaseAmount, AddModification, RemoveModification, \
    Complex
from depmap_analysis.util.io_functions import file_opener, DT_YmdHMS, \
    RE_YmdHMS_, RE_YYYYMMDD, get_earliest_date, get_date_from_str, \
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
           'get_default_args', 'get_mandatory_args', 'is_weighted',
           'is_context_weighted']

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


def get_latest_graphs() -> Dict[str, str]:
    """Return the s3 urls to the latest unsigned and signed graphs available

    Returns
    -------
    Dict[str, str]
    """
    s3 = get_s3_client(unsigned=False)
    tree = get_s3_file_tree(s3=s3, bucket=NET_BUCKET,
                            prefix=NETS_PREFIX,
                            with_dt=True)
    keys = [key for key in tree.gets('key') if key[0].endswith('.pkl')]

    # Sort newest first
    keys.sort(key=lambda t: t[1], reverse=True)

    # Find latest graph of each type
    latest_graphs = {}
    for graph_type in [INDRA_DG, INDRA_SNG, INDRA_SEG]:
        for key, _ in keys:
            if graph_type in key:
                latest_graphs[graph_type] = key
                break
    if len(latest_graphs) == 0:
        logger.warning(f'Found no graphs at s3://{NET_BUCKET}'
                       f'/{NETS_PREFIX}/*.pkl')
    return latest_graphs


def load_indra_graph(unsigned_graph: bool = True,
                     unsigned_multi_graph: bool = False,
                     sign_node_graph: bool = True,
                     sign_edge_graph: bool = False) \
        -> Tuple[Optional[nx.DiGraph], Optional[nx.MultiDiGraph],
                 Optional[nx.MultiDiGraph], Optional[nx.DiGraph]]:
    """Return a tuple of graphs to be used in the network search API

    Parameters
    ----------
    unsigned_graph : bool
        Load the latest unsigned graph. Default: True.
    unsigned_multi_graph : bool
        Load the latest unsigned multi graph. Default: False.
    sign_node_graph : bool
        Load the latest signed node graph. Default: True.
    sign_edge_graph : bool
        Load the latest signed edge graph. Default: False.

    Returns
    -------
    Tuple[nx.DiGraph, nx.MultiDiGraph, nx.MultiDiGraph, nx.DiGraph]
        Returns, as a tuple:
            - unsigned graph
            - unsigned multi graph
            - signed node graph
            - signed edge graphs
        If a graph was not chosen to be loaded or wasn't found, None will be
        returned in its place in the tuple.
    """
    # Initialize graphs
    indra_dir_graph = None
    indra_multi_di_graph = None
    indra_signed_edge_graph = None
    indra_signed_node_graph = None
    latest_graphs = get_latest_graphs()

    if unsigned_graph:
        if latest_graphs.get(INDRA_DG):
            indra_dir_graph = file_opener(latest_graphs[INDRA_DG])
        else:
            logger.warning(f'{INDRA_DG} was not found')

    if unsigned_multi_graph:
        if latest_graphs.get(INDRA_MDG):
            indra_multi_di_graph = file_opener(latest_graphs[INDRA_MDG])
        else:
            logger.warning(f'{INDRA_MDG} was not found')

    if sign_node_graph:
        if latest_graphs.get(INDRA_SNG):
            indra_signed_node_graph = file_opener(latest_graphs[INDRA_SNG])
        else:
            logger.warning(f'{INDRA_SNG} was not found')

    if sign_edge_graph:
        if latest_graphs.get(INDRA_SEG):
            indra_signed_edge_graph = file_opener(latest_graphs[INDRA_SEG])
        else:
            logger.warning(f'{INDRA_SEG} was not found')

    return indra_dir_graph, indra_multi_di_graph, indra_signed_edge_graph, \
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


def is_context_weighted(mesh_id_list: List[str],
                        strict_filtering: bool) -> bool:
    """Return True if context weighted

    Parameters
    ----------
    mesh_id_list : List[str]
        A list of mesh ids
    strict_filtering : bool
        whether to run strict context filtering or not

    Returns
    -------
    bool
        True for the combination of mesh ids being present and unstrict
        filtering, otherwise False
    """
    if mesh_id_list and not strict_filtering:
        return True
    return False


def is_weighted(weighted: bool, mesh_ids: List[str],
                strict_mesh_filtering: bool) -> bool:
    """Return True if the combination is either weighted or context weighted

    Parameters
    ----------
    weighted : bool
        If a query is weighted or not
    mesh_ids : List[str]
        A list of mesh ids
    strict_mesh_filtering : bool
        whether to run strict context filtering or not

    Returns
    -------
    bool
        True if the combination is either weighted or context weighted
    """
    if mesh_ids:
        ctx_w = is_context_weighted(mesh_id_list=mesh_ids,
                                    strict_filtering=strict_mesh_filtering)
        return weighted or ctx_w
    else:
        return weighted
