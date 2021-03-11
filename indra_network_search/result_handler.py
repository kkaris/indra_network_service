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
from networkx import DiGraph, MultiDiGraph
from typing import Generator, Union, Dict, List, Optional, Iterator, Iterable
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search,\
    open_dijkstra_search
from .pathfinding import *
from .data_models import OntologyResults, Node, StmtData, EdgeData, Path, \
    PathResults, SharedInteractorsResults, Results, NetworkSearchQuery


__all__ = ['ResultHandler', 'Dijkstra', 'ShortestSimplePaths',
           'BreadthFirstSearch']


class ResultHandler:
    """Applies post-search filtering and assembles edge data for paths"""
    alg_name: str = NotImplemented

    def __init__(self, path_generator: Generator,
                 graph: Union[DiGraph, MultiDiGraph],
                 query: NetworkSearchQuery,
                 max_paths: int = 50):
        self.path_gen: Generator = path_generator
        self.graph: Union[DiGraph, MultiDiGraph] = graph
        self.query: NetworkSearchQuery = query
        self.start_time: Optional[datetime] = None  # Set when starting to
        # loop paths
        self.max_paths: int = max_paths
        self.timed_out = False

    def get_node(self, node: str) -> Node:
        """Get a Node model given a node name"""
        return Node(name=node,
                    namespace=self.graph.nodes[node]['ns'],
                    identifier=self.graph.nodes[node]['id'])

    def _filter_results(self):
        pass

    def _build_result_data(self):
        # loop the generator and fill in paths list and edge data dictionary
        pass

    def get_results(self):
        """Loops out and builds results from the paths from the generator"""
        # Main method for executing the path finding and results assembly
        raise NotImplementedError


class PathResultsHandler(ResultHandler):
    """Parent class for path results"""
    alg_name = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: Union[DiGraph, MultiDiGraph],
                 query: NetworkSearchQuery, max_paths: int):
        super().__init__(path_generator=path_generator, graph=graph,
                         query=query, max_paths=max_paths)
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
    """Handles results from shared_interactors, both up and downstream"""
    alg_name = shared_interactors


class Ontology(ResultHandler):
    """Handles results from shared_parents"""
    alg_name = shared_parents.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 graph: Union[DiGraph, MultiDiGraph],
                 query: NetworkSearchQuery, max_paths: int = 50):
        super().__init__(path_generator=path_generator, graph=graph,
                         query=query, max_paths=max_paths)
        self._parents: Optional[List[Node]] = None

    def _get_parents(self):
        for ns, _id, idurl in self.path_gen:
            # Todo get name and use instead of identifier
            self._parents.append(Node(name=_id, namespace=ns,
                                      identifier=_id, lookup=idurl))

    def get_results(self) -> OntologyResults:
        """Get results for shared_parents"""
        self._get_parents()
        source_node: Node = self.get_node(self.query.source)
        target_node: Node = self.get_node(self.query.target)
        return OntologyResults(source=source_node, target=target_node,
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
