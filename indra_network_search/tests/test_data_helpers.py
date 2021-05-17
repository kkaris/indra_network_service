from indra_network_search.data_models import basemodels_equal, \
    basemodel_in_iterable, Node
from depmap_analysis.network_functions.famplex_functions import \
    get_identifiers_url


def test_node_equals():
    node1 = Node(name='BRCA1', namespace='HGNC', identifier='1100')
    node2 = Node(name='BRCA1', namespace='HGNC', identifier='1100', sign=0)
    node3 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name=node1.namespace,
                                            db_id=node1.identifier))

    assert basemodels_equal(basemodel=node1, other_basemodel=node2,
                            any_item=False) == False
    assert basemodels_equal(basemodel=node1, other_basemodel=node2,
                            any_item=False, exclude={'sign'})
    assert basemodels_equal(basemodel=node1, other_basemodel=node3,
                            any_item=False, exclude={'lookup'})
    assert basemodels_equal(basemodel=node2, other_basemodel=node3,
                            any_item=False, exclude={'lookup', 'sign'})


def test_node_membership():
    node1 = Node(name='BRCA1', namespace='HGNC', identifier='1100')
    node2 = Node(name='BRCA1', namespace='HGNC', identifier='1100', sign=0)
    node3 = Node(name='BRCA1', namespace='HGNC', identifier='1100',
                 lookup=get_identifiers_url(db_name=node1.namespace,
                                            db_id=node1.identifier))
    node_collection = [node2, node3]

    assert basemodel_in_iterable(
        basemodel=node1, iterable=node_collection, any_item=False) == False
    assert basemodel_in_iterable(basemodel=node1, iterable=node_collection,
                                 any_item=False, exclude={'sign'})
    assert basemodel_in_iterable(basemodel=node1, iterable=node_collection,
                                 any_item=False, exclude={'lookup'})
    assert basemodel_in_iterable(basemodel=node2, iterable=node_collection,
                                 any_item=False)
