from networkx import DiGraph

from indra_network_search.query import OntologyQuery, SharedRegulatorsQuery, \
    SharedTargetsQuery
from indra_network_search.result_handler import Ontology, SharedInteractors
from indra_network_search.data_models import NetworkSearchQuery
from indra_network_search.pathfinding import shared_parents, shared_interactors


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
    ont_rh = Ontology(graph=g, path_generator=path_gen, source=n1, target=n2,
                      filter_options=query.get_filter_options())
    ont_res = ont_rh.get_results()
    assert len(ont_res.parents) > 0

    # Filter out fplx
    query = NetworkSearchQuery(source=n1, target=n2, allowed_ns=['hgnc'])
    oq = OntologyQuery(query=query)
    oq_options = oq.run_options(graph=g)
    path_gen = shared_parents(**oq_options)
    ont_rh = Ontology(graph=g, path_generator=path_gen, source=n1, target=n2,
                      filter_options=query.get_filter_options())
    ont_res = ont_rh.get_results()
    assert len(ont_res.parents) == 0


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
    sd12 = {'statements': [{'stmt_hash': 31955807459270625,
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
    g.add_node(nst, ns=ns_st, id=id_st)
    g.add_node(nsr, ns=ns_sr, id=id_sr)

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
    st_rh = SharedInteractors(path_generator=path_gen,
                              filter_options=rest_query.get_filter_options(),
                              graph=g, is_targets_query=True)
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
    sr_rh = SharedInteractors(path_generator=path_gen,
                              filter_options=rest_query.get_filter_options(),
                              graph=g, is_targets_query=False)
    sr_res = sr_rh.get_results()
    assert not sr_res.is_empty()
    assert not sr_res.downstream

    # Check that regulator is the intended regulator and the same for both
    assert sr_res.target_data[0].edge[0].name == 'nsr'
    assert sr_res.source_data[0].edge[0].name == \
           sr_res.target_data[0].edge[0].name
