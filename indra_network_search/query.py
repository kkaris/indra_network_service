"""
This file contains the Query classes that maps to different algorithms used
in the search api.
"""
from typing import Callable, Dict, Any, Optional, Tuple, Set, Union, List

import networkx as nx
from pydantic import BaseModel

from depmap_analysis.network_functions.net_functions import SIGNS_TO_INT_SIGN
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search, \
    open_dijkstra_search
from indra_db.client.readonly.mesh_ref_counts import get_mesh_ref_counts
from .data_models import *
from .pathfinding import *

__all__ = ['ShortestSimplePathsQuery', 'BreadthFirstSearchQuery',
           'DijkstraQuery', 'SharedTargetsQuery', 'SharedRegulatorsQuery',
           'OntologyQuery', 'Query', 'PathQuery', 'alg_func_mapping',
           'alg_name_query_mapping', 'SubgraphQuery']


class MissingParametersError(Exception):
    """Raise for missing query parameters"""


class InvalidParametersError(Exception):
    """Raise when conflicting or otherwise invalid parameters """


alg_func_mapping = {bfs_search.__name__: bfs_search,
                    shortest_simple_paths.__name__: shortest_simple_paths,
                    open_dijkstra_search.__name__: open_dijkstra_search,
                    shared_parents.__name__: shared_parents,
                    shared_interactors.__name__: shared_interactors,
                    'shared_regulators': shared_interactors,
                    'shared_targets': shared_interactors}


class Query:
    """Parent class to all Query classes

    The Query classes are helpers that make sure the methods of the
    IndraNetworkSearchAPI receive the data needed from a NetworkSearchQuery
    """
    alg_name: str = NotImplemented  # String with name of algorithm function
    options = NotImplemented  # options model

    def __init__(self, query: NetworkSearchQuery):
        self.query: NetworkSearchQuery = query
        self.query_hash: str = query.get_hash()

    def api_options(self) -> Dict[str, Any]:
        """These options are used when IndraNetworkSearchAPI handles the query

        The options here impact decisions on which extra search algorithms
        to include and which graph to pick
        """
        return ApiOptions(sign=SIGNS_TO_INT_SIGN.get(self.query.sign),
                          fplx_expand=self.query.fplx_expand,
                          user_timout=self.query.user_timeout,
                          two_way=self.query.two_way,
                          shared_regulators=self.query.shared_regulators,
                          format=self.query.format).dict()

    def alg_options(self) -> Dict[str, Any]:
        """Returns the options for the algorithm used"""
        raise NotImplementedError

    def run_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Combines all options to one dict that can be sent to algorithm"""
        raise NotImplementedError

    def result_options(self) -> Dict:
        """Provide args to corresponding result class in result_handler"""
        raise NotImplementedError


class PathQuery(Query):
    """Parent Class for ShortestSimplePaths, Dijkstra and BreadthFirstSearch"""
    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Returns the options for the algorithm used, excl mesh options"""
        raise NotImplementedError

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Return algorithm specific mesh options"""
        raise NotImplementedError

    def run_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Combines all options to one dict that can be sent to algorithm"""
        return self.options(**self.alg_options(),
                            **self.mesh_options(graph=graph)).dict()

    def result_options(self) -> Dict:
        """Provide args to corresponding result class in result_handler"""
        return {'filter_options': self.query.get_filter_options(),
                'source': self.query.source, 'target': self.query.target}

    # This method is specific for PathQuery classes
    def _get_mesh_options(self, get_func: bool = True) \
            -> Tuple[Set, Union[Callable, None]]:
        """Get the necessary mesh options"""
        if self.query.mesh_ids is None or len(self.query.mesh_ids) == 0:
            raise InvalidParametersError('No mesh ids provided, but method '
                                         'for getting mesh options was called')
        hash_mesh_dict: Dict[Any, Dict] = \
            get_mesh_ref_counts(self.query.mesh_ids)
        related_hashes: Set = set(hash_mesh_dict.keys())
        ref_counts_from_hashes = \
            _get_ref_counts_func(hash_mesh_dict) if get_func else None
        return related_hashes, ref_counts_from_hashes


