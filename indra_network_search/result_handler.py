"""Handles the aggregation of results from the IndraNetworkSearchAPI

The results handler deals with things like:
- Sorting paths
- Calculating weights
- Stopping path iteration when timeout is reached
- Keeping count of number of paths returned
- Filtering paths when it's not done in the algorithm

Todo: consider using a wrapper for checking time elapsed
"""
from datetime import datetime
from typing import Generator, Union, List, Optional, Iterator, Iterable, \
    Dict, Any

from networkx import DiGraph

from depmap_analysis.network_functions.famplex_functions import \
    get_identifiers_url
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search, \
    open_dijkstra_search
from .pathfinding import *
from .data_models import OntologyResults, SharedInteractorsResults, \
    EdgeData, StmtData, Node, FilterOptions

__all__ = ['ResultHandler', 'Dijkstra', 'ShortestSimplePaths',
           'BreadthFirstSearch', 'SharedInteractors', 'Ontology']


class ResultHandler:
    """Applies post-search filtering and assembles edge data for paths"""
    alg_name: str = NotImplemented

    def __init__(self, path_generator: Generator, graph: DiGraph,
                 filter_options: FilterOptions, max_paths: int = 50):
        self.path_gen: Generator = path_generator
        self.start_time: Optional[datetime] = None  # Start when looping paths
        self.max_paths: int = max_paths
        self.timed_out = False
        self.filter_options: FilterOptions = filter_options
        self._graph: DiGraph = graph

    def _pass_node(self, node: Node) -> bool:
        if self.filter_options.no_node_filters():
            return True

        # Check allowed namespaces
        if len(self.filter_options.allowed_ns) > 0 and \
                node.namespace.lower() not in self.filter_options.allowed_ns:
            return False

        # Check node blacklist
        if self.filter_options.node_blacklist and \
                node.name.lower() in self.filter_options.node_blacklist:
            return False

        return True

    def _pass_stmts(self,
                    stmt_dict: Dict[str, Union[str, int, float,
                                               Dict[str, int]]]) -> bool:
        if self.filter_options.no_stmt_filters():
            return True

        # Check stmt types
        if stmt_dict['stmt_type'] in self.filter_options.exclude_stmts:
            return False

        # Check curated db
        if self.filter_options.curated_db_only and \
                stmt_dict['curated'] is False:
            return False

        # Check belief
        if stmt_dict['belief'] < self.filter_options.belief_cutoff:
            return False

        # Check hashes
        if stmt_dict['stmt_hash'] in self.filter_options.hash_blacklist:
            return False

        return True

    def _get_node(self, node_name: str) -> Union[Node, None]:
        db_ns = self._graph.nodes.get(node_name, {}).get('ns')
        db_id = self._graph.nodes.get(node_name, {}).get('id')
        lookup = get_identifiers_url(db_name=db_ns, db_id=db_id) or ''
        if db_id is None and db_ns is None:
            return None
        return Node(name=node_name, namespace=db_ns,
                    identifier=db_id, lookup=lookup)

    def _get_stmt_data(self, stmt_dict: Dict[str, Union[str, int, float,
                                                        Dict[str, int]]]) -> \
            Union[StmtData, None]:
        if not self._pass_stmts(stmt_dict):
            return None

        return StmtData(**stmt_dict)

    def _get_edge_data(self, a: Union[str, Node], b: Union[str, Node]) -> \
            Union[EdgeData, None]:
        a_node = a if isinstance(a, Node) else self._get_node(a)
        b_node = b if isinstance(b, Node) else self._get_node(b)
        edge = (a_node, b_node)
        ed: Dict[str, Any] = self._graph.edges[(a_node.name, b_node.name)]
        stmt_dict: Dict[str, List[StmtData]] = {}
        for sd in ed['statements']:
            stmt_data = self._get_stmt_data(stmt_dict=sd)
            if stmt_data:
                try:
                    stmt_dict[stmt_data.stmt_type].append(stmt_data)
                except KeyError:
                    stmt_dict[stmt_data.stmt_type] = [stmt_data]

        # If all support was filtered out
        if not stmt_dict:
            return None

        edge_belief = ed['belief']
        edge_weight = ed['weight']

        # FixMe: assume signed paths are (node, sign) tuples, and translate
        #  sign from there
        # sign = ed.get('sign')
        context_weight = ed.get('context_weight')
        if context_weight:
            ct_dict = {'context_weight': context_weight}
        else:
            ct_dict = {}

        return EdgeData(edge=edge, stmts=stmt_dict, belief=edge_belief,
                        weight=edge_weight, **ct_dict)

    def get_results(self):
        """Loops out and builds results from the paths from the generator"""
        # Main method for executing the path finding and results assembly
        raise NotImplementedError


class PathResultsHandler(ResultHandler):
    """Parent class for path results"""
    alg_name = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 max_paths: int):
        super().__init__(path_generator=path_generator, max_paths=max_paths)
        self.paths: List = []

    def get_results(self):
        raise NotImplementedError


class Dijkstra(PathResultsHandler):
    """Handles results from open_dijkstra_search"""
    alg_name = open_dijkstra_search.__name__


class BreadthFirstSearch(PathResultsHandler):
    """Handles results from bfs_search"""
    alg_name = bfs_search.__name__


class ShortestSimplePaths(PathResultsHandler):
    """Handles results from shortest_simple_paths"""
    alg_name = shortest_simple_paths.__name__


class SharedInteractors(ResultHandler):
    """Handles results from shared_interactors, both up and downstream

    downstream is True for shared targets and False for shared regulators
    """
    alg_name: str = shared_interactors.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 filter_options: FilterOptions, graph: DiGraph,
                 is_targets_query: bool, max_paths: int = 50):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, max_paths=max_paths)
        self._downstream: bool = is_targets_query

    def get_results(self) -> SharedInteractorsResults:
        source_edges: List[EdgeData] = []
        target_edges: List[EdgeData] = []
        for (s1, s2), (t1, t2) in self.path_gen:
            source_edge = self._get_edge_data(a=s1, b=s2)
            target_edge = self._get_edge_data(a=t1, b=t2)
            if source_edge and target_edge:
                source_edges.append(source_edge)
                target_edges.append(target_edge)

        return SharedInteractorsResults(source_data=source_edges,
                                        target_data=target_edges,
                                        downstream=self._downstream)


class Ontology(ResultHandler):
    """Handles results from shared_parents"""
    alg_name: str = shared_parents.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str],
                 max_paths: int = 50):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, max_paths=max_paths)
        self.source: Node = source if isinstance(source, Node) else \
            self._get_node(source)
        self.target: Node = target if isinstance(target, Node) else \
            self._get_node(target)
        self._parents: List[Node] = []

    def _get_parents(self):
        for name, ns, _id, idurl in self.path_gen:
            node = Node(name=name, namespace=ns, identifier=_id, lookup=idurl)
            if self._pass_node(node):
                self._parents.append(node)

            if len(self._parents) >= self.max_paths:
                break

    def get_results(self) -> OntologyResults:
        """Get results for shared_parents"""
        self._get_parents()
        return OntologyResults(source=self.source, target=self.target,
                               parents=self._parents)


# Map result algorithm names to result handlers
alg_handler_mapping = {
    shortest_simple_paths.__name__: ShortestSimplePaths,
    open_dijkstra_search.__name__: Dijkstra,
    bfs_search.__name__: BreadthFirstSearch,
    'shared_targets': SharedInteractors,
    'shared_regulators': SharedInteractors,
    shared_parents.__name__: Ontology
}
