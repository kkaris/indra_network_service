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
from typing import Set, Callable, Dict, Any, Type, Tuple, Union, List, Optional
from networkx import DiGraph, MultiDiGraph
from pydantic import BaseModel
from indra.assemblers.indranet.net import default_sign_dict
from indra.explanation.pathfinding import bfs_search, shortest_simple_paths,\
    open_dijkstra_search
from indra.explanation.model_checker.model_checker import \
    signed_edges_to_signed_nodes
from indra_network_search.util import get_mandatory_args
from indra_network_search.data_models import *
from indra_network_search.query import SharedTargetsQuery, Query,\
    SharedRegulatorsQuery, ShortestSimplePathsQuery, BreadthFirstSearchQuery,\
    DijkstraQuery, OntologyQuery, MissingParametersError, \
    InvalidParametersError, alg_func_mapping, alg_name_query_mapping,\
    SubgraphQuery
from indra_network_search.result_handler import ResultManager, \
    alg_manager_mapping, DB_URL_EDGE, DB_URL_HASH
from indra_network_search.pathfinding import shared_parents, \
    shared_interactors, get_subgraph_edges
from indra_network_search.search_api import IndraNetworkSearchAPI
from . import edge_data, nodes, more_edge_data


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


def _setup_bigger_graph() -> DiGraph:
    big_g = DiGraph()
    for edge in more_edge_data:
        # Add node data
        if edge[0] not in big_g.nodes:
            big_g.add_node(edge[0], **nodes[edge[0]])
        if edge[1] not in big_g.nodes:
            big_g.add_node(edge[1], **nodes[edge[1]])

        # Add edge data
        big_g.add_edge(*edge, **more_edge_data[edge])
    return big_g


def _setup_signed_node_graph() -> DiGraph:
    seg = MultiDiGraph()
    dg = _setup_graph()
    for u, v in dg.edges:
        edge_dict = dg.edges[(u, v)]
        if edge_dict['statements'][0]['stmt_type'] in default_sign_dict:
            sign = default_sign_dict[edge_dict['statements'][0]['stmt_type']]
            # Add nodes if not previously present
            if u not in seg.nodes:
                seg.add_node(u, **dg.nodes[u])
            if v not in seg.nodes:
                seg.add_node(v, **dg.nodes[v])

            # Add edge
            seg.add_edge(u, v, sign, sign=sign, **edge_dict)

        # If not signed type
        else:
            continue
    return signed_edges_to_signed_nodes(graph=seg, copy_edge_data=True)


def _setup_api(large: bool) -> IndraNetworkSearchAPI:
    # fixme: add signed graph when that development is done
    g = expanded_unsigned_graph if large else unsigned_graph
    return IndraNetworkSearchAPI(unsigned_graph=g,
                                 signed_node_graph=DiGraph())


unsigned_graph = _setup_graph()
expanded_unsigned_graph = _setup_bigger_graph()
signed_node_graph = _setup_signed_node_graph()
search_api = _setup_api(False)
exp_search_api = _setup_api(True)


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
    # Check node name, namespace, identifier.
    # Ignore 'lookup' if either node does not have it.
    exclude = {'lookup'} if node.lookup is None \
                            or other_node.lookup is None else set()
    other_node_dict = other_node.dict(exclude=exclude)
    return all(v == other_node_dict[k] for k, v in
               node.dict(exclude=exclude).items())


def _edge_data_equals(edge_model: EdgeData,
                      other_edge_model: EdgeData) -> bool:
    # Check nodes of edge
    assert all(_node_equals(n1, n2) for n1, n2 in zip(edge_model.edge,
                                                      other_edge_model.edge))
    assert edge_model.db_url_edge == other_edge_model.db_url_edge
    assert edge_model.sign == other_edge_model.sign
    assert edge_model.belief == other_edge_model.belief
    assert edge_model.context_weight == other_edge_model.context_weight
    assert edge_model.weight == other_edge_model.weight
    assert \
        all(all(_basemodels_equal(s1, s2, False) for s1, s2 in
                zip(other_edge_model.statements[k], st_data_lst))
            for k, st_data_lst in edge_model.statements.items())
    return True


def _basemodels_equal(basemodel: BaseModel, other_basemodel: BaseModel,
                      any_item: bool,
                      exclude: Optional[Set[str]] = None) -> bool:
    b1d = basemodel.dict(exclude=exclude)
    b2d = other_basemodel.dict(exclude=exclude)
    qual_func = any if any_item else all
    return qual_func(_equals(b1d[k1], b2d[k2], any_item)
                     for k1, k2 in zip(b1d, b2d))