class ShortestSimplePathsQuery(PathQuery):
    """Check queries that will use the shortest_simple_paths algorithm"""
    alg_name: str = shortest_simple_paths.__name__
    options: ShortestSimplePathOptions = ShortestSimplePathOptions

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Match arguments of shortest_simple_paths from query"""
        return {'source': self.query.source,
                'target': self.query.target,
                'ignore_nodes': self.query.node_blacklist,
                'weight': 'weight' if self.query.weighted else None}

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Union[Set, int, bool, Callable]]:
        """Match input to shortest_simple_paths

        Returns
        -------
        Tuple[Set, Callable]
        """
        # If any mesh ids are provided:
        if self.query.mesh_ids and len(self.query.mesh_ids) > 0:
            hashes, ref_counts_func = self._get_mesh_options()
        else:
            hashes, ref_counts_func = None, None
        return {
            'hashes': hashes,
            'ref_counts_function': ref_counts_func,
            'strict_mesh_id_filtering': self.query.strict_mesh_id_filtering,
            'const_c': self.query.const_c,
            'const_tk': self.query.const_tk
        }


class BreadthFirstSearchQuery(PathQuery):
    """Check queries that will use the bfs_search algorithm"""
    alg_name: str = bfs_search.__name__
    options: BaseModel = BreadthFirstSearchOptions

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Match arguments of bfs_search from query"""
        if self.query.source and not self.query.target:
            source_node, reverse = self.query.source, False
        elif not self.query.source and self.query.target:
            source_node, reverse = self.query.target, True
        else:
            raise InvalidParametersError(
                f'Cannot use {self.alg_name} with both source and target '
                f'set.'
            )
        depth_limit = self.query.path_length - 1 if self.query.path_length \
            else 2
        return {'source_node': source_node,
                'reverse': reverse,
                'depth_limit': depth_limit,
                'path_limit': None,  # Sets yield limit inside algorithm
                'max_per_node': self.query.max_per_node or 5,
                'node_filter': self.query.allowed_ns,
                'node_blacklist': self.query.node_blacklist,
                'terminal_ns': self.query.terminal_ns,
                'sign': SIGNS_TO_INT_SIGN.get(self.query.sign),
                'max_memory': int(2**29)}  # Currently not set in UI

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Union[Set, bool, Callable]]:
        """Match input to bfs_search"""
        # If any mesh ids are provided:
        if self.query.mesh_ids and len(self.query.mesh_ids) > 0:
            if not isinstance(graph, nx.DiGraph):
                raise InvalidParametersError(
                    f'Must provide graph when doing {self.alg_name} with '
                    f'mesh options.'
                )
            hashes, _ = self._get_mesh_options(get_func=False)
            allowed_edge = {graph.graph['edge_by_hash'][h] for h in
                            hashes if h in graph.graph['edge_by_hash']}
            def _allow_edge_func(u: Union[str, Tuple[str, int]],
                                 v: Union[str, Tuple[str, int]]):
                return (u, v) in allowed_edge
        else:
            hashes, _allow_edge_func = None, lambda u, v: True
        return {
            'hashes': hashes,
            'strict_mesh_id_filtering': self.query.strict_mesh_id_filtering,
            'allow_edge': _allow_edge_func
        }


