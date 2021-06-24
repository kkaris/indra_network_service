"""
Tests the whole query pipeline from initial query building to results,
this is a better approach than to make partially overlapping tests for e.g.
query handling and result handling

Todo
    Add tests for:
    - Test arg types match if possible, i.e. is the model's attribute of the
      same type as the arg of the algorithm function
    - Test how non-resolving queries are handled, e.g. source or target does
      not exist in graph
    - Test some options (all would lead to permuation explosion) that
      shouldn't affect the outcome of the result
FixMe
    Add mock db call for
    indra_db.client.readonly.mesh_ref_counts::get_mesh_ref_counts
    using moto? mock?
Note: Some of the tests here currently rely on being able to call indra_db
(via PathQuery._get_mesh_options in indra_network_search.query), which is
blocked from non-hms and non-AWS IP addresses, unless explicitly added.
"""
from typing import Type, Union
from networkx import DiGraph
from pydantic import BaseModel
from depmap_analysis.network_functions.famplex_functions import \
    get_identifiers_url
from indra_network_search.data_models import *
from indra_network_search.query import SharedTargetsQuery, Query, \
    SharedRegulatorsQuery, ShortestSimplePathsQuery, \
    BreadthFirstSearchQuery, alg_func_mapping, alg_name_query_mapping
from indra_network_search.result_handler import ResultManager, \
    alg_manager_mapping
from .util import _match_args, _node_equals, _edge_data_equals, \
    _get_path_gen, _get_api_res, _get_edge_data_list, _get_path_list, \
    unsigned_graph, expanded_unsigned_graph, exp_signed_node_graph, \
    signed_node_graph


