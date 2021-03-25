from typing import Iterator, Tuple
from networkx import DiGraph

from indra.explanation.pathfinding import shortest_simple_paths
from indra_network_search.query import OntologyQuery, SharedRegulatorsQuery, \
    SharedTargetsQuery, ShortestSimplePathsQuery, SubgraphQuery
from indra_network_search.result_handler import OntologyResultManager, \
    SharedInteractorsResultManager, ShortestSimplePathsResultManager, \
    SubgraphResultManager,  DB_URL_HASH, DB_URL_EDGE
from indra_network_search.data_models import NetworkSearchQuery, Node, \
    SubgraphRestQuery, SubgraphResults
from indra_network_search.pathfinding import shared_parents, \
    shared_interactors, get_subgraph_edges
from . import edge_data, nodes


mock_edge_dict = {'statements': [{'stmt_hash': 31955807459270625,
                                  'stmt_type': 'Inhibition',
                                  'evidence_count': 1,
                                  'belief': 0.65,
                                  'source_counts': {'reach': 1},
                                  'english': 'AR inhibits testosterone.',
                                  'weight': 0.4307829160924542,
                                  'position': None,
                                  'curated': False,
                                  'residue': None,
                                  'initial_sign': 1}],
                  'belief': 0.9999998555477862469,
                  'weight': 1.4445222418630995515e-07}


def test_ontology_query():
    g = DiGraph()
    n1 = 'BRCA1'
    n2 = 'BRCA2'
    ns1 = 'HGNC'
    ns2 = 'HGNC'
    id1 = '1100'
    id2 = '1101'
    sd = {'statements': [{'stmt_hash': 31955807459270625,
                          'stmt_type': 'Inhibition',
                          'evidence_count': 1,
                          'belief': 0.65,
                          'source_counts': {'reach': 1},
                          'english': 'AR inhibits testosterone.',
                          'weight': 0.4307829160924542,
                          'position': None,
                          'curated': False,
                          'residue': None,
                          'initial_sign': 1}],
          'belief': 0.9999998555477862469,
          'weight': 1.4445222418630995515e-07}

    g.add_node(n1, ns=ns1, id=id1)
    g.add_node(n2, ns=ns2, id=id2)
    g.add_edge(n1, n2, **sd)

    query = NetworkSearchQuery(source=n1, target=n2)
    oq = OntologyQuery(query=query)
    oq_options = oq.run_options(graph=g)
    path_gen = shared_parents(**oq_options)
    ont_rh = OntologyResultManager(graph=g, path_generator=path_gen,
                                   source=n1, target=n2,
                                   filter_options=query.get_filter_options())
    ont_res = ont_rh.get_results()
    assert len(ont_res.parents) > 0

    # # Filter out fplx
    # query = NetworkSearchQuery(source=n1, target=n2, allowed_ns=['hgnc'])
    # oq = OntologyQuery(query=query)
    # oq_options = oq.run_options(graph=g)
    # path_gen = shared_parents(**oq_options)
    # ont_rh = OntologyResultManager(graph=g, path_generator=path_gen,
    #                                source=n1, target=n2,
    #                                filter_options=query.get_filter_options())
    # ont_res = ont_rh.get_results()
    # assert len(ont_res.parents) == 0


def _setup_query_graph() -> DiGraph:
    # Sets up shared parameters for shared_targets and shared_regulators

    # Add 4 nodes: two nodes that have two other nodes as shared up- and
    # downstream
    g = DiGraph()
    n1 = 'n1'
    n2 = 'n2'
    nsr = 'nsr'
    nst = 'nst'
    ns1, ns2, ns_sr, ns_st = ('HGNC',)*4
    id1, id2, id_sr, id_st = '1100', '1101', '1102', '1103'

    g.add_node(n1, ns=ns1, id=id1)
    g.add_node(n2, ns=ns2, id=id2)
    g.add_node(nst, ns=ns_st, id=id_st)
    g.add_node(nsr, ns=ns_sr, id=id_sr)
    g.graph['node_by_ns_id'] = {(ns, _id): n for n, ns, _id in
                                zip([n1, n2, nsr, nst],
                                    [ns1, ns2, ns_sr, ns_st],
                                    [id1, id2, id_sr, id_st])}
    sd12 = mock_edge_dict

    g.add_edge(n1, n2, **sd12)
    g.add_edge(nsr, n1, **sd12)
    g.add_edge(nsr, n2, **sd12)
    g.add_edge(n1, nst, **sd12)
    g.add_edge(n2, nst, **sd12)

    # Return graph and the instances that are shared between the two
    return g


def test_shared_targets_result_handling():
    g = _setup_query_graph()
    rest_query = NetworkSearchQuery(source='n1', target='n2',
                                    shared_regulators=False)
    st_query = SharedTargetsQuery(query=rest_query)
    st_options = st_query.run_options()
    path_gen = shared_interactors(graph=g, **st_options)
    st_rh = SharedInteractorsResultManager(
        path_generator=path_gen,
        filter_options=rest_query.get_filter_options(),
        graph=g, is_targets_query=True
    )
    st_res = st_rh.get_results()
    assert not st_res.is_empty()
    assert st_res.downstream

    # Check that target is the intended target and the same for both
    assert st_res.target_data[0].edge[1].name == 'nst'
    assert st_res.source_data[0].edge[1].name == \
           st_res.target_data[0].edge[1].name