class DijkstraQuery(PathQuery):
    """Check queries that will use the open_dijkstra_search algorithm"""
    alg_name: str = open_dijkstra_search.__name__
    options: DijkstraOptions = DijkstraOptions

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Match arguments of open_dijkstra_search from query"""
        if self.query.source and not self.query.target:
            start, reverse = self.query.source, False
        elif not self.query.source and self.query.target:
            start, reverse = self.query.target, True
        else:
            raise InvalidParametersError(
                f'Cannot use {self.alg_name} with both source and target '
                f'set.'
            )
        return {'start': start,
                'reverse': reverse,
                'path_limit': None,  # Sets yield limit inside algorithm
                'node_filter': None,  # Unused in algorithm currently
                'ignore_nodes': self.query.node_blacklist,
                'ignore_edges': None,  # Not provided as an option in UI
                'terminal_ns': self.query.terminal_ns,
                'weight': 'weight' if self.query.weighted else None}

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Union[Set, bool, Callable]]:
        """Produces mesh arguments matching open_dijkstra_search from query

        Parameters
        """
        if self.query.mesh_ids and len(self.query.mesh_ids) > 0:
            hashes, ref_counts_func = self._get_mesh_options()
        else:
            hashes, ref_counts_func = None, None
        return {'ref_counts_function': ref_counts_func,
                'hashes': hashes,
                'const_c': self.query.const_c,
                'const_tk': self.query.const_tk}


class SharedInteractorsQuery(Query):
    """Parent class for shared target and shared regulator search"""
    alg_name: str = NotImplemented
    alg_alt_name: str = shared_interactors.__name__
    options: SharedInteractorsOptions = SharedInteractorsOptions
    reverse: bool = NotImplemented

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Match arguments of shared_interactors from query"""
        return {'source': self.query.source,
                'target': self.query.target,
                'allowed_ns': self.query.allowed_ns,
                'stmt_types': self.query.stmt_filter,
                'source_filter': None,  # Not implemented in UI
                'max_results': self.query.k_shortest,
                'regulators': self.reverse,
                'sign': SIGNS_TO_INT_SIGN.get(self.query.sign),
                'hash_blacklist': self.query.edge_hash_blacklist,
                'node_blacklist': self.query.node_blacklist,
                'belief_cutoff': self.query.belief_cutoff,
                'curated_db_only': self.query.curated_db_only}

    def run_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Check query options and return them"""
        return self.options(**self.alg_options()).dict()

    def result_options(self) -> Dict:
        """Provide args to SharedInteractorsResultManager in result_handler"""
        return {'filter_options': self.query.get_filter_options(),
                'is_targets_query': not self.reverse}


class SharedRegulatorsQuery(SharedInteractorsQuery):
    """Check queries that will use shared_interactors(regulators=True)"""
    alg_name = 'shared_regulators'
    reverse = True

    def __init__(self, query: NetworkSearchQuery):
        # bool(shared_regulators) == bool(reverse)
        if query.shared_regulators != self.reverse:
            # shared regulators must not be requested if
            # query.shared_regulators == False
            raise InvalidParametersError('Request for shared regulators in '
                                         'query does not match class '
                                         'attribute reverse')

        super().__init__(query=query)


class SharedTargetsQuery(SharedInteractorsQuery):
    """Check queries that will use shared_interactors(regulators=False)"""
    alg_name = 'shared_targets'
    reverse = False


class OntologyQuery(Query):
    """Check queries that will use shared_parents"""
    alg_name = shared_parents.__name__
    options: OntologyOptions = OntologyOptions

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    @staticmethod
    def _get_ns_id(graph: nx.DiGraph, node_name: str) -> Tuple[str, str]:
        return (graph.nodes.get(node_name, {}).get('ns'),
                graph.nodes.get(node_name, {}).get('id'))

    def _get_ontology_options(self, graph: nx.DiGraph):
        source_ns, source_id = self._get_ns_id(graph=graph,
                                               node_name=self.query.source)
        target_ns, target_id = self._get_ns_id(graph=graph,
                                               node_name=self.query.target)
        return {'source_ns': source_ns, 'source_id': source_id,
                'target_ns': target_ns, 'target_id': target_id}

    def alg_options(self) -> Dict[str, Any]:
        """Match arguments of shared_parents from query"""
        return {'immediate_only': False,
                'is_a_part_of': None,
                'max_paths': self.query.k_shortest}

    def run_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Check query options and return them"""
        ontology_options: Dict[str, str] = self._get_ontology_options(graph)
        return self.options(**ontology_options,
                            **self.alg_options()).dict()

    def result_options(self) -> Dict:
        """Provide args to OntologyResultManager in result_handler"""
        return {'filter_options': self.query.get_filter_options(),
                'source': self.query.source, 'target': self.query.target}