def _check_path_queries(graph: DiGraph, QueryCls: Type[Query],
                        rest_query: NetworkSearchQuery,
                        expected_res: PathResultData) -> bool:
    """Test path queries

    Parameters
    ----------
    graph: DiGraph
    QueryCls: Type[Query]
        The Query class used
    rest_query: NetworkSearchQuery
        The networksearch query to test
    expected_res: PathResultData
        The expected results

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
    assert results.is_empty() == expected_res.is_empty(), \
        f'result is {"empty" if results.is_empty() else "not empty"}; but ' \
        f'expected {"empty" if expected_res.is_empty() else "not empty"}'

    if expected_res.source is not None:
        assert _node_equals(results.source, expected_res.source), \
            f'Got node {results.source}; expected {expected_res.source}'
    if expected_res.target is not None:
        assert _node_equals(results.target, expected_res.target), \
            f'Got node {results.target}; expected {expected_res.target}'
    if expected_res.source is None and expected_res.target is None:
        raise ValueError('Both source and target of expected results are '
                         'None')

    for exp_len, expected in expected_res.paths.items():
        try:
            res_paths = results.paths[exp_len]
        except KeyError as ke:
            raise KeyError(f'Expected paths of length {exp_len} to exist') \
                from ke

        # Check that the number of paths are the same
        assert len(res_paths) == len(expected), \
            f'Expected {len(expected)} paths, got {len(res_paths)} paths'

        # If the paths are ordered, check the order of the paths and that
        # the nodes in the resulting path are as expected
        if rest_query.is_overall_weighted():
            for rp, ep in zip(res_paths, expected):
                for rn, en in zip(rp.path, ep.path):
                    assert _node_equals(rn, en), \
                        'Paths are out of order or nodes in path are not ' \
                        'the same'
        else:
            # Check that sets of paths are the same
            set_of_paths = {tuple(n.name for n in p.path) for p in res_paths}
            exp_path_sets = {tuple(n.name for n in p.path) for p in expected}
            assert set_of_paths == exp_path_sets, \
                'Paths are not the same'

    # Check search api
    query = QueryCls(query=rest_query)
    signed = rest_query.sign is not None
    api_res_mngr = _get_api_res(query=query, is_signed=signed, large=False)
    api_res = api_res_mngr.get_results()
    assert isinstance(api_res, PathResultData)
    assert not api_res.is_empty(), \
        f'result is "{"empty" if api_res.is_empty() else "not empty"}"; but ' \
        f'expected "{"empty" if expected_res.is_empty() else "not empty"}"'

    for exp_len, expected in expected_res.paths.items():
        try:
            res_paths = api_res.paths[exp_len]
        except KeyError as ke:
            raise KeyError(f'Expected paths of length {exp_len} to exist') \
                from ke

        # Check that the number of paths are the same
        assert len(res_paths) == len(expected), \
            f'Expected {len(expected)} paths, got {len(res_paths)} paths'

        # If the paths are ordered, check the order of the paths and that
        # the nodes in the resulting path are as expected
        if rest_query.is_overall_weighted():
            for rp, ep in zip(res_paths, expected):
                for rn, en in zip(rp.path, ep.path):
                    assert _node_equals(rn, en), \
                        f'Paths are out of order or nodes in path are not ' \
                        f'the same'
        else:
            # Check that sets of paths are the same
            set_of_paths = {tuple(n.name for n in p.path) for p in res_paths}
            exp_path_sets = {tuple(n.name for n in p.path) for p in expected}
            assert set_of_paths == exp_path_sets, f'Nodes are out of order'
    return True


def _check_shared_interactors(
        rest_query: NetworkSearchQuery,
        query: Union[SharedTargetsQuery, SharedRegulatorsQuery],
        graph: DiGraph, expected_res: SharedInteractorsResults) -> bool:

    # Check pipeline
    results: BaseModel = _check_pipeline(rest_query=rest_query,
                                         alg_name=query.alg_name, graph=graph)
    assert isinstance(results, SharedInteractorsResults), \
        f'Result is not SharedInteractorsResults model:\n{type(results)}'
    assert results.is_empty() == expected_res.is_empty(), \
        f'result is {"empty" if results.is_empty() else "not empty"}; but ' \
        f'expected {"empty" if expected_res.is_empty() else "not empty"}'

    # Check if results are as expected
    assert all(_edge_data_equals(d1, d1) for d1, d2 in
               zip(expected_res.source_data, results.source_data))
    assert all(_edge_data_equals(d1, d1) for d1, d2 in
               zip(expected_res.target_data, results.target_data))

    # Check search api
    signed = rest_query.sign is not None
    api_res_mngr = _get_api_res(query=query, is_signed=signed, large=True)
    api_res = api_res_mngr.get_results()
    assert isinstance(api_res, SharedInteractorsResults)
    assert api_res.is_empty() == expected_res.is_empty(), \
        f'result is "{"empty" if results.is_empty() else "not empty"}"; but ' \
        f'expected "{"empty" if expected_res.is_empty() else "not empty"}"'

    # Check is results are as expected
    assert all(_edge_data_equals(d1, d1) for d1, d2 in
               zip(expected_res.source_data, api_res.source_data))
    assert all(_edge_data_equals(d1, d1) for d1, d2 in
               zip(expected_res.target_data, api_res.target_data))

    return True


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
    ResMng: Type[ResultManager] = alg_manager_mapping[query.alg_name]
    res_mngr = ResMng(path_generator=path_gen, graph=graph,
                      **query.result_options())

    # Get results
    results = res_mngr.get_results()

    # Return results
    return results


def test_shortest_simple_paths():
    # Test:
    # - normal search
    # - signed search
    # - belief weighted
    # - reverse
    # - context weighted
    # - strict context
    # - stmt_filter
    # - edge_hash_blacklist
    # - allowed_ns
    # - node_blacklist
    # - path_length <-- path length
    # - belief_cutoff
    # - curated_db_only
    # - k_shortest <-- number of paths
    # - cull_best_node
    # Todo:
    #  - user_timeout
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100')
    brca1_up = Node(name='BRCA1', namespace='HGNC', identifier='1100', sign=0)
    brca1_down = Node(name='BRCA1', namespace='HGNC',
                      identifier='1100', sign=1)
    brca2 = Node(name='BRCA2', namespace='HGNC', identifier='1101')
    brca2_up = Node(name='BRCA2', namespace='HGNC', identifier='1101', sign=0)
    brca2_down = Node(name='BRCA2', namespace='HGNC',
                      identifier='1101', sign=1)

    # Create rest query - normal search
    rest_query = NetworkSearchQuery(source='BRCA1', target='BRCA2')
    str_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                 ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    str_paths5 = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                  ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=str_paths, graph=unsigned_graph,
                               large=False, signed=False),
             5: _get_path_list(str_paths=str_paths5, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)

    # Create rest query - signed search
    signed_rest_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                           sign='+')
    sign_str_paths = [(('BRCA1', 0), ('AR', 0), ('CHEK1', 0), ('BRCA2', 0))]
    sign_paths = {4: _get_path_list(str_paths=sign_str_paths,
                                    graph=signed_node_graph,
                                    large=False, signed=True)}
    expected_sign_paths: PathResultData = \
        PathResultData(source=brca1_up, target=brca2_up, paths=sign_paths)
    assert _check_path_queries(graph=signed_node_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=signed_rest_query,
                               expected_res=expected_sign_paths)

    signed_rest_query2 = NetworkSearchQuery(source='BRCA2', target='BRCA1',
                                            sign='-')
    sign_str_paths2 = [(('BRCA2', 0), ('BRCA1', 1))]
    sign_paths2 = {2: _get_path_list(str_paths=sign_str_paths2,
                                     graph=signed_node_graph,
                                     large=False, signed=True)}
    expected_sign_paths2: PathResultData = \
        PathResultData(source=brca2_up, target=brca1_down, paths=sign_paths2)
    assert _check_path_queries(graph=signed_node_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=signed_rest_query2,
                               expected_res=expected_sign_paths2)

    # Create rest query - belief weighted
    belief_weighted_query = NetworkSearchQuery(source=brca1.name,
                                               target=brca2.name,
                                               weighted=True)
    paths = {4: _get_path_list(str_paths=str_paths, graph=unsigned_graph,
                               large=False, signed=False),
             5: _get_path_list(str_paths=str_paths5, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=belief_weighted_query,
                               expected_res=expected_paths)

    # reverse
    reverse_query = rest_query.reverse_search()
    rev_str_paths = [('BRCA2', 'BRCA1')]
    rev_paths = {2: _get_path_list(str_paths=rev_str_paths,
                                   graph=unsigned_graph, large=False,
                                   signed=False)}
    expected_rev_paths: PathResultData = \
        PathResultData(source=brca2, target=brca1, paths=rev_paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=reverse_query,
                               expected_res=expected_rev_paths)

    # context weighted
    # Todo: Figure out how to get correct edges to mesh ids

    # strict context
    # Todo: Figure out how to get correct edges to mesh ids

    # stmt_filter - should remove ('testosterone', 'CHEK1'), ('NR2C2', 'CHEK1')
    stmt_filter_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                           stmt_filter=['Phosphorylation'])
    stmt_filter_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                         ['AR', 'MBD2', 'PATZ1']]
    stmt_filter_paths5 = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                          ['AR', 'MBD2', 'PATZ1']]

    paths = {4: _get_path_list(str_paths=stmt_filter_paths,
                               graph=unsigned_graph, large=False,
                               signed=False),
             5: _get_path_list(str_paths=stmt_filter_paths5,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=stmt_filter_query,
                               expected_res=expected_paths)

    # edge_hash_blacklist
    # Remove ('AR', 'CHEK1')
    hash_bl_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                       edge_hash_blacklist=[915990])
    hash_bl_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                     ['testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    hash_bl_paths5 = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                      ['testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=hash_bl_paths,
                               graph=unsigned_graph, large=False,
                               signed=False),
             5: _get_path_list(str_paths=hash_bl_paths5,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=hash_bl_query,
                               expected_res=expected_paths)

    # allowed_ns
    # Only allow HGNC: will remove testosterone and NCOA as node
    ns_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                  allowed_ns=['HGNC'])
    ns_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                ['AR', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=ns_paths, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=ns_query,
                               expected_res=expected_paths)

    # node_blacklist
    # Blacklist testosterone
    node_bl_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                       node_blacklist=['testosterone'])
    node_bl_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                     ['AR', 'NR2C2', 'MBD2', 'PATZ1']]
    node_bl_paths5 = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                      ['AR', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=node_bl_paths,
                               graph=unsigned_graph, large=False,
                               signed=False),
             5: _get_path_list(str_paths=node_bl_paths5,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=node_bl_query,
                               expected_res=expected_paths)

    # path_length
    pl5_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                   path_length=5)
    pl5_str_paths = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                     ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {5: _get_path_list(str_paths=pl5_str_paths,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=pl5_query,
                               expected_res=expected_paths)

    # belief_cutoff - filter out NCOA edges
    belief_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                      belief_cutoff=0.71)
    belief_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                    ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=belief_paths, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=belief_query,
                               expected_res=expected_paths)

    # curated_db_only
    curated_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                       curated_db_only=True)
    curated_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                     ['AR', 'testosterone', 'NR2C2']]
    paths = {4: _get_path_list(str_paths=curated_paths,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=curated_query,
                               expected_res=expected_paths)

    # k_shortest <-- number of paths to return
    k_short_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                       k_shortest=4)
    k_short_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                     ['AR', 'testosterone', 'NR2C2', 'MBD2']]
    paths = {4: _get_path_list(str_paths=k_short_paths,
                               graph=unsigned_graph, large=False,
                               signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=k_short_query,
                               expected_res=expected_paths)

    # cull_best_node
    cull_query = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                    cull_best_node=3)
    cull_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                  ['AR', 'testosterone', 'NR2C2']]
    paths = {4: _get_path_list(str_paths=cull_paths, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = \
        PathResultData(source=brca1, target=brca2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=cull_query,
                               expected_res=expected_paths)

    # user_timeout <-- not yet implemented
    # todo: add timeout test


def test_dijkstra():
    # Test weighted searches with all applicable options
    # Test signed weighted searches
    pass


def test_bfs_default():
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    rest_query = NetworkSearchQuery(source='BRCA1')
    str_paths2 = [('BRCA1', n) for n in
                  ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    str_paths3 = [('BRCA1', 'AR', 'CHEK1')]
    paths = {2: _get_path_list(str_paths=str_paths2, graph=unsigned_graph,
                               large=False, signed=False),
             3: _get_path_list(str_paths=str_paths3, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = PathResultData(source=brca1, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=BreadthFirstSearchQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)


def test_bfs_path_length():
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    rest_query = NetworkSearchQuery(source='BRCA1', max_per_node=10,
                                    path_length=4)
    str_paths4 = [('BRCA1', 'AR', 'CHEK1', 'BRCA2'),
                  ('BRCA1', 'AR', 'CHEK1', 'NCOA')]
    paths = {4: _get_path_list(str_paths=str_paths4, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = PathResultData(source=brca1, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=BreadthFirstSearchQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)


def test_bfs_depth_limit():
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    # Test depth limit = 4 (i.e. max number of edges = 4)
    rest_query = NetworkSearchQuery(source='BRCA1', depth_limit=4)
    str_paths2 = [('BRCA1', n) for n in
                  ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    str_paths3 = [('BRCA1', 'AR', 'CHEK1')]
    str_paths4 = [('BRCA1', 'AR', 'CHEK1', 'BRCA2'),
                  ('BRCA1', 'AR', 'CHEK1', 'NCOA')]
    paths = {2: _get_path_list(str_paths=str_paths2, graph=unsigned_graph,
                               large=False, signed=False),
             3: _get_path_list(str_paths=str_paths3, graph=unsigned_graph,
                               large=False, signed=False),
             4: _get_path_list(str_paths=str_paths4, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = PathResultData(source=brca1, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=BreadthFirstSearchQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)


def test_bfs_k_shortest():
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    rest_query = NetworkSearchQuery(source='BRCA1', k_shortest=3)
    str_paths2 = [('BRCA1', n) for n in
                  ['AR', 'testosterone', 'NR2C2']]
    paths = {2: _get_path_list(str_paths=str_paths2, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = PathResultData(source=brca1, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=BreadthFirstSearchQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)


def test_bfs_reverse():
    chek1 = Node(name='CHEK1', namespace='HGNC', identifier='1925',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1925'))
    rest_query = NetworkSearchQuery(target='CHEK1')
    str_paths2 = [(n, 'CHEK1') for n in
                  ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    str_paths3 = [('BRCA1', 'AR', 'CHEK1')]
    paths = {2: _get_path_list(str_paths=str_paths2, graph=unsigned_graph,
                               large=False, signed=False),
             3: _get_path_list(str_paths=str_paths3, graph=unsigned_graph,
                               large=False, signed=False)}
    expected_paths: PathResultData = PathResultData(target=chek1, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=BreadthFirstSearchQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)


def test_shared_interactors():
    brca1 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    brca1_up = Node(name='BRCA1', namespace='HGNC', identifier='1100', sign=0,
                    lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    brca1_down = Node(name='BRCA1', namespace='HGNC',
                      identifier='1100', sign=1,
                      lookup=get_identifiers_url(db_name='HGNC', db_id='1100'))
    brca2 = Node(name='BRCA2', namespace='HGNC', identifier='1101',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1101'))
    brca2_up = Node(name='BRCA2', namespace='HGNC', identifier='1101', sign=0,
                    lookup=get_identifiers_url(db_name='HGNC', db_id='1101'))
    brca2_down = Node(name='BRCA2', namespace='HGNC',
                      identifier='1101', sign=1,
                      lookup=get_identifiers_url(db_name='HGNC', db_id='1101'))

    # 'HDAC3': {'ns': 'HGNC', 'id': '4854'}
    hdac3 = Node(name='HDAC3', namespace='HGNC', identifier='4854',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='4854'))
    hdac3_up = Node(name='HDAC3', namespace='HGNC', identifier='4854', sign=0,
                    lookup=get_identifiers_url(db_name='HGNC', db_id='4854'))
    hdac3_down = Node(name='HDAC3', namespace='HGNC',
                      identifier='4854', sign=1,
                      lookup=get_identifiers_url(db_name='HGNC', db_id='4854'))

    # 'CHEK1': {'ns': 'HGNC', 'id': '1925'}
    chek1 = Node(name='CHEK1', namespace='HGNC', identifier='1925',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='1925'))
    chek1_up = Node(name='CHEK1', namespace='HGNC', identifier='1925', sign=0,
                    lookup=get_identifiers_url(db_name='HGNC', db_id='1925'))
    chek1_down = Node(name='CHEK1', namespace='HGNC', identifier='1925',
                      lookup=get_identifiers_url(db_name='HGNC', db_id='1925'))

    # 'H2AZ1': {'ns': 'HGNC', 'id': '4741'}
    h2az1 = Node(name='H2AZ1', namespace='HGNC', identifier='4741',
                 lookup=get_identifiers_url(db_name='HGNC', db_id='4741'))
    h2az1_up = Node(name='H2AZ1', namespace='HGNC', identifier='4741', sign=0,
                    lookup=get_identifiers_url(db_name='HGNC', db_id='4741'))
    h2az1_down = Node(name='H2AZ1', namespace='HGNC',
                      identifier='4741', sign=1,
                      lookup=get_identifiers_url(db_name='HGNC', db_id='4741'))

    # Check shared targets
    rest_query = NetworkSearchQuery(source=brca1.name, target=hdac3.name)
    source_edges = [('BRCA1', n) for n in
                    ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    target_edges = [('HDAC3', n) for n in
                    ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    stq = SharedTargetsQuery(query=rest_query)
    expected_results = SharedInteractorsResults(
        source_data=_get_edge_data_list(edge_list=source_edges,
                                        graph=expanded_unsigned_graph,
                                        large=True, signed=False),
        target_data=_get_edge_data_list(edge_list=target_edges,
                                        graph=expanded_unsigned_graph,
                                        large=True, signed=False),
        downstream=True)
    assert _check_shared_interactors(rest_query=rest_query, query=stq,
                                     graph=expanded_unsigned_graph,
                                     expected_res=expected_results)

    # Check shared regulators
    rest_query = NetworkSearchQuery(source=chek1.name, target=h2az1.name,
                                    shared_regulators=True)
    source_edges = [(n, chek1.name) for n in
                    ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    target_edges = [(n, h2az1.name) for n in
                    ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    srq = SharedRegulatorsQuery(query=rest_query)
    expected_results = SharedInteractorsResults(
        source_data=_get_edge_data_list(edge_list=source_edges,
                                        graph=expanded_unsigned_graph,
                                        large=True, signed=False),
        target_data=_get_edge_data_list(edge_list=target_edges,
                                        graph=expanded_unsigned_graph,
                                        large=True, signed=False),
        downstream=False)
    assert _check_shared_interactors(rest_query=rest_query, query=srq,
                                     graph=expanded_unsigned_graph,
                                     expected_res=expected_results)

    # - sign
    # Check shared targets
    rest_query = NetworkSearchQuery(source=brca1.name, target=hdac3.name,
                                    sign='+')
    source_edges = [(brca1_up.signed_node_tuple(), ('AR', 0))]
    target_edges = [(hdac3_up.signed_node_tuple(), ('AR', 0))]
    stq = SharedTargetsQuery(query=rest_query)
    expected_results = SharedInteractorsResults(
        source_data=_get_edge_data_list(edge_list=source_edges,
                                        graph=exp_signed_node_graph,
                                        large=True, signed=True),
        target_data=_get_edge_data_list(edge_list=target_edges,
                                        graph=exp_signed_node_graph,
                                        large=True, signed=True),
        downstream=True)
    assert _check_shared_interactors(rest_query=rest_query, query=stq,
                                     graph=exp_signed_node_graph,
                                     expected_res=expected_results)

    # Check shared regulators
    rest_query = NetworkSearchQuery(source=chek1.name, target=h2az1.name,
                                    shared_regulators=True)
    source_edges = [(('AR', 0), chek1_up.signed_node_tuple())]
    target_edges = [(('AR', 0), h2az1_up.get_unsigned_node())]
    srq = SharedRegulatorsQuery(query=rest_query)
    expected_results = SharedInteractorsResults(
        source_data=_get_edge_data_list(edge_list=source_edges,
                                        graph=exp_signed_node_graph,
                                        large=True, signed=True),
        target_data=_get_edge_data_list(edge_list=target_edges,
                                        graph=exp_signed_node_graph,
                                        large=True, signed=True),
        downstream=False)
    assert _check_shared_interactors(rest_query=rest_query, query=srq,
                                     graph=exp_signed_node_graph,
                                     expected_res=expected_results)

    # Check
    # - allowed ns
    # - stmt types
    # - source filter
    # - max results
    # - hash blacklist
    # - node blacklist
    # - belief cutoff
    # - curated db only