def _equals(d1: Union[str, int, float, List, Set, Tuple, Dict],
            d2: Union[str, int, float, List, Set, Tuple, Dict],
            any_item: bool) -> bool:
    qual_func = any if any_item else all
    if d1 is None:
        return d2 is None
    elif isinstance(d1, (str, int, float)):
        return d1 == d2
    elif isinstance(d1, (list, tuple)):
        return qual_func(_equals(e1, e2, any_item) for e1, e2 in zip(d1, d2))
    elif isinstance(d1, set):
        return d1 == d2
    elif isinstance(d1, dict):
        return qual_func(_equals(d1[k1], d2[k2], False)
                         for k1, k2 in zip(d1, d2))
    else:
        raise TypeError(f'Unable to do comparison of type {type(d1)}')


def _get_node(name: Union[str, Tuple[str, int]],
              graph: DiGraph) -> Optional[Node]:
    # Signed node
    if isinstance(name, tuple):
        node_name, sign = name
        if node_name in graph.nodes:
            return Node(name=node_name, namespace=graph.nodes[name]['ns'],
                        identifier=graph.nodes[name]['id'], sign=sign)
    # Unsigned node
    else:
        node_name = name
        if node_name in graph.nodes:
            return Node(name=node_name, namespace=graph.nodes[name]['ns'],
                        identifier=graph.nodes[name]['id'])

    raise ValueError(f'{name} not in graph')


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
        f'result is "{"empty" if results.is_empty() else "not empty"}"; but ' \
        f'expected "{"empty" if expected_res.is_empty() else "not empty"}"'

    assert _node_equals(results.source, expected_res.source)
    assert _node_equals(results.target, expected_res.target)

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
                        f'Paths are out of order or nodes in path are not ' \
                        f'the same'
        else:
            # Check that sets of paths are the same
            set_of_paths = {tuple(n.name for n in p.path) for p in res_paths}
            exp_path_sets = {tuple(n.name for n in p.path) for p in expected}
            assert set_of_paths == exp_path_sets, f'Nodes are out of order'

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
        return shared_interactors(graph=graph, **run_options)
    elif alg_func.__name__ == get_subgraph_edges.__name__:
        return get_subgraph_edges(graph=graph, **run_options)
    else:
        raise ValueError(f'Unrecognized function {alg_func.__name__}')


def _get_api_res(query: Query, is_signed: bool, large: bool) -> ResultManager:
    api = exp_search_api if large else search_api
    # Helper to map Query to correct search_api method
    if query.alg_name == bfs_search.__name__:
        assert isinstance(query, BreadthFirstSearchQuery)
        return api.breadth_first_search(query, is_signed)
    elif query.alg_name == shortest_simple_paths.__name__:
        assert isinstance(query, ShortestSimplePathsQuery)
        return api.shortest_simple_paths(query, is_signed)
    elif query.alg_name == open_dijkstra_search.__name__:
        assert isinstance(query, DijkstraQuery)
        return api.dijkstra(query, is_signed)
    elif query.alg_name == shared_parents.__name__:
        assert isinstance(query, OntologyQuery)
        return api.shared_parents(query)
    elif query.alg_name == 'shared_targets':
        assert isinstance(query, SharedTargetsQuery)
        return api.shared_targets(query, is_signed)
    elif query.alg_name == 'shared_regulators':
        assert isinstance(query, SharedRegulatorsQuery)
        return api.shared_regulators(query)
    elif query.alg_name == get_subgraph_edges.__name__:
        assert isinstance(query, SubgraphQuery)
        return api.subgraph_query(query)
    else:
        raise ValueError(f'Unrecognized Query class {type(query)}')


def _get_edge_data_list(
        edge_list: List[Union[Tuple[str, str], Tuple[Tuple[str, int]],
                              Tuple[str, int]]],
        graph: DiGraph, large: bool
) -> List[EdgeData]:
    edges: List[EdgeData] = []
    for a, b in edge_list:
        edata = _get_edge_data(edge=(a, b), graph=graph, large=large)
        edges.append(edata)
    return edges


