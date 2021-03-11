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
from typing import Generator, Union, List, Optional, Iterator, Iterable

from indra.explanation.pathfinding import shortest_simple_paths, bfs_search, \
    open_dijkstra_search
from .pathfinding import *
from .data_models import OntologyResults, Node

__all__ = ['ResultHandler', 'Dijkstra', 'ShortestSimplePaths',
           'BreadthFirstSearch']


class ResultHandler:
    """Applies post-search filtering and assembles edge data for paths"""
    alg_name: str = NotImplemented

    def __init__(self, path_generator: Generator,
                 max_paths: int = 50):
        self.path_gen: Generator = path_generator
        self.start_time: Optional[datetime] = None  # Set when starting to
        # loop paths
        self.max_paths: int = max_paths
        self.timed_out = False

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
    """Handles results from shared_interactors, both up and downstream"""
    alg_name = shared_interactors


class Ontology(ResultHandler):
    """Handles results from shared_parents"""
    alg_name = shared_parents.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 source: Node, target: Node, max_paths: int = 50):
        super().__init__(path_generator=path_generator, max_paths=max_paths)
        self.source: Node = source
        self.target: Node = target
        self._parents: List[Node] = []

    def _get_parents(self):
        for name, ns, _id, idurl in self.path_gen:
            self._parents.append(Node(name=name, namespace=ns,
                                      identifier=_id, lookup=idurl))

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
