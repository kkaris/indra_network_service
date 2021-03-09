"""
Todo
    Add tests for:
    - Test arg types match if possible, i.e. is the model's attribute of the
      same type as the arg of the algorithm function
FixMe
    Add mock db call for
    indra_db.client.readonly.mesh_ref_counts::get_mesh_ref_counts
    using
"""
from inspect import signature
import networkx as nx
from typing import Set, Callable
from indra_network_search.util import get_mandatory_args
from indra_network_search.data_models import NetworkSearchQuery
from indra_network_search.query import SharedTargetsQuery,\
    SharedRegulatorsQuery, ShortestSimplePathsQuery, BreadthFirstSearchQuery,\
    DijkstraQuery, OntologyQuery, MissingParametersError, \
    InvalidParametersError, alg_func_mapping


def _match_args(run_options: Set[str], alg_fun: Callable) -> bool:
    # graph or g or G argument is not provided by query from caller and
    # should therefore be excluded from the count. Also ignore the possible
    # kwargs parameter

    # Do the run options contain all mandatory args?
    mand_args = get_mandatory_args(alg_fun).difference({'kwargs'})
    if len(run_options.intersection(mand_args)) < len(mand_args) - 1:
        raise MissingParametersError(
            f'Missing at least one of mandatory parameters (excl. graph/g/G '
            f'args, kwargs). Mandatory parameters: "{", ".join(mand_args)}". '
            f'Provided parameters: "{", ".join(run_options)}".')

    # Are all the run options part of the function args?
    all_args = set(signature(alg_fun).parameters.keys())
    invalid = run_options.difference(all_args)
    if len(invalid):
        raise InvalidParametersError(
            f'Invalid args provided for algorithm {alg_fun.__name__}: '
            f'"{", ".join(invalid)}"'
        )

    return True


def test_shortest_simple_paths_query():
    graph = nx.DiGraph()
    graph.add_nodes_from([('A', {'ns': 'HGNC', 'id': '0'}),
                          ('B', {'ns': 'HGNC', 'id': '1'})])
    graph.add_edge('A', 'B')
    graph.graph['edge_by_hash'] = {'123456': ('A', 'B')}
    # Test unweighted + auxiliary queries
    query = NetworkSearchQuery(source='A', target='B')
    for QueryClass in [ShortestSimplePathsQuery, SharedRegulatorsQuery,
                       SharedTargetsQuery, OntologyQuery]:
        q_unw = QueryClass(query)
        if QueryClass.__name__ == 'OntologyQuery':
            options = q_unw.run_options(graph=graph)
        else:
            options = q_unw.run_options()
        _match_args(set(options.keys()), alg_func_mapping[q_unw.alg_name])

    # Test belief weighted
    query = NetworkSearchQuery(source='A', target='B', weighted=True)
    sspq_w = ShortestSimplePathsQuery(query)
    options = sspq_w.run_options()
    _match_args(set(options.keys()), alg_func_mapping[sspq_w.alg_name])

    # Test context weighted
    query = NetworkSearchQuery(source='A', target='B', mesh_ids=['D000544'],
                               strict_mesh_id_filtering=False)
    sspq_cw = ShortestSimplePathsQuery(query)
    options = sspq_cw.run_options()
    _match_args(set(options.keys()), alg_func_mapping[sspq_cw.alg_name])

    # Test strict search
    query = NetworkSearchQuery(source='A', target='B', mesh_ids=['D000544'],
                               strict_mesh_id_filtering=True)
    sspq_cs = ShortestSimplePathsQuery(query)
    options = sspq_cs.run_options()
    _match_args(set(options.keys()), alg_func_mapping[sspq_cs.alg_name])


def test_breadth_first_search_query():
    # Test regular BFS
    query = NetworkSearchQuery(source='A')
    bfsq = BreadthFirstSearchQuery(query)
    options = set(bfsq.run_options().keys())
    _match_args(run_options=options, alg_fun=alg_func_mapping[bfsq.alg_name])

    # Test strict context BFS
    graph = nx.DiGraph()
    graph.add_nodes_from([('A', {'ns': 'HGNC', 'id': '0'}),
                          ('B', {'ns': 'HGNC', 'id': '1'})])
    graph.add_edge('A', 'B')
    graph.graph['edge_by_hash'] = {'123456': ('A', 'B')}
    query = NetworkSearchQuery(source='A', mesh_ids=['D000544'],
                               strict_mesh_id_filtering=True)
    bfsq = BreadthFirstSearchQuery(query)
    options = set(bfsq.run_options(graph=graph).keys())
    _match_args(run_options=options, alg_fun=alg_func_mapping[bfsq.alg_name])


def test_dijkstra_query():
    # Test belief weight
    query = NetworkSearchQuery(source='A', weighted=True)
    dijq = DijkstraQuery(query)
    options = set(dijq.run_options().keys())
    _match_args(run_options=options, alg_fun=alg_func_mapping[dijq.alg_name])

    # Test context weight
    query = NetworkSearchQuery(source='A', mesh_ids=['D000544'],
                               strict_mesh_id_filtering=False)
    dijq = DijkstraQuery(query)
    options = set(dijq.run_options().keys())
    _match_args(run_options=options, alg_fun=alg_func_mapping[dijq.alg_name])