class SubgraphQuery:
    """Check queries that gets the subgraph"""
    # todo: subclass from Query and abstract Query more. Make a new class
    #  NetworkSearchQuery as a subclass to Query, that is parent class for
    #  all queries derived from NetworkSearchQuery
    alg_name: str = get_subgraph_edges.__name__
    options: SubgraphOptions = SubgraphOptions

    def __init__(self, query: SubgraphRestQuery):
        self.query: SubgraphRestQuery = query
        self._nodes_in_graph: List[Node] = []
        self._not_in_graph: List[Node] = []

    def _check_nodes(self, graph: nx.DiGraph):
        """Filter out nodes based on their availability in graph

        1. Check if ns/id of node is in mapping: Yes: valid node, No: go to 2.
        2. If a node name is provided in node and it is in the graph, check
           the graph ns/id of the name and overwrite the ns/id of the node.
        3. If not, set node as not in graph
        """
        ns_id2node = graph.graph['node_by_ns_id']
        for node in self.query.nodes:

            # See if node is in mapping
            mapped_name = ns_id2node.get((node.namespace, node.identifier))
            if mapped_name is not None and mapped_name in graph.nodes:
                proper_node = Node(name=mapped_name,
                                   namespace=node.namespace,
                                   identifier=node.identifier)

                # Append to existing nodes
                self._nodes_in_graph.append(proper_node)

            # See if node name, if provided, is among nodes
            elif node.name and node.name in graph.nodes:
                # Check if ns/id are proper
                if node.namespace != graph.nodes[node.name]['ns'] or \
                        node.identifier != graph.nodes[node.name]['id']:
                    proper_node = Node(name=node.name,
                                       namespace=graph.nodes[node.name]['ns'],
                                       identifier=graph.nodes[node.name]['id'])
                else:
                    proper_node = node

                # Append to existing nodes
                self._nodes_in_graph.append(proper_node)

            # Append to nodes not in graph
            else:
                self._not_in_graph.append(node)

    def alg_options(self, graph: nx.DiGraph) -> Dict[str, List[Node]]:
        """Match arguments of get_subgraph_edges"""
        if not self._nodes_in_graph and not self._not_in_graph:
            self._check_nodes(graph=graph)
        return {'nodes': self._nodes_in_graph}

    def run_options(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Return options needed for get_subgraph_edges"""
        return self.options(**self.alg_options(graph)).dict()

    def result_options(self) -> Dict[str, Any]:
        """Return options needed for SubgraphResultManager

        Returns
        -------
        Dict[str, Any]
        """
        return {'filter_options': FilterOptions(),
                'original_nodes': self.query.nodes,
                'nodes_in_graph': self._nodes_in_graph,
                'not_in_graph': self._not_in_graph}


def _get_ref_counts_func(hash_mesh_dict: Dict):
    def _func(graph: nx.DiGraph, u: str, v: str):
        # Get hashes for edge
        hashes = [d['stmt_hash'] for d in graph[u][v]['statements']]

        # Get all relevant mesh counts
        dicts: List[Dict] = [hash_mesh_dict.get(h, {'': 0, 'total': 1})
                             for h in hashes]

        # Count references
        ref_counts: int = sum(sum(v for k, v in d.items() if k != 'total')
                              for d in dicts)
        total: int = sum(d['total'] for d in dicts) or 1
        return ref_counts, total
    return _func


alg_name_query_mapping = {
    bfs_search.__name__: BreadthFirstSearchQuery,
    shortest_simple_paths.__name__: ShortestSimplePathsQuery,
    open_dijkstra_search.__name__: DijkstraQuery,
    shared_parents.__name__: OntologyQuery,
    'shared_regulators': SharedRegulatorsQuery,
    'shared_targets': SharedTargetsQuery}
