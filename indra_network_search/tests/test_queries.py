"""
Test helpers and functions related to the query module
"""
from indra_network_search.data_models import NetworkSearchQuery
from indra_network_search.query import BreadthFirstSearchQuery, pass_stmt, \
    _get_edge_filter_func, EdgeFilter
from indra_network_search.tests.util import unsigned_graph


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
