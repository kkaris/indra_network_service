"""
Tests the whole query pipeline from initial query building to results,
this is a better approach than to make partially overlapping tests for e.g.
query handling and result handling

Todo
    Add tests for:
    - Test arg types match if possible, i.e. is the model's attribute of the
      same type as the arg of the algorithm function
FixMe
    Add mock db call for
    indra_db.client.readonly.mesh_ref_counts::get_mesh_ref_counts
    using moto? mock?
Note: Some of the tests here currently rely on being able to call indra_db
(via PathQuery._get_mesh_options in indra_network_search.query), which is
blocked from non-hms and non-AWS IP addresses, unless explicitly added.
"""
from inspect import signature
from typing import Set, Callable, Dict, Any, Type, Tuple, Union, List
from networkx import DiGraph
import networkx as nx
from pydantic import BaseModel
from indra.explanation.pathfinding import bfs_search, shortest_simple_paths,\
    open_dijkstra_search
from indra_network_search.util import get_mandatory_args
from indra_network_search.data_models import *
from indra_network_search.query import SharedTargetsQuery, Query,\
    SharedRegulatorsQuery, ShortestSimplePathsQuery, BreadthFirstSearchQuery,\
    DijkstraQuery, OntologyQuery, MissingParametersError, \
    InvalidParametersError, alg_func_mapping, alg_name_query_mapping,\
    SubgraphQuery
from indra.explanation.pathfinding import shortest_simple_paths
from indra_network_search.result_handler import OntologyResultManager, \
    SharedInteractorsResultManager, ShortestSimplePathsResultManager, \
    ResultManager, alg_manager_mapping
from indra_network_search.pathfinding import shared_parents, \
    shared_interactors, get_subgraph_edges
from indra_network_search.search_api import IndraNetworkSearchAPI
from . import edge_data, nodes


def _setup_graph() -> DiGraph:
    g = DiGraph()
    for edge in edge_data:
        # Add node data
        if edge[0] not in g.nodes:
            g.add_node(edge[0], **nodes[edge[0]])
        if edge[1] not in g.nodes:
            g.add_node(edge[1], **nodes[edge[1]])

        # Add edge data
        g.add_edge(*edge, **edge_data[edge])
    return g


def _setup_api() -> IndraNetworkSearchAPI:
    # fixme: add signed graph when that development is done
    return IndraNetworkSearchAPI(unsigned_graph=unsigned_graph,
                                 signed_node_graph=DiGraph())


unsigned_graph = _setup_graph()
search_api = _setup_api()


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


def _node_equals(node: Node, other_node: Node) -> bool:
    # Check node name, namespace, identifier and ignore node lookup
    other_node_dict = other_node.dict(exclude={'lookup'})
    return all(v == other_node_dict[k] for k, v in
               node.dict(exclude={'lookup'}).items())


