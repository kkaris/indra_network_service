"""
Todo
    Add tests for:
    - Test arg types match if possible, i.e. is the model's attribute of the
      same type as the arg of the algorithm function
FixMe
    Add mock db call for
    indra_db.client.readonly.mesh_ref_counts::get_mesh_ref_counts
    using moto? mock?
Note: The tests here currently rely on being able to call indra_db (via
PathQuery._get_mesh_options in indra_network_search.query), which is blocked
from non-hms and non-AWS IP addresses, unless explicitly added.
"""
from inspect import signature
import networkx as nx
from typing import Set, Callable
from indra_network_search.util import get_mandatory_args
from indra_network_search.data_models import NetworkSearchQuery
from indra_network_search.query import SharedTargetsQuery,\
    SharedRegulatorsQuery, ShortestSimplePathsQuery, BreadthFirstSearchQuery,\
    DijkstraQuery, OntologyQuery, MissingParametersError, \
    InvalidParametersError, alg_func_mapping, pass_stmt, \
    _get_edge_filter_func, EdgeFilter
from indra_network_search.tests.util import unsigned_graph


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
    query = NetworkSearchQuery(source='A', target='B', shared_regulators=True)
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

    # Test the reverse search
    rev_query = query.reverse_search()
    assert rev_query.source == query.target
    assert rev_query.target == query.source

    sspq_rev = ShortestSimplePathsQuery(rev_query)
    options_rev = sspq_rev.run_options()
    _match_args(set(options_rev.keys()), alg_func_mapping[sspq_rev.alg_name])


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


def test_pass_stmt():
    # stmt_types: Optional[List[str]],
    stmt_dict = {'stmt_type': 'Activation'}
    assert pass_stmt(stmt_dict=stmt_dict, stmt_types=['activation']) == True
    assert pass_stmt(stmt_dict=stmt_dict, stmt_types=['complex']) == False

    # hash_blacklist: Optional[List[int]],
    stmt_dict = {'stmt_hash': 123456}
    assert pass_stmt(stmt_dict=stmt_dict) == True
    assert pass_stmt(stmt_dict=stmt_dict, hash_blacklist=[654321]) == True
    assert pass_stmt(stmt_dict=stmt_dict, hash_blacklist=[123456]) == False

    # check_curated: bool,
    stmt_dict = {'curated': True}
    assert pass_stmt(stmt_dict=stmt_dict, check_curated=True) == True
    assert pass_stmt(stmt_dict=stmt_dict) == True

    stmt_dict = {'curated': False}
    assert pass_stmt(stmt_dict=stmt_dict, check_curated=True) == False
    assert pass_stmt(stmt_dict=stmt_dict) == True

    # belief_cutoff: float = 0
    stmt_dict = {'belief': 0.7}
    assert pass_stmt(stmt_dict=stmt_dict) == True
    assert pass_stmt(stmt_dict=stmt_dict, belief_cutoff=0.6) == True
    assert pass_stmt(stmt_dict=stmt_dict, belief_cutoff=0.8) == False


def test_bfs_edge_filter():
    # Test basic functionality

    # stmt_types: Optional[List[str]],
    edge_filter_func = _get_edge_filter_func(stmt_types=['activation'])
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == True
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'testosterone') == False

    # hash_blacklist: Optional[List[int]],
    edge_filter_func = _get_edge_filter_func(hash_blacklist=[5603789525715921])
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == False
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'testosterone') == True

    # check_curated: bool,
    edge_filter_func = _get_edge_filter_func(check_curated=True)
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == True
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'MBD2') == False

    # belief_cutoff: float
    edge_filter_func = _get_edge_filter_func(belief_cutoff=0.8)
    assert edge_filter_func(unsigned_graph, 'PATZ1', 'CHEK1') == True
    assert edge_filter_func(unsigned_graph, 'CHEK1', 'NCOA') == False

    # Test getting edge filter from BreadthFirstSearchQuery
    # stmt_types
    rq = NetworkSearchQuery(source='BRCA1', stmt_filter=['Activation'])
    bfsq = BreadthFirstSearchQuery(rq)
    run_options = bfsq.run_options(graph=unsigned_graph)
    edge_filter_func: EdgeFilter = run_options['edge_filter']
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == True
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'testosterone') == False

    # hash_blacklist
    rq = NetworkSearchQuery(source='BRCA1',
                            edge_hash_blacklist=[5603789525715921])
    bfsq = BreadthFirstSearchQuery(rq)
    run_options = bfsq.run_options(graph=unsigned_graph)
    edge_filter_func: EdgeFilter = run_options['edge_filter']
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == False
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'testosterone') == True

    # Curated
    rq = NetworkSearchQuery(source='BRCA1', curated_db_only=True)
    bfsq = BreadthFirstSearchQuery(rq)
    run_options = bfsq.run_options(graph=unsigned_graph)
    edge_filter_func: EdgeFilter = run_options['edge_filter']
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'AR') == True
    assert edge_filter_func(unsigned_graph, 'BRCA1', 'MBD2') == False

    # belief_cutoff: float
    rq = NetworkSearchQuery(source='BRCA1', belief_cutoff=0.8)
    bfsq = BreadthFirstSearchQuery(rq)
    run_options = bfsq.run_options(graph=unsigned_graph)
    edge_filter_func: EdgeFilter = run_options['edge_filter']
    assert edge_filter_func(unsigned_graph, 'PATZ1', 'CHEK1') == True
    assert edge_filter_func(unsigned_graph, 'CHEK1', 'NCOA') == False