def test_shared_regulators_result_handling():
    g = _setup_query_graph()
    rest_query = NetworkSearchQuery(source='n1', target='n2',
                                    shared_regulators=True)
    sr_query = SharedRegulatorsQuery(query=rest_query)
    sr_options = sr_query.run_options()
    path_gen = shared_interactors(graph=g, **sr_options)
    sr_rh = SharedInteractorsResultManager(
        path_generator=path_gen,
        filter_options=rest_query.get_filter_options(),
        graph=g, is_targets_query=False
    )
    sr_res = sr_rh.get_results()
    assert not sr_res.is_empty()
    assert not sr_res.downstream

    # Check that regulator is the intended regulator and the same for both
    assert sr_res.target_data[0].edge[0].name == 'nsr'
    assert sr_res.source_data[0].edge[0].name == \
           sr_res.target_data[0].edge[0].name


def test_shortest_simple_paths():
    g = DiGraph()
    for edge in edge_data:
        # Add node data
        if edge[0] not in g.nodes:
            g.add_node(edge[0], **nodes[edge[0]])
        if edge[1] not in g.nodes:
            g.add_node(edge[1], **nodes[edge[1]])

        # Add edge data
        g.add_edge(*edge, **edge_data[edge])

    query = NetworkSearchQuery(source='BRCA1', target='BRCA2')
    shortest_query = ShortestSimplePathsQuery(query)
    shortest_options = shortest_query.run_options(graph=g)
    path_gen = shortest_simple_paths(G=g, **shortest_options)
    shortest_mngr = ShortestSimplePathsResultManager(
        path_generator=path_gen, graph=g,
        filter_options=query.get_filter_options(), source='BRCA1',
        target='BRCA2')
    res = shortest_mngr.get_results()
    assert not res.is_empty(), 'Results seem empty'
    assert len(res.paths[4]) == 4, f'{len(res.paths[4])} paths found'
    # assert len(res.paths[4]) == 5, f'{len(res.paths[4])} paths found'

    # Test with culling every 3
    query_cull = NetworkSearchQuery(source='BRCA1', target='BRCA2',
                                    cull_best_node=2)
    shortest_query_cull = ShortestSimplePathsQuery(query_cull)
    shortest_options_cull = shortest_query_cull.run_options(graph=g)
    path_gen_cull = shortest_simple_paths(G=g, **shortest_options_cull)
    shortest_mngr_cull = ShortestSimplePathsResultManager(
        path_generator=path_gen_cull, graph=g,
        filter_options=query_cull.get_filter_options(), source='BRCA1',
        target='BRCA2')
    res_cull = shortest_mngr_cull.get_results()
    assert not res_cull.is_empty(), 'Results seem empty'
    assert len(res_cull.paths[4]) == 3, f'{len(res_cull.paths[4])} paths found'


