"""
Pathfinding algorithms local to this repo
"""
import logging
from itertools import islice, product
from typing import Generator, List, Union, Optional, Set, Iterator, Tuple, \
    Any, Dict

from networkx import DiGraph, MultiDiGraph

from depmap_analysis.network_functions.famplex_functions import \
    common_parent, get_identifiers_url, ns_id_to_name
from depmap_analysis.scripts.depmap_script_expl_funcs import \
    _get_signed_shared_targets, _get_signed_shared_regulators, _src_filter, \
    _node_ns_filter

logger = logging.getLogger(__name__)

__all__ = ['shared_interactors', 'shared_parents', 'get_subgraph_edges']


def shared_parents(source_ns: str, source_id: str, target_ns: str,
                   target_id: str, immediate_only: bool = False,
                   is_a_part_of: Optional[Set[str]] = None,
                   max_paths: int = 50) \
        -> Iterator[Tuple[str, Any, Any, str]]:
    """Get shared parents of (source ns, source id) and (target ns, target id)

    Parameters
    ----------
    source_ns : str
        Namespace of source
    source_id : str
        Identifier of source
    target_ns
        Namespace of target
    target_id
        Identifier of target
    immediate_only : bool
        Determines if all or just the immediate parents should be returned.
        Default: False, i.e. all parents.
    is_a_part_of : Set[str]
        If provided, the parents must be in this set of ids. The set is
        assumed to be valid ontology labels (see ontology.label()).
    max_paths : int
        Maximum number of results to return. Default: 50.

    Returns
    -------
    List[Tuple[str, str, str, str]]
    """
    sp_set = common_parent(id1=source_id, id2=target_id, ns1=source_ns,
                           ns2=target_ns, immediate_only=immediate_only,
                           is_a_part_of=is_a_part_of)
    return islice(sorted([
        (ns_id_to_name(n, i) or '',
         n, i, get_identifiers_url(n, i))
        for n, i in sp_set
        # sort on     name,  ns,  id
    ], key=lambda t: (t[0], t[1], t[2])), max_paths)


