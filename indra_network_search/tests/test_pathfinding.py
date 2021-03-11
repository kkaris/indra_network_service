from depmap_analysis.tests import *
from indra_network_search.pathfinding import *


def test_shared_parents():
    ns1 = 'HGNC'
    ns2 = 'HGNC'
    id1 = '1100'
    id2 = '1101'
    res = shared_parents(source_ns=ns1, target_ns=ns2, source_id=id1,
                         target_id=id2)
    short_res = [(ns, _id) for _, ns, _id, _ in res]
    assert ('FPLX', 'BRCA') in short_res
    assert ('FPLX', 'FANC') in short_res


def test_shared_targets():
    idg = get_dg()
    source = 'X1'
    target = 'X2'
    shared_target = 'Z1'

    res = shared_interactors(graph=idg, source=source, target=target,
                             regulators=False)
    res_list = [t for t in res]
    assert ([source, shared_target], [target, shared_target]) in res_list


def test_shared_regulators():
    idg = get_dg()
    source = 'X1'
    target = 'X2'
    shared_regulator = 'Z2'

    res = shared_interactors(graph=idg, source=source, target=target,
                             regulators=True)
    res_list = [t for t in res]
    assert ([shared_regulator, source], [shared_regulator, target]) in res_list
