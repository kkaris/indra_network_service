"""
Pathfinding algorithms local to this repo
"""
import logging
from itertools import islice, product
from typing import Generator, List, Union, Optional, Set, Iterator, Tuple, \
    Any

from networkx import DiGraph, MultiDiGraph

from depmap_analysis.network_functions.famplex_functions import \
    common_parent, get_identifiers_url, ns_id_to_name
from depmap_analysis.scripts.depmap_script_expl_funcs import \
    _get_signed_shared_targets, _get_signed_shared_regulators, _src_filter, \
    _node_ns_filter

logger = logging.getLogger(__name__)

__all__ = ['shared_interactors', 'shared_parents']


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
    ], key=lambda t: (t[0], t[1])), max_paths)


def shared_interactors(graph: DiGraph,
                       source: str, target: str,
                       allowed_ns: Optional[List[str]] = None,
                       stmt_types: Optional[List[str]] = None,
                       source_filter: Optional[List[str]] = None,
                       max_results: int = 50,
                       regulators: bool = False,
                       sign: Optional[int] = None) \
        -> Iterator[Tuple[List[str], List[str]]]:
    """Get shared regulators or targets and filter them based on sign

    Closely resembles get_st and get_sr from
    depmap_analysis.scripts.depmap_script_expl_funcs

    Parameters
    ----------
    graph : DiGraph
        The graph to perform the search in
    source : str
        Node to look for common up- or downstream interactors from with target
    target : str
        Node to look for common up- or downstream interactors from with source
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
    sign

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
    s_neigh: Set[str] = set(neigh[source])
    o_neigh: Set[str] = set(neigh[target])

    # Filter ns
    if allowed_ns:
        s_neigh = _node_ns_filter(s_neigh, graph, allowed_ns)
        o_neigh = _node_ns_filter(o_neigh, graph, allowed_ns)

    # Filter statements type
    if stmt_types:
        st_args = (graph, regulators, stmt_types)
        s_neigh = _stmt_types_filter(source, s_neigh, *st_args)
        o_neigh = _stmt_types_filter(target, o_neigh, *st_args)

    # Filter source
    if source_filter:
        src_args = (graph, regulators, source_filter)
        s_neigh = _src_filter(source, s_neigh, *src_args)
        o_neigh = _src_filter(target, o_neigh, *src_args)

    intermediates = s_neigh & o_neigh

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


def _stmt_types_filter(start_node: str, neighbor_nodes: Set[str],
                       graph: Union[DiGraph, MultiDiGraph], reverse: bool,
                       stmt_types: List[str]) -> Set[str]:
    node_list = sorted(neighbor_nodes)

    edge_iter = \
        product(node_list, [start_node]) if reverse else \
        product([start_node], node_list)

    # Check which edges have the allowed stmt types
    filtered_neighbors = set()
    for n, edge in zip(node_list, edge_iter):
        stmt_list = graph.edges[edge]['statements']
        if any(sd['stmt_type'].lower() in stmt_types for sd in stmt_list):
            filtered_neighbors.add(n)
    return filtered_neighbors