def test_subgraph():
    g = _setup_query_graph()
    input_node = Node(name='n1', namespace='HGNC', identifier='1100')
    subgrap_rest_query = SubgraphRestQuery(nodes=[input_node])
    subgraph_query = SubgraphQuery(query=subgrap_rest_query)
    options = subgraph_query.run_options(graph=g)
    edge_iter: Iterator[Tuple[str, str]] = get_subgraph_edges(graph=g,
                                                              **options)

    # Should have zero results
    edges = list(edge_iter)
    assert len(edges) == 0

    # Get result manager
    res_mngr = SubgraphResultManager(path_generator=iter(edges), graph=g,
                                     **subgraph_query.result_options())
    results: SubgraphResults = res_mngr.get_results()

    # Should have zero results
    assert len(results.edges) == 0

    # Test with n1, n2
    input_nodes = [Node(name='n1', namespace='HGNC', identifier='1100'),
                   Node(name='n2', namespace='HGNC', identifier='1101')]
    subgrap_rest_query = SubgraphRestQuery(nodes=input_nodes)
    subgraph_query = SubgraphQuery(query=subgrap_rest_query)
    options = subgraph_query.run_options(graph=g)
    edge_iter = get_subgraph_edges(graph=g, **options)

    # Should have one result total: B1 -> B2
    edges = list(edge_iter)
    assert len(edges) == 1
    assert set(edges) == {('n1', 'n2')}

    # Get result manager
    res_mngr = SubgraphResultManager(path_generator=iter(edges), graph=g,
                                     **subgraph_query.result_options())
    results: SubgraphResults = res_mngr.get_results()

    # Should have one result total: B1 -> B2
    assert len(results.edges) == 1

    str_edges = {tuple([n.name for n in e.edge]) for e in results.edges}
    assert str_edges == {('n1', 'n2')}
    assert results.edges[0].weight == mock_edge_dict['weight']
    assert results.edges[0].belief == mock_edge_dict['belief']
    assert results.edges[0].db_url_edge == DB_URL_EDGE.format(
        subj_id='1100', subj_ns='HGNC', obj_id='1101', obj_ns='HGNC'
    ), results.edges[0].db_url_edge
    assert list(results.edges[0].stmts.values())[0].db_url_hash == \
           DB_URL_HASH.format(stmt_hash=mock_edge_dict['statements'][0][
               'stmt_hash']), \
           list(results.edges[0].stmts.values())[0].db_url_hash
    assert set(
        list(results.edges[0].stmts.values())[0].dict().keys()
    ).difference({'db_url_hash'}) == \
        set(mock_edge_dict['statements'][0].keys())
    assert all(mock_edge_dict['statements'][0][k] == v for k, v in
               list(results.edges[0].stmts.values())[0].dict().items() if k
               != 'db_url_hash')

    # Check that input nodes were mapped properly
    assert results.input_nodes[0].name == input_node.name
    assert results.input_nodes[0].namespace == input_node.namespace
    assert results.input_nodes[0].identifier == input_node.identifier
    assert len(results.not_in_graph) == 0
    assert results.available_nodes[0].name == 'n1'
    assert results.available_nodes[0].namespace == input_node.namespace
    assert results.available_nodes[0].identifier == input_node.identifier

    # Check correct name, missing/bad ns & id
    input_nodes = [Node(name='n1', namespace='bad ns', identifier='bad id'),
                   Node(name='n2', namespace='HGNC', identifier='1101'),
                   Node(name='nst', namespace='HGNC', identifier='1103'),
                   Node(name='nsr', namespace='HGNC', identifier='1102')]
    subgrap_rest_query = SubgraphRestQuery(nodes=input_nodes)
    subgraph_query = SubgraphQuery(query=subgrap_rest_query)
    options = subgraph_query.run_options(graph=g)
    edge_iter = get_subgraph_edges(graph=g, **options)

    # Should have five results total
    edges = list(edge_iter)
    assert len(edges) == 5
    assert set(edges) == {('nsr', 'n1'), ('nsr', 'n2'), ('n1', 'n2'),
                          ('n1', 'nst'), ('n2', 'nst')}

    # Get result manager
    res_mngr = SubgraphResultManager(path_generator=iter(edges), graph=g,
                                     **subgraph_query.result_options())
    results: SubgraphResults = res_mngr.get_results()

    # Should have five results total
    assert len(results.edges) == 5

    str_edges = {tuple([n.name for n in e.edge]) for e in results.edges}
    assert str_edges == {('nsr', 'n1'), ('nsr', 'n2'), ('n1', 'n2'),
                         ('n1', 'nst'), ('n2', 'nst')}
    assert results.edges[0].weight == mock_edge_dict['weight']
    assert results.edges[0].belief == mock_edge_dict['belief']
    assert list(results.edges[0].stmts.values())[0].db_url_hash == \
           DB_URL_HASH.format(stmt_hash=mock_edge_dict['statements'][0][
               'stmt_hash']), \
           list(results.edges[0].stmts.values())[0].db_url_hash
    assert set(
        list(results.edges[0].stmts.values())[0].dict().keys()
    ).difference({'db_url_hash'}) == \
        set(mock_edge_dict['statements'][0].keys())
    assert all(mock_edge_dict['statements'][0][k] == v for k, v in
               list(results.edges[0].stmts.values())[0].dict().items() if k
               != 'db_url_hash')

    # Check that input nodes were mapped properly
    assert results.input_nodes[0].name == input_nodes[0].name
    assert results.input_nodes[0].namespace == input_nodes[0].namespace
    assert results.input_nodes[0].identifier == input_nodes[0].identifier
    assert len(results.not_in_graph) == 0
    assert results.available_nodes[0].name == input_nodes[0].name
    assert results.available_nodes[0].namespace == 'HGNC'
    assert results.available_nodes[0].identifier == '1100'

    # Check node not in graph
    input_node = Node(name='not in graph', namespace='bad ns ',
                      identifier='bad id')
    subgrap_rest_query = SubgraphRestQuery(nodes=[input_node])
    subgraph_query = SubgraphQuery(query=subgrap_rest_query)
    options = subgraph_query.run_options(graph=g)
    edge_iter = list(get_subgraph_edges(graph=g, **options))

    assert len(edge_iter) == 0

    # Get result manager
    res_mngr = SubgraphResultManager(path_generator=edge_iter, graph=g,
                                     **subgraph_query.result_options())
    results: SubgraphResults = res_mngr.get_results()
    assert len(results.edges) == 0
    assert len(results.not_in_graph) == 1
    assert results.input_nodes[0].name == input_node.name
    assert results.input_nodes[0].namespace == input_node.namespace
    assert results.input_nodes[0].identifier == input_node.identifier
    assert results.not_in_graph[0].name == input_node.name
    assert results.not_in_graph[0].namespace == input_node.namespace
    assert results.not_in_graph[0].identifier == input_node.identifier
