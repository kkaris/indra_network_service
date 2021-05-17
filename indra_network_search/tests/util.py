from inspect import signature
from typing import Dict, Set, Callable, Optional, Union, List, Tuple, Any

from networkx import DiGraph, MultiDiGraph

from indra.assemblers.indranet.net import default_sign_dict
from indra.explanation.model_checker.model_checker import \
    signed_edges_to_signed_nodes
from indra.explanation.pathfinding import bfs_search, shortest_simple_paths, \
    open_dijkstra_search
from indra_network_search.data_models import Node, EdgeData, StmtData, Path, \
    basemodels_equal
from indra_network_search.pathfinding import shared_parents, \
    shared_interactors, get_subgraph_edges
from indra_network_search.query import MissingParametersError, \
    InvalidParametersError, Query, BreadthFirstSearchQuery, \
    ShortestSimplePathsQuery, DijkstraQuery, OntologyQuery, \
    SharedTargetsQuery, \
    SharedRegulatorsQuery, SubgraphQuery
from indra_network_search.result_handler import ResultManager, DB_URL_HASH, \
    DB_URL_EDGE
from indra_network_search.search_api import IndraNetworkSearchAPI
from indra_network_search.tests import nodes
from indra_network_search.util import get_mandatory_args


def _setup_graph() -> DiGraph:
    edge_data = _get_edge_data_dict(large=False, signed=False)
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
    edge_data = _get_edge_data_dict(large=True, signed=False)
    big_g = DiGraph()
    for edge in edge_data:
        # Add node data
        if edge[0] not in big_g.nodes:
            big_g.add_node(edge[0], **nodes[edge[0]])
        if edge[1] not in big_g.nodes:
            big_g.add_node(edge[1], **nodes[edge[1]])

        # Add edge data
        big_g.add_edge(*edge, **edge_data[edge])
    return big_g


def _setup_signed_node_graph(large: bool) -> DiGraph:
    seg = MultiDiGraph()
    dg = _setup_bigger_graph() if large else _setup_graph()
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
    return signed_edges_to_signed_nodes(graph=seg, copy_edge_data=True,
                                        prune_nodes=True)


def _setup_api(large: bool) -> IndraNetworkSearchAPI:
    g = expanded_unsigned_graph if large else unsigned_graph
    sg = exp_signed_node_graph if large else signed_node_graph
    return IndraNetworkSearchAPI(unsigned_graph=g,
                                 signed_node_graph=sg)


def _get_signed_node_edge_dict(large: bool) -> Dict:
    g = _get_graph(large=large, signed=True)
    return {edge: g.edges[edge] for edge in g.edges}


def _get_edge_data_dict(large: bool, signed: bool) -> Dict:
    if signed:
        return _get_signed_node_edge_dict(large=large)
    else:
        from . import edge_data, more_edge_data
        if large:
            return more_edge_data
        else:
            return edge_data


def _get_graph(large: bool, signed: bool) -> DiGraph:
    if signed:
        if large:
            return exp_signed_node_graph
        else:
            return signed_node_graph
    else:
        if large:
            return expanded_unsigned_graph
        else:
            return unsigned_graph


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
        all(all(basemodels_equal(s1, s2, False) for s1, s2 in
                zip(other_edge_model.statements[k], st_data_lst))
            for k, st_data_lst in edge_model.statements.items())
    return True


def _get_node(name: Union[str, Tuple[str, int]],
              graph: DiGraph) -> Optional[Node]:
    # Signed node
    if isinstance(name, tuple):
        if name in graph.nodes:
            node_name, sign = name
            return Node(name=node_name, namespace=graph.nodes[name]['ns'],
                        identifier=graph.nodes[name]['id'], sign=sign)
        else:
            pass
    # Unsigned node
    else:
        node_name = name
        if node_name in graph.nodes:
            return Node(name=node_name, namespace=graph.nodes[name]['ns'],
                        identifier=graph.nodes[name]['id'])
        else:
            pass

    raise ValueError(f'{name} not in graph')


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
        return api.shared_regulators(query, is_signed)
    elif query.alg_name == get_subgraph_edges.__name__:
        assert isinstance(query, SubgraphQuery)
        return api.subgraph_query(query)
    else:
        raise ValueError(f'Unrecognized Query class {type(query)}')


def _get_edge_data_list(edge_list: List[Tuple[Union[str, Tuple[str, int]],
                                              Union[str, Tuple[str, int]]]],
                        graph: DiGraph, large: bool, signed: bool) \
        -> List[EdgeData]:
    edges: List[EdgeData] = []
    for a, b in edge_list:
        edata = _get_edge_data(edge=(a, b), graph=graph, large=large,
                               signed=signed)
        edges.append(edata)
    return edges


def _get_edge_data(edge: Tuple[Union[str, Tuple[str, int]], ...],
                   graph: DiGraph, large: bool, signed: bool) -> EdgeData:
    edge_data = _get_edge_data_dict(large=large, signed=signed)
    ed = edge_data[edge]
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
                   graph: DiGraph, large: bool, signed: bool) -> List[Path]:
    paths: List[Path] = []
    for spath in str_paths:
        path: List[Node] = []
        for sn in spath:
            path.append(_get_node(sn, graph))
        edl: List[EdgeData] = []
        for a, b in zip(spath[:-1], spath[1:]):
            edge = (a, b)
            e_data = _get_edge_data(edge=edge, graph=graph, large=large,
                                    signed=signed)
            edl.append(e_data)
        paths.append(Path(path=path, edge_data=edl))
    return paths


unsigned_graph = _setup_graph()
expanded_unsigned_graph = _setup_bigger_graph()
signed_node_graph = _setup_signed_node_graph(False)
exp_signed_node_graph = _setup_signed_node_graph(True)
search_api = _setup_api(False)
exp_search_api = _setup_api(True)