def _check_path_queries(
        graph: DiGraph, QueryCls: Type[Query], rest_query: NetworkSearchQuery,
        expected_paths: Dict[int, Union[Set[Tuple[str, ...]],
                             List[Tuple[str, ...]]]]) -> bool:
    """Test path queries

    Parameters
    ----------
    graph: DiGraph
    QueryCls: Type[Query]
        The Query class used
    rest_query: NetworkSearchQuery
        The networksearch query to test
    expected_paths: Dict[int, Union[Set[Tuple[str, ...]],
                                    List[Tuple[str, ...]]]]
        A dict of a set or list of paths keyed by their path lengths. If
        list, the paths are assumed to have that specific order

    Returns
    -------
    bool

    """
    # Check pipeline
    results = _check_pipeline(rest_query=rest_query,
                              alg_name=QueryCls.alg_name,
                              graph=graph)

    assert isinstance(results, PathResultData), \
        f'results is not PathResultData model:\n{str(results)}'

    # Check if we have any results
    assert results.is_empty() is not bool(expected_paths), \
        f'result is "{"empty" if results.is_empty() else "not empty"}"; but ' \
        f'expected "{"not empty" if expected_paths else "empty"}"'

    for exp_len, expected in expected_paths.items():
        res_paths = results.paths[exp_len]
        # Check that the number of paths are the same
        assert len(res_paths) == len(expected), \
            f'Expected {len(expected)} paths, got {len(res_paths)} paths'

        # If the paths are ordered, check the order of the paths and that
        # the nodes in the resulting path are as expected
        if isinstance(expected, list):
            assert all(all(n.name == en for n, en in zip(p1, p2))
                       for p1, p2 in zip(res_paths, expected)), \
                f'Paths are out of order or nodes in path are not the same'
        elif isinstance(expected, set):
            # Check that sets of paths are the same
            set_of_paths = {tuple(n.name for n in p.path) for p in res_paths}
            assert set_of_paths == expected, \
                f'Paths are permuted'

    # Check search api
    query = QueryCls(query=rest_query)
    signed = rest_query.sign is not None
    api_res_mngr = _get_api_res(query=query, is_signed=signed)
    api_res = api_res_mngr.get_results()
    assert isinstance(api_res, PathResultData)
    assert not api_res.is_empty()

    for exp_len, expected in expected_paths.items():
        res_paths = api_res.paths[exp_len]
        # Check that the number of paths are the same
        assert len(res_paths) == len(expected), \
            f'Expected {len(expected)} paths, got {len(res_paths)} paths'

        # If the paths are ordered, check the order of the paths and that
        # the nodes in the resulting path are as expected
        if isinstance(expected, list):
            assert all(all(n.name == en for n, en in zip(p1, p2))
                       for p1, p2 in zip(res_paths, expected)), \
                f'Paths are out of order or nodes in path are not the same'
        elif isinstance(expected, set):
            # Check that sets of paths are the same
            set_of_paths = {tuple(n.name for n in p.path) for p in res_paths}
            assert set_of_paths == expected, \
                f'Paths are permuted'

    return True


def _get_path_gen(alg_func: Callable, graph: DiGraph,
                  run_options: Dict[str, Any]):
    # This helper mostly does the job of using the correct keyword for the
    # graph argument
    if alg_func.__name__ == bfs_search.__name__:
        return bfs_search(g=graph, **run_options)
    elif alg_func.__name__ == shortest_simple_paths.__name__:
        return shortest_simple_paths(G=graph, **run_options)
    elif alg_func.__name__ == open_dijkstra_search.__name__:
        return open_dijkstra_search(g=graph, **run_options)
    elif alg_func.__name__ == shared_parents.__name__:
        return shared_parents(**run_options)
    elif alg_func.__name__ == shared_interactors.__name__:
        # Should catch 'shared_interactors', 'shared_regulators' and
        # 'shared_targets'
        return shared_interactors(**run_options)
    elif alg_func.__name__ == get_subgraph_edges.__name__:
        return get_subgraph_edges(graph=graph, **run_options)
    else:
        raise ValueError(f'Unrecognized function {alg_func.__name__}')


def _get_api_res(query: Query, is_signed: bool) -> ResultManager:
    # Helper to map Query to correct search_api method
    if query.alg_name == bfs_search.__name__:
        assert isinstance(query, BreadthFirstSearchQuery)
        return search_api.breadth_first_search(query, is_signed)
    elif query.alg_name == shortest_simple_paths.__name__:
        assert isinstance(query, ShortestSimplePathsQuery)
        return search_api.shortest_simple_paths(query, is_signed)
    elif query.alg_name == open_dijkstra_search.__name__:
        assert isinstance(query, DijkstraQuery)
        return search_api.dijkstra(query, is_signed)
    elif query.alg_name == shared_parents.__name__:
        assert isinstance(query, OntologyQuery)
        return search_api.shared_parents(query)
    elif query.alg_name == 'shared_targets':
        assert isinstance(query, SharedTargetsQuery)
        return search_api.shared_targets(query, is_signed)
    elif query.alg_name == 'shared_regulators':
        assert isinstance(query, SharedRegulatorsQuery)
        return search_api.shared_regulators(query)
    elif query.alg_name == get_subgraph_edges.__name__:
        assert isinstance(query, SubgraphQuery)
        return search_api.subgraph_query(query)
    else:
        raise ValueError(f'Unrecognized Query class {type(query)}')


