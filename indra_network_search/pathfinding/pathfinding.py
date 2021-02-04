"""
Pathfinding algorithms local to this repo
"""
from itertools import islice, product
from networkx import DiGraph, MultiDiGraph
from typing import Generator, List, Union, Optional, Set, Iterator

from depmap_analysis.scripts.depmap_script_expl_funcs import \
    _get_signed_shared_targets, _get_signed_shared_regulators, _src_filter, \
    _node_ns_filter


__all__ = ['shared_interactors']


def shared_interactors(graph: Union[DiGraph, MultiDiGraph],
                       source: str, target: str,
                       allowed_ns: Optional[List[str]] = None,
                       stmt_types: Optional[List[str]] = None,
                       source_filter: Optional[List[str]] = None,
                       max_results: int = 50,
                       regulators: bool = False,
                       sign: Optional[int] = None) -> Iterator:
    """Get shared regulators or targets and filter them based on sign

    Closely resembles get_st and get_sr from
    depmap_analysis.scripts.depmap_script_expl_funcs

    Parameters
    ----------
    graph
    source
    target
    allowed_ns
    stmt_types
    source_filter
    max_results
    regulators
        If True, the do shared regulator search (upstream), otherwise do
        shared target search (downstream). Default False.
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
    src_args = (graph, regulators, source_filter)
    if source_filter:
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
