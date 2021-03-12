from networkx import DiGraph

from indra_network_search.query import OntologyQuery
from indra_network_search.result_handler import Ontology
from indra_network_search.data_models import NetworkSearchQuery
from indra_network_search.pathfinding import shared_parents


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