def shared_interactors(graph: DiGraph,
                       source: Union[str, Tuple[str, int]],
                       target: Union[str, Tuple[str, int]],
                       allowed_ns: Optional[List[str]] = None,
                       stmt_types: Optional[List[str]] = None,
                       source_filter: Optional[List[str]] = None,
                       max_results: int = 50,
                       regulators: bool = False,
                       sign: Optional[int] = None,
                       hash_blacklist: Optional[List[str]] = None,
                       node_blacklist: Optional[List[str]] = None,
                       belief_cutoff: float = 0.0,
                       curated_db_only: bool = False) \
        -> Iterator[Tuple[List[str], List[str]]]:
    """Get shared regulators or targets and filter them based on sign

    Closely resembles get_st and get_sr from
    depmap_analysis.scripts.depmap_script_expl_funcs

    Parameters
    ----------
    graph : DiGraph
        The graph to perform the search in
    source : str
        Node to look for common up- or downstream neighbors from with target
    target : str
        Node to look for common up- or downstream neighbors from with source
    allowed_ns : Optional[List[str]]
        If provided, filter common nodes to these namespaces
    stmt_types : Optional[List[str]]
        If provided, filter the statements in the supporting edges to these
        statement types
    source_filter : Optional[List[str]]
        If provided, filter the statements in the supporting edges to those
        with these sources
    max_results : int
        The maximum number of results to return
    regulators : bool
        If True, do shared regulator search (upstream), otherwise do shared
        target search (downstream). Default False.
    sign : Optional[int]
        If provided, match edges to sign:
            - positive: edges must have same sign
            - negative: edges must have opposite sign
    hash_blacklist : Optional[List[int]]
        A list of hashes to exclude from the edges
    node_blacklist : Optional[List[str]]
        A list of node names to exclude
    belief_cutoff : float
        Exclude statements that are below the cutoff. Default: 0.0 (no cutoff)
    curated_db_only : bool
        If True, exclude statements in edge support that only have readers
        in their sources. Default: False.

    Returns
    -------
    Generator
    """
    def _get_min_max_belief(node: str):
        s_edge = (node, source) if regulators else (source, node)
        t_edge = (node, target) if regulators else (target, node)
        s_max: float = max([sd['belief'] for sd in
                            graph.edges[s_edge]['statements']])
        t_max: float = max([sd['belief'] for sd in
                            graph.edges[t_edge]['statements']])
        return min(s_max, t_max)

    neigh = graph.pred if regulators else graph.succ
    s_neigh: Set[Union[str, Tuple[str, int]]] = set(neigh[source])
    t_neigh: Set[Union[str, Tuple[str, int]]] = set(neigh[target])

    # If signed, filter sign
    # Sign is handled different here than in the depmap explanations - if
    # the caller provides a positive sign, the common nodes should be the
    # ones that are upregulated by the source & target in the case of
    # shared targets and upregulates source & target in the case of shared
    # regul.
    if sign is not None:
        s_neigh, t_neigh = _sign_filter(source, s_neigh, target, t_neigh,
                                        sign, regulators)

    # Filter nodes
    if node_blacklist:
        s_neigh = {n for n in s_neigh if n not in node_blacklist}
        t_neigh = {n for n in t_neigh if n not in node_blacklist}

    # Filter ns
    if allowed_ns:
        s_neigh_names = s_neigh if sign is None else {s[0] for s in s_neigh}
        t_neigh_names = t_neigh if sign is None else {t[0] for t in t_neigh}

        s_neigh_names = _node_ns_filter(s_neigh_names, graph, allowed_ns)
        t_neigh_names = _node_ns_filter(t_neigh_names, graph, allowed_ns)

        s_neigh = s_neigh_names if sign is None else \
            {s for s in s_neigh if s[0] in s_neigh_names}
        t_neigh = t_neigh_names if sign is None else \
            {t for t in t_neigh if t[0] in t_neigh_names}

    # Filter statements type
    if stmt_types:
        st_args = (graph, regulators, stmt_types)
        s_neigh = _stmt_types_filter(source, s_neigh, *st_args)
        t_neigh = _stmt_types_filter(target, t_neigh, *st_args)

    # Filter curated db
    if curated_db_only:
        curated_args = (graph, regulators)
        s_neigh = _filter_curated(source, s_neigh, *curated_args)
        t_neigh = _filter_curated(target, t_neigh, *curated_args)

    # Filter hashes
    if hash_blacklist:
        hash_args = (graph, regulators, hash_blacklist)
        s_neigh = _hash_filter(source, s_neigh, *hash_args)
        t_neigh = _hash_filter(target, t_neigh, *hash_args)

    # Filter belief
    if belief_cutoff > 0:
        belief_args = (graph, regulators, belief_cutoff)
        s_neigh = _belief_filter(source, s_neigh, *belief_args)
        t_neigh = _belief_filter(target, t_neigh, *belief_args)

    # Filter source
    if source_filter:
        src_args = (graph, regulators, source_filter)
        s_neigh = _src_filter(source, s_neigh, *src_args)
        t_neigh = _src_filter(target, t_neigh, *src_args)

    intermediates = s_neigh & t_neigh

    # If sign, filter sign
    if sign is not None:
        # Have to match sign as well
        num_sign = 1 if sign == 0 else -1
        sign_args = (source, target, num_sign, graph, intermediates, False)
        if regulators:
            intermediates: Set[str] = _get_signed_shared_regulators(*sign_args)
        else:
            intermediates: Set[str] = _get_signed_shared_targets(*sign_args)

    interm_sorted = sorted(intermediates,
                           key=_get_min_max_belief,
                           reverse=True)

    # Return generator of edge pairs sorted by lowest highest belief of
    if regulators:
        path_gen: Generator = (([x, source], [x, target])
                               for x in interm_sorted)
    else:
        path_gen: Generator = (([source, x], [target, x])
                               for x in interm_sorted)
    return islice(path_gen, max_results)


def _sign_filter(source: Tuple[str, int], s_neigh: Set[Tuple[str, int]],
                 target: Tuple[str, int], t_neigh: Set[Tuple[str, int]],
                 sign: Optional[int], regulators: bool, ):
    # Check that nodes are signed
    try:
        assert isinstance(source, tuple)
        assert isinstance(target, tuple)
    except AssertionError as err:
        raise ValueError('Input nodes are not signed') from err
    # Check that signs are proper
    if sign not in {0, 1}:
        raise ValueError(f'Unknown sign {sign}')

    if regulators:
        # source and target sign match requested sign, neighbors are
        # always + signed
        try:
            assert source[1] == sign
            assert target[1] == sign
        except AssertionError as err:
            raise ValueError('Node sign does not match requested sign') \
                from err

        # Regulators can only have + sign
        # Find regulators that upregulate both source & target
        # Find regulators that downregulate both source & target

        s_neigh: Set[str] = {s for s in s_neigh if s[1] == 0}
        t_neigh: Set[str] = {t for t in t_neigh if t[1] == 0}
    else:
        # Match target sign with requested sign
        s_neigh: Set[str] = {s for s in s_neigh if s[1] == sign}
        t_neigh: Set[str] = {t for t in t_neigh if t[1] == sign}

    return s_neigh, t_neigh