def _check_pipeline(rest_query: NetworkSearchQuery, alg_name: str,
                    graph: DiGraph) -> BaseModel:
    """Checks pipeline from incoming Query to result model"""
    # Map to Query:
    QueryCls = alg_name_query_mapping[alg_name]
    query = QueryCls(rest_query)

    # Get run options, the query class will run some checks on its own
    options = query.run_options(graph=graph)

    # Run argument matching to see if the algorithm that fulfills the query
    # get the correct arguments
    _match_args(run_options=set(options.keys()),
                alg_fun=alg_func_mapping[query.alg_name])

    # Get path_gen
    alg_func = alg_func_mapping[query.alg_name]
    path_gen = _get_path_gen(alg_func=alg_func, graph=graph,
                             run_options=options)

    # Get the result manager
    # Todo: Add signed node graph for future tests of signed paths
    ResMng: Type[ResultManager] = alg_manager_mapping[query.alg_name]
    res_mngr = ResMng(path_generator=path_gen,
                      graph=graph,
                      **query.result_options())

    # Get results
    results = res_mngr.get_results()

    # Return results
    return results


def test_shortest_simple_paths():
    # Test:
    # - normal search
    # - belief weighted
    # - reverse
    # - context weighted
    # - strict context
    # - stmt_filter
    # - edge_hash_blacklist
    # - allowed_ns
    # - node_blacklist
    # - path_length
    # - belief_cutoff
    # - curated_db_only
    # - k_shortest <-- number of paths to return
    # - cull_best_node
    # - user_timeout <-- not yet implemented

    # Create rest query - normal search
    rest_query = NetworkSearchQuery(source='BRCA1', target='BRCA2')
    expected_paths = {4: {('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                          ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']}}
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=rest_query,
                               expected_paths=expected_paths)

    # Create rest query - belief weighted
    belief_weighted_query = NetworkSearchQuery(source='BRCA1',
                                               target='BRCA2',
                                               weighted=True)
    expected_paths = {4: [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                          ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]}
    # results = _check_pipeline(
    #     rest_query=rest_query, alg_name=ShortestSimplePathsQuery.alg_name,
    #     graph=unsigned_graph
    # )
    # assert isinstance(results, PathResultData)
    # assert not results.is_empty()
    #
    # # Get results from search_api
    # api_res_mngr = \
    #     search_api.shortest_simple_paths(
    #         ShortestSimplePathsQuery(query=rest_query), is_signed=False
    #     )
    # api_res = api_res_mngr.get_results()
    # assert isinstance(api_res, PathResultData)
    # assert not api_res.is_empty()
    #
    # # Compare results
    # assert len(results.paths[4]) == 5, f'{len(results.paths[4])} paths found'
    # assert len(api_res.paths[4]) == 5, f'{len(api_res.paths[4])} paths found'
    # assert all(p1 == p2 for p1, p2 in zip(results.paths[4], api_res.paths[4]))
    # found_paths = [tuple(n.name for n in p.path) for p in results.paths[4]]
    # api_paths = [tuple(n.name for n in p.path) for p in api_res.paths[4]]
    # # Check order
    # expected_order = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
    #                   ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    # assert all(p == ep for p, ep in zip(found_paths, expected_order))
    # assert all(p == ep for p, ep in zip(api_paths, expected_order))

    # reverse
    # context weighted
    # strict context
    # stmt_filter
    # edge_hash_blacklist
    # allowed_ns
    # node_blacklist
    # path_length
    # belief_cutoff
    # curated_db_only
    # k_shortest <-- number of paths to return
    # cull_best_node
    # user_timeout <-- not yet implemented



def test_dijkstra():
    pass
    # Create dijkstra specific query
    # Test query
    # Test results mngr
    # Check results
    # Compare results with running search_api
