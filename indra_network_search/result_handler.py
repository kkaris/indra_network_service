"""Handles the aggregation of results from the IndraNetworkSearchAPI

The results handler deals with things like:
- Sorting paths
- Calculating weights
- Stopping path iteration when timeout is reached
- Keeping count of number of paths returned
- Filtering paths when it's not done in the algorithm

Todo:
 - Consider using a wrapper for checking time elapsed
"""
import logging
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
    EdgeData, StmtData, Node, FilterOptions, PathResultData, Path

__all__ = ['ResultManager', 'DijkstraResultManager',
           'ShortestSimplePathsResultManager',
           'BreadthFirstSearchResultManager',
           'SharedInteractorsResultManager', 'OntologyResultManager']


logger = logging.getLogger(__name__)


class ResultManager:
    """Applies post-search filtering and assembles edge data for paths"""
    # Todo: this class is just a parent class for results, we might also
    #  need a wrapper class that manages all the results, analogous to
    #  query vs query_handler
    alg_name: str = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterator, Iterable],
                 graph: DiGraph, filter_options: FilterOptions):
        self.path_gen: Union[Generator, Iterator, Iterable] = path_generator
        self.start_time: Optional[datetime] = None  # Start when looping paths
        self.timed_out = False
        # Remove used filters per algorithm
        self.filter_options: FilterOptions = \
            self._remove_used_filters(filter_options)
        self._graph: DiGraph = graph

    def _pass_node(self, node: Node) -> bool:
        """Pass an individual node based on node data"""
        raise NotImplementedError

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        """Pass an individual statement based statement dict content"""
        raise NotImplementedError

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        raise NotImplementedError

    def _get_node(self, node_name: str,
                  apply_filter: bool = True) -> Union[Node, None]:
        db_ns = self._graph.nodes.get(node_name, {}).get('ns')
        db_id = self._graph.nodes.get(node_name, {}).get('id')
        lookup = get_identifiers_url(db_name=db_ns, db_id=db_id) or ''
        if db_id is None or db_ns is None:
            return None
        node = Node(name=node_name, namespace=db_ns,
                    identifier=db_id, lookup=lookup)
        if not apply_filter:
            return node
        elif self.filter_options.no_node_filters() or \
                self._pass_node(node=node):
            return node

        return None

    def _get_stmt_data(self, stmt_dict: Dict[str, Union[str, int, float,
                                                        Dict[str, int]]]) -> \
            Union[StmtData, None]:
        """If statement passes filter, return StmtData model"""
        if not self.filter_options.no_stmt_filters() and \
                not self._pass_stmt(stmt_dict):
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
        # Main method for looping the path finding and results assembly
        raise NotImplementedError


class PathResultManager(ResultManager):
    """Parent class for path results

    The only thing needed in the children is defining _pass_node,
    _pass_stmt, alg_name and _remove_used_filters
    """
    alg_name = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options)

        self.paths: Dict[int, List[Path]] = {}

        # Set path source and/or target
        if not source and not target:
            raise ValueError('Must provide at least source or target for '
                             'path results')
        if source:
            self.source: Node = source if isinstance(source, Node) else \
                self._get_node(source)
        else:
            self.source = None
        if target:
            self.target: Node = target if isinstance(target, Node) else \
                self._get_node(target)
        else:
            self.target = None

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        raise NotImplementedError

    def _pass_node(self, node: Node) -> bool:
        raise NotImplementedError

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        raise NotImplementedError

    def _build_paths(self):
        paths_built = 0
        for path in self.path_gen:
            if paths_built >= self.filter_options.max_paths:
                logger.info(f'Found all {self.filter_options.max_paths} '
                            f'shortest paths')
                break
            if self.filter_options.path_length and \
                    not self.filter_options.overall_weighted:
                if len(path) < self.filter_options.path_length:
                    continue
                elif len(path) > self.filter_options.path_length:
                    logger.info(f'Found all paths of length '
                                f'{self.filter_options.path_length}')
                    break
                else:
                    pass

            # Initialize variables for this iteration
            node_path: List[Node] = []
            edge_data_list = []
            filtered_out = False  # Flag for continuing loop
            edge_data = None  # To catch cases when no paths come out

            # Loop edges of path
            for s, o in zip(path[:-1], path[1:]):
                # Get edge data: if None, edge has been filtered out,
                # break and go to next path
                edge_data = self._get_edge_data(a=s, b=o)
                if edge_data is None or edge_data.is_empty():
                    filtered_out = True
                    break

                # Build PathResultData
                edge_data_list.append(edge_data)
                node_path.append(edge_data.edge[0])

            # If inner loop was broken
            if filtered_out or edge_data is None:
                continue

            # Append final node
            node_path.append(edge_data.edge[1])
            assert len(node_path) == len(path)

            # Build data for current path
            path_data = Path(path=node_path, edge_data=edge_data_list)
            try:
                self.paths[len(path)].append(path_data)
            except KeyError:
                self.paths[len(path)] = [path_data]
            paths_built += 1

    def get_results(self) -> PathResultData:
        """Returns the result for the associated algorithm"""
        if len(self.paths) == 0:
            self._build_paths()
        return PathResultData(source=self.source, target=self.target,
                              paths=self.paths)