def _get_edge_data(edge: Tuple[Union[str, Tuple[str, int]], ...],
                   graph: DiGraph, large: bool) -> EdgeData:
    ed = more_edge_data[edge] if large else edge_data[edge]
    stmt_dict = {}

    for sd in ed['statements']:
        url = DB_URL_HASH.format(stmt_hash=sd['stmt_hash'])
        stmt_data = StmtData(db_url_hash=url, **sd)
        try:
            stmt_dict[stmt_data.stmt_type].append(stmt_data)
        except KeyError:
            stmt_dict[stmt_data.stmt_type] = [stmt_data]

    node_edge = [_get_node(edge[0], graph), _get_node(edge[1], graph)]
    edge_url = DB_URL_EDGE.format(subj_id=node_edge[0].identifier,
                                  subj_ns=node_edge[0].namespace,
                                  obj_id=node_edge[1].identifier,
                                  obj_ns=node_edge[1].namespace)

    return EdgeData(edge=node_edge, statements=stmt_dict, belief=ed['belief'],
                    weight=ed['weight'], db_url_edge=edge_url)


def _get_path_list(str_paths: List[Tuple[Union[str, Tuple[str, int]], ...]],
                   graph: DiGraph, large: bool) -> List[Path]:
    paths: List[Path] = []
    for spath in str_paths:
        path: List[Node] = []
        for sn in spath:
            path.append(_get_node(sn, graph))
        edl: List[EdgeData] = []
        for a, b in zip(spath[:-1], spath[1:]):
            edge = (a, b)
            e_data = _get_edge_data(edge=edge, graph=graph, large=large)
            edl.append(e_data)
        paths.append(Path(path=path, edge_data=edl))
    return paths


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
    # - path_length <-- path length
    # - belief_cutoff
    # - curated_db_only
    # - k_shortest <-- number of paths
    # - cull_best_node
    # - user_timeout <-- not yet implemented!
    BRCA1 = Node(name='BRCA1', namespace='HGNC', identifier='1100')
    BRCA2 = Node(name='BRCA2', namespace='HGNC', identifier='1101')

    # Create rest query - normal search
    rest_query = NetworkSearchQuery(source='BRCA1', target='BRCA2')
    str_paths = [('BRCA1', n, 'CHEK1', 'BRCA2') for n in
                 ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    str_paths5 = [('BRCA1', n, 'CHEK1', 'NCOA', 'BRCA2') for n in
                  ['AR', 'testosterone', 'NR2C2', 'MBD2', 'PATZ1']]
    paths = {4: _get_path_list(str_paths=str_paths, graph=unsigned_graph,
                               large=False),
             5: _get_path_list(str_paths=str_paths5, graph=unsigned_graph,
                               large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=rest_query,
                               expected_res=expected_paths)

    # Create rest query - belief weighted
    belief_weighted_query = NetworkSearchQuery(source=BRCA1.name,
                                               target=BRCA2.name,
                                               weighted=True)
    paths = {4: _get_path_list(str_paths=str_paths, graph=unsigned_graph,
                               large=False),
             5: _get_path_list(str_paths=str_paths5, graph=unsigned_graph,
                               large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=belief_weighted_query,
                               expected_res=expected_paths)

    # reverse
    reverse_query = rest_query.reverse_search()
    rev_str_paths = [('BRCA2', 'BRCA1')]
    rev_paths = {2: _get_path_list(str_paths=rev_str_paths,
                                   graph=unsigned_graph, large=False)}
    expected_rev_paths: PathResultData = \
        PathResultData(source=BRCA2, target=BRCA1, paths=rev_paths)
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
                               graph=unsigned_graph, large=False),
             5: _get_path_list(str_paths=stmt_filter_paths5,
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               graph=unsigned_graph, large=False),
             5: _get_path_list(str_paths=hash_bl_paths5,
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               graph=unsigned_graph, large=False),
             5: _get_path_list(str_paths=node_bl_paths5,
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               graph=unsigned_graph, large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
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
                               large=False)}
    expected_paths: PathResultData = \
        PathResultData(source=BRCA1, target=BRCA2, paths=paths)
    assert _check_path_queries(graph=unsigned_graph,
                               QueryCls=ShortestSimplePathsQuery,
                               rest_query=cull_query,
                               expected_res=expected_paths)

    # user_timeout <-- not yet implemented
    # todo: add timeout test


def test_dijkstra():
    pass
    # Create dijkstra specific query
    # Test query
    # Test results mngr
    # Check results
    # Compare results with running search_api