def _stmt_types_filter(start_node: Union[str, Tuple[str, int]],
                       neighbor_nodes: Set[Union[str, Tuple[str, int]]],
                       graph: DiGraph, reverse: bool, stmt_types: List[str])\
        -> Set[Union[str, Tuple[str, int]]]:
    # Sort to ensure edge_iter is co-ordered
    if isinstance(start_node, tuple):
        node_list = sorted(neighbor_nodes, key=lambda t: t[0])
    else:
        node_list = sorted(neighbor_nodes)

    edge_iter = \
        product(node_list, [start_node]) if reverse else \
        product([start_node], node_list)

    # Check which edges have the allowed stmt types
    filtered_neighbors: Set[Union[str, Tuple[str, int]]] = set()
    for n, edge in zip(node_list, edge_iter):
        stmt_list = graph.edges[edge]['statements']
        if any(sd['stmt_type'].lower() in stmt_types for sd in stmt_list):
            filtered_neighbors.add(n)
    return filtered_neighbors


def _filter_curated(start_node: str, neighbor_nodes: Set[str],
                    graph: Union[DiGraph, MultiDiGraph], reverse: bool) -> \
        Set[str]:
    node_list = sorted(neighbor_nodes)

    edge_iter = \
        product(node_list, [start_node]) if reverse else \
        product([start_node], node_list)

    # Filter out edges without support from databases
    filtered_neighbors = set()
    for n, edge in zip(node_list, edge_iter):
        stmt_list = graph.edges[edge]['statements']
        if any(sd['curated'] for sd in stmt_list):
            filtered_neighbors.add(n)
    return filtered_neighbors


def _hash_filter(start_node: str, neighbor_nodes: Set[str],
                 graph: Union[DiGraph, MultiDiGraph], reverse: bool,
                 hashes: List[int]) -> Set[str]:
    node_list = sorted(neighbor_nodes)

    edge_iter = \
        product(node_list, [start_node]) if reverse else \
        product([start_node], node_list)

    # Filter out edges without support from databases
    filtered_neighbors = set()
    for n, edge in zip(node_list, edge_iter):
        stmt_list = graph.edges[edge]['statements']

        # Add node if *any* hash is *not* in blacklist
        for sd in stmt_list:
            if sd['stmt_hash'] not in hashes:
                filtered_neighbors.add(n)
                break
    return filtered_neighbors


def _belief_filter(start_node: str, neighbor_nodes: Set[str],
                   graph: Union[DiGraph, MultiDiGraph], reverse: bool,
                   belief_cutoff: float) -> Set[str]:
    node_list = sorted(neighbor_nodes)

    edge_iter = \
        product(node_list, [start_node]) if reverse else \
        product([start_node], node_list)

    # Filter out edges with belief below the cutoff
    filtered_neighbors = set()
    for n, edge in zip(node_list, edge_iter):
        stmt_list = graph.edges[edge]['statements']

        # Add node if *any* belief score is *above* cutoff
        for sd in stmt_list:
            if sd['belief'] > belief_cutoff:
                filtered_neighbors.add(n)
                break
    return filtered_neighbors


def get_subgraph_edges(graph: DiGraph,
                       nodes: List[Dict[str, str]])\
        -> Iterator[Tuple[str, str]]:
    """Get the subgraph connecting the provided nodes

    Parameters
    ----------
    graph : DiGraph
        Graph to look for in and out edges in
    nodes : List[Dict[str, str]]
        List of dicts of Node instances to look for neighbors in

    Returns
    -------
    Dict[str, Dict[str, List[Tuple[str, str]]]
        A dict keyed by each of the input node names that were present in
        the graph. For each node, two lists are provided for in-edges
        and out-edges respectively
    """
    node_names = [n['name'] for n in nodes]
    subgraph = graph.subgraph(nodes=node_names)
    return iter(subgraph.edges)