class DijkstraResultManager(PathResultManager):
    """Handles results from open_dijkstra_search"""
    alg_name = open_dijkstra_search.__name__

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target)

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Filters already done in algorithm
        # node_blacklist
        # terminal_ns
        return FilterOptions(**filter_options.dict(
            exclude={'node_blacklist'}, exclude_defaults=True
        ))

    def _pass_node(self, node: Node) -> bool:
        # open_dijkstra_search already checks:
        # node_blacklist
        # terminal_ns
        #
        # Still need to check:
        # allowed_ns

        if node.namespace not in self.filter_options.allowed_ns:
            return False

        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # Check:
        # - stmt_type
        # - hash_blacklist
        # - belief
        # - curated db
        # Order the checks by likelihood of being applied
        if self.filter_options.exclude_stmts and \
                stmt_dict['stmt_type'] in self.filter_options.exclude_stmts:
            return False

        if self.filter_options.belief_cutoff > 0.0 and \
                self.filter_options.belief_cutoff > stmt_dict['belief']:
            return False

        if self.filter_options.curated_db_only and not stmt_dict['curated']:
            return False

        if self.filter_options.hash_blacklist and \
                stmt_dict['stmt_hash'] in self.filter_options.hash_blacklist:
            return False

        return True


class BreadthFirstSearchResultManager(PathResultManager):
    """Handles results from bfs_search"""
    alg_name = bfs_search.__name__

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target)

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Filters already done in algorithm
        # ns filter
        # node blacklist
        # path len <-- not really though, BFS stops when paths starts to be
        #              longer than path_len, but also allows paths that are
        #              shorter
        # terminal ns <-- not in post filtering anyway
        return FilterOptions(**filter_options.dict(
            exclude={'allowed_ns', 'node_blacklist', }, exclude_defaults=True
        ))

    def _pass_node(self, node: Node) -> bool:
        # allowed_ns, node_blacklist and terminal_ns are all checked in
        # bfs_search
        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # Check:
        # - stmt_type
        # - hash_blacklist
        # - belief
        # - curated
        # Order the checks by likelihood of being applied
        if self.filter_options.exclude_stmts and \
                stmt_dict['stmt_type'] in self.filter_options.exclude_stmts:
            return False

        if self.filter_options.belief_cutoff > 0.0 and \
                self.filter_options.belief_cutoff > stmt_dict['belief']:
            return False

        if self.filter_options.curated_db_only and not stmt_dict['curated']:
            return False

        if self.filter_options.hash_blacklist and \
                stmt_dict['stmt_hash'] in self.filter_options.hash_blacklist:
            return False

        return True


class ShortestSimplePathsResultManager(PathResultManager):
    """Handles results from shortest_simple_paths"""
    alg_name = shortest_simple_paths.__name__

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target)

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Filters already done in algorithm
        #
        #
        return FilterOptions(**filter_options.dict(
            exclude={'node_blacklist'}, exclude_defaults=True
        ))

    def _pass_node(self, node: Node) -> bool:
        # Check:
        # - allowed_ns
        if node.namespace not in self.filter_options.allowed_ns:
            return False

        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # Check:
        # - stmt_type
        # - hash_blacklist
        # - belief
        # - curated
        if self.filter_options.exclude_stmts and \
                stmt_dict['stmt_type'] in self.filter_options.exclude_stmts:
            return False

        if self.filter_options.belief_cutoff > 0.0 and \
                self.filter_options.belief_cutoff > stmt_dict['belief']:
            return False

        if self.filter_options.curated_db_only and not stmt_dict['curated']:
            return False

        if self.filter_options.hash_blacklist and \
                stmt_dict['stmt_hash'] in self.filter_options.hash_blacklist:
            return False

        return True


class SharedInteractorsResultManager(ResultManager):
    """Handles results from shared_interactors, both up and downstream

    downstream is True for shared targets and False for shared regulators
    """
    alg_name: str = shared_interactors.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 filter_options: FilterOptions, graph: DiGraph,
                 is_targets_query: bool):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options)
        self._downstream: bool = is_targets_query

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # All filters are applied in algorithm
        return FilterOptions()

    def _pass_node(self, node: Node) -> bool:
        # allowed_ns, node_blacklist are both check in algorithm
        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # stmt_type, hash_blacklist, belief, curated are all checked in
        # algorithm
        return True

    def get_results(self) -> SharedInteractorsResults:
        """Get results for shared_targets and shared_regulators"""
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


class OntologyResultManager(ResultManager):
    """Handles results from shared_parents"""
    alg_name: str = shared_parents.__name__

    def __init__(self, path_generator: Union[Iterable, Iterator, Generator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str], target: Union[Node, str]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options)
        self.source: Node = source if isinstance(source, Node) else \
            self._get_node(source)
        self.target: Node = target if isinstance(target, Node) else \
            self._get_node(target)
        self._parents: List[Node] = []

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # No filters are applied
        return FilterOptions()

    def _pass_node(self, node: Node) -> bool:
        # No filters are applied
        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # No filters are applied
        return True

    def _get_parents(self):
        for name, ns, _id, id_url in self.path_gen:
            node = Node(name=name, namespace=ns, identifier=_id, lookup=id_url)
            self._parents.append(node)

    def get_results(self) -> OntologyResults:
        """Get results for shared_parents"""
        self._get_parents()
        return OntologyResults(source=self.source, target=self.target,
                               parents=self._parents)


# Map algorithm names to result classes
alg_handler_mapping = {
    shortest_simple_paths.__name__: ShortestSimplePathsResultManager,
    open_dijkstra_search.__name__: DijkstraResultManager,
    bfs_search.__name__: BreadthFirstSearchResultManager,
    'shared_targets': SharedInteractorsResultManager,
    'shared_regulators': SharedInteractorsResultManager,
    shared_parents.__name__: OntologyResultManager
}
