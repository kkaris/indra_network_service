"""Handles the aggregation of results from the IndraNetworkSearchAPI

The results handler deals with things like:
- Sorting paths
- Calculating weights
- Stopping path iteration when timeout is reached
- Keeping count of number of paths returned
- Filtering paths when it's not done in the algorithm

"""
import logging
from datetime import datetime, timedelta
from typing import Generator, Union, List, Optional, Iterator, Iterable, \
    Dict, Any, Set, Tuple

from networkx import DiGraph

from depmap_analysis.network_functions.famplex_functions import \
    get_identifiers_url
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search, \
    open_dijkstra_search
from pydantic import ValidationError
from .util import StrNode
from .pathfinding import *
from .data_models import OntologyResults, SharedInteractorsResults, \
    EdgeData, StmtData, Node, FilterOptions, PathResultData, Path, \
    EdgeDataByHash, SubgraphResults, DEFAULT_TIMEOUT

__all__ = ['ResultManager', 'DijkstraResultManager',
           'ShortestSimplePathsResultManager',
           'BreadthFirstSearchResultManager',
           'SharedInteractorsResultManager', 'OntologyResultManager',
           'SubgraphResultManager', 'alg_manager_mapping']


logger = logging.getLogger(__name__)


DB_URL_HASH = 'https://db.indra.bio/statements/from_hash/' \
              '{stmt_hash}?format=html'
DB_URL_EDGE = 'https://db.indra.bio/statements/from_agents?subject=' \
              '{subj_id}@{subj_ns}&object={obj_id}@{obj_ns}&format=html'


class ResultManager:
    """Applies post-search filtering and assembles edge data for paths"""
    # Todo: this class is just a parent class for results, we might also
    #  need a wrapper class that manages all the results, analogous to
    #  query vs query_handler
    alg_name: str = NotImplemented
    filter_input_node: bool = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterator, Iterable],
                 graph: DiGraph, filter_options: FilterOptions,
                 input_nodes: List[Union[StrNode, Node]],
                 timeout: Optional[float] = DEFAULT_TIMEOUT):
        self.path_gen: Union[Generator, Iterator, Iterable] = path_generator
        self.start_time: Optional[datetime] = None  # Start when looping paths
        self.timeout = timeout
        self.timed_out = False
        # Remove used filters per algorithm
        self.filter_options: FilterOptions = \
            self._remove_used_filters(filter_options)
        self._graph: DiGraph = graph
        self.input_nodes: List[Union[StrNode, Node]] = input_nodes

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

    def _get_node(self, node_name: Union[str, Tuple[str, int]],
                  apply_filter: bool = True) -> Optional[Node]:
        # Check if node is signed
        if isinstance(node_name, tuple):
            name, sign = node_name
            node_info = {'name': name, 'sign': sign}
        else:
            name, sign = node_name, None
            node_info = {'name': name}

        # Check if node exists in graph
        db_ns = self._graph.nodes.get(node_name, {}).get('ns')
        db_id = self._graph.nodes.get(node_name, {}).get('id')
        if db_id is None or db_ns is None:
            return None

        # Add ns/id to data
        node_info['namespace'] = db_ns
        node_info['identifier'] = db_id

        # Create Node
        node = Node(**node_info)

        # Check if we need to filter node
        if not apply_filter:
            lookup = get_identifiers_url(db_name=db_ns, db_id=db_id) or ''
            node.lookup = lookup
            return node
        # Apply filters if there are any
        elif self.filter_options.no_node_filters() or \
                self._pass_node(node=node):
            lookup = get_identifiers_url(db_name=db_ns, db_id=db_id) or ''
            node.lookup = lookup
            return node

        return None

    def _get_stmt_data(self, stmt_dict: Dict[str, Union[str, int, float,
                                                        Dict[str, int]]]) -> \
            Union[StmtData, None]:
        """If statement passes filter, return StmtData model"""
        if not self.filter_options.no_stmt_filters() and \
                not self._pass_stmt(stmt_dict):
            return None

        try:
            url = DB_URL_HASH.format(stmt_hash=stmt_dict['stmt_hash'])
            return StmtData(db_url_hash=url, **stmt_dict)
        except ValidationError as err:
            logger.warning(
                f'Validation of statement data failed for '
                f'"{stmt_dict.get("english", "(unknown statement)")}" with '
                f'hash {stmt_dict.get("stmt_hash", "(unknown hash)")}:'
                f' {str(err)}'
            )
            return None

    def _get_edge_data(self,
                       a: Union[str, Tuple[str, int], Node],
                       b: Union[str, Tuple[str, int], Node]) \
            -> Union[EdgeData, None]:
        a_node = a if isinstance(a, Node) else self._get_node(a)
        b_node = b if isinstance(b, Node) else self._get_node(b)
        if a_node is None or b_node is None:
            return None
        edge = [a_node, b_node]
        str_edge = (a_node.name, b_node.name) if a_node.sign is None else \
            (a_node.signed_node_tuple(), b_node.signed_node_tuple())
        ed: Dict[str, Any] = self._graph.edges[str_edge]
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

        # Get sign and context weight if present
        extra_dict = {}
        if a_node.sign is not None and b_node.sign is not None:
            sign = 1 if a_node.sign != b_node.sign else 0
            extra_dict['sign'] = sign
        if ed.get('context_weight'):
            extra_dict['context_weight'] = ed['context_weight']

        url: str = DB_URL_EDGE.format(subj_id=a_node.identifier,
                                      subj_ns=a_node.namespace,
                                      obj_id=b_node.identifier,
                                      obj_ns=b_node.namespace)
        return EdgeData(edge=edge, statements=stmt_dict, belief=edge_belief,
                        weight=edge_weight, db_url_edge=url, **extra_dict)

    def _get_results(self):
        # Main method for looping the path finding and results assembly
        raise NotImplementedError

    def get_results(self):
        """Loops out and builds results from the paths from the generator"""
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        return self._get_results()


class PathResultManager(ResultManager):
    """Parent class for path results

    The only thing needed in the children is defining _pass_node,
    _pass_stmt, alg_name and _remove_used_filters
    """
    alg_name = NotImplemented

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str, Tuple[str, int]],
                 target: Union[Node, str, Tuple[str, int]], reverse: bool):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options)

        self.paths: Dict[int, List[Path]] = {}
        self.reverse: bool = reverse

        # Set path source and/or target
        if not source and not target:
            raise ValueError('Must provide at least source or target for '
                             'path results')
        if source:
            self.source: Node = source if isinstance(source, Node) else \
                self._get_node(source, apply_filter=False)
        else:
            self.source = None
        if target:
            self.target: Node = target if isinstance(target, Node) else \
                self._get_node(target, apply_filter=False)
        else:
            self.target = None

        if self.source is None and self.target is None:
            raise ValueError(f'Failed to set source ({source}) and/or target '
                             f'({target})')

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
        prev_path: Optional[List[str]] = None
        culled_nodes: Set[str] = set()
        if self.filter_options.context_weighted:
            weight = 'context_weight'
        elif self.filter_options.weighted:
            weight = 'weight'
        else:
            weight = None

        while True:
            if self.timeout and datetime.utcnow() - self.start_time > \
                    timedelta(seconds=self.timeout):
                logger.info(f'Timeout reached ({self.timeout} seconds), '
                            f'breaking results loop')
                self.timed_out = True
                break
            if paths_built >= self.filter_options.max_paths:
                logger.info(f'Found all {self.filter_options.max_paths} '
                            f'shortest paths')
                break

            try:
                if self.filter_options.cull_best_node is not None and \
                        prev_path is not None:
                    send_values = _get_cull_values(
                        culled_nodes=culled_nodes,
                        cull_best_node=self.filter_options.cull_best_node,
                        prev_path=prev_path,
                        added_paths=paths_built,
                        graph=self._graph,
                        weight=weight
                    )
                    # Send value affects current yield value, not next one:
                    # See https://stackoverflow.com/a/12638313/10478812
                    path = self.path_gen.send(send_values)
                else:
                    path = next(self.path_gen)

                # Reverse path if it is reversed, e.g. upstream open search
                if self.reverse:
                    path = path[::-1]

            except StopIteration:
                logger.info('Reached StopIteration in PathResultsManager, '
                            'breaking.')
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
                # Add subject node of edge
                node_path.append(edge_data.edge[0])

            # If inner loop was broken or never run
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
            prev_path = path

    def _get_results(self) -> PathResultData:
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
                 source: Union[Node, str, Tuple[str, int]],
                 target: Union[Node, str, Tuple[str, int]], reverse: bool):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target, reverse=reverse)

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Filters already done in algorithm
        # node_blacklist
        # terminal_ns <- Not part of FilterOptions currently
        # cull best nodes <- Not applicable
        return FilterOptions(**filter_options.dict(
            exclude={'node_blacklist', 'cull_best_node'},
            exclude_defaults=True
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
                 source: Union[Node, str, Tuple[str, int]],
                 target: Union[Node, str, Tuple[str, int]], reverse: bool):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target, reverse=reverse)

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Filters already done in algorithm
        # Node filters:
        # ns filter
        # node blacklist
        # path len <-- not really though, BFS stops when paths starts to be
        #              longer than path_len, but also allows paths that are
        #              shorter
        # terminal ns <-- not in post filtering anyway
        #
        # Edge filters:
        # exclude_stmts ('stmt_filter' NetworkSearchQuery)
        # hash_blacklist ('edge_hash_blacklist'  NetworkSearchQuery)
        # belief_cutoff
        # curated_db_only
        return FilterOptions(**filter_options.dict(
            exclude={'allowed_ns', 'node_blacklist', 'exclude_stmts',
                     'hash_blacklist', 'belief_cutoff', 'curated_db_only'},
            exclude_defaults=True
        ))

    def _pass_node(self, node: Node) -> bool:
        # allowed_ns, node_blacklist and terminal_ns are all checked in
        # bfs_search
        return True

    def _pass_stmt(self,
                   stmt_dict: Dict[str, Union[str, int, float,
                                              Dict[str, int]]]) -> bool:
        # stmt_type, hash_blacklist, belief, curated already applied in
        # bfs_search
        return True


class ShortestSimplePathsResultManager(PathResultManager):
    """Handles results from shortest_simple_paths"""
    alg_name = shortest_simple_paths.__name__

    def __init__(self, path_generator: Union[Generator, Iterable, Iterator],
                 graph: DiGraph, filter_options: FilterOptions,
                 source: Union[Node, str, Tuple[str, int]],
                 target: Union[Node, str, Tuple[str, int]], reverse: bool):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options, source=source,
                         target=target, reverse=reverse)

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

    def _get_results(self) -> SharedInteractorsResults:
        """Get results for shared_targets and shared_regulators"""
        source_edges: List[EdgeData] = []
        target_edges: List[EdgeData] = []
        for (s1, s2), (t1, t2) in self.path_gen:
            if self.timeout and datetime.utcnow() - self.start_time > \
                    timedelta(seconds=self.timeout):
                logger.info(f'Timeout reached ({self.timeout} seconds), '
                            f'breaking results loop')
                self.timed_out = True
                break
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
                 source: Union[Node, str, Tuple[str, int]],
                 target: Union[Node, str, Tuple[str, int]]):
        super().__init__(path_generator=path_generator, graph=graph,
                         filter_options=filter_options)
        self.source: Node = source if isinstance(source, Node) else \
            self._get_node(source, apply_filter=False)
        self.target: Node = target if isinstance(target, Node) else \
            self._get_node(target, apply_filter=False)
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
            if self.timeout and datetime.utcnow() - self.start_time > \
                    timedelta(seconds=self.timeout):
                logger.info(f'Timeout reached ({self.timeout} seconds), '
                            f'breaking results loop')
                self.timed_out = True
                break
            node = Node(name=name, namespace=ns, identifier=_id, lookup=id_url)
            self._parents.append(node)

    def _get_results(self) -> OntologyResults:
        """Get results for shared_parents"""
        self._get_parents()
        return OntologyResults(source=self.source, target=self.target,
                               parents=self._parents)


def _get_cull_values(culled_nodes: Set[str],
                     cull_best_node: int,
                     prev_path: List[str],
                     added_paths: int,
                     graph: DiGraph,
                     weight: Optional[str] = None) \
        -> Tuple[Set[str], Set[str]]:
    if added_paths >= cull_best_node and \
            added_paths % cull_best_node == 0 and \
            prev_path is not None and len(prev_path) >= 3:
        degrees = graph.degree(prev_path[1:-1], weight)
        highest_degree_node = max(degrees, key=lambda x: x[1])[0]
        culled_nodes.add(highest_degree_node)

    return culled_nodes, set()


class SubgraphResultManager(ResultManager):
    """Handles results from get_subgraph_edges"""
    alg_name = get_subgraph_edges.__name__

    def __init__(self, path_generator: Iterator[Tuple[str, str]],
                 graph: DiGraph,
                 filter_options: FilterOptions, original_nodes: List[Node],
                 nodes_in_graph: List[Node], not_in_graph: List[Node]):
        super().__init__(path_generator=path_generator,
                         graph=graph, filter_options=filter_options)
        self.edge_dict: Dict[Tuple[str, str], EdgeDataByHash] = {}
        self._orignal_nodes: List[Node] = original_nodes
        self._available_nodes: Dict[str, Node] = {n.name: n for n
                                                  in nodes_in_graph}
        self._not_in_graph: List[Node] = not_in_graph

    def _pass_node(self, node: Node) -> bool:
        # No filters implemented yet
        return True

    def _pass_stmt(self, stmt_dict: Dict[str, Union[str, int, float,
                                                    Dict[str, int]]]) -> bool:
        # Check:
        # - stmt_type
        if self.filter_options.exclude_stmts and \
                stmt_dict['stmt_type'] in self.filter_options.exclude_stmts:
            return False

        return True

    @staticmethod
    def _remove_used_filters(filter_options: FilterOptions) -> FilterOptions:
        # Hard code removal of stmt type 'fplx'
        return FilterOptions(exclude_stmts=['fplx'])

    def _get_edge_data_by_hash(self, a: Union[str, Node], b: Union[str, Node])\
            -> Union[EdgeDataByHash, None]:
        # Get node, return if unidentifiable
        a_node = a if isinstance(a, Node) else self._get_node(a)
        b_node = b if isinstance(b, Node) else self._get_node(b)
        if a_node is None or b_node is None:
            return None

        # Add lookup if not present
        if not a_node.lookup:
            a_node.lookup = get_identifiers_url(a_node.namespace,
                                                a_node.identifier)
        if not b_node.lookup:
            b_node.lookup = get_identifiers_url(b_node.namespace,
                                                b_node.identifier)

        # Get stmt data for edge
        edge = [a_node, b_node]
        ed: Dict[str, Any] = self._graph.edges[(a_node.name, b_node.name)]
        stmt_dict: Dict[int, StmtData] = {}  # Collect stmt_data by hash
        for sd in ed['statements']:
            stmt_data = self._get_stmt_data(stmt_dict=sd)
            if stmt_data and stmt_data.stmt_hash not in stmt_dict:
                stmt_dict[stmt_data.stmt_hash] = stmt_data

        # If all support was filtered out
        if not stmt_dict:
            return None

        # Get edge aggregated belief, weight
        edge_belief = ed['belief']
        edge_weight = ed['weight']

        return EdgeDataByHash(
            edge=edge, stmts=stmt_dict, belief=edge_belief, weight=edge_weight,
            db_url_edge=DB_URL_EDGE.format(subj_id=a_node.identifier,
                                           subj_ns=a_node.namespace,
                                           obj_id=b_node.identifier,
                                           obj_ns=b_node.namespace)
        )

    def _fill_data(self):
        """Build EdgeDataByHash for all edges, without duplicates"""
        logger.info(f'Generating output data for subgraph with '
                    f'{len(self._available_nodes)} eligible nodes')
        # Loop edges
        for a, b in self.path_gen:
            if self.timeout and datetime.utcnow() - self.start_time > \
                    timedelta(seconds=self.timeout):
                logger.info(f'Timeout reached ({self.timeout} seconds), '
                            f'breaking results loop')
                self.timed_out = True
                break
            if self.timeout and datetime.utcnow() - self.start_time > \
                    timedelta(seconds=self.timeout):
                logger.info(f'Timeout reached ({self.timeout} seconds), '
                            f'breaking results loop')
                self.timed_out = True
                break
            edge: Tuple[str, str] = (a, b)
            if edge not in self.edge_dict:
                half_edge = (self._available_nodes[a]
                             if a in self._available_nodes else a,
                             self._available_nodes[b]
                             if b in self._available_nodes else b)
                edge_data: EdgeDataByHash = \
                    self._get_edge_data_by_hash(*half_edge)
                if edge_data:
                    self.edge_dict[edge] = edge_data

    def _get_results(self) -> SubgraphResults:
        """Get results for get_subgraph_edges"""
        if not self.edge_dict and len(self._available_nodes) > 0:
            self._fill_data()
        edges: List[EdgeDataByHash] = list(self.edge_dict.values())

        return SubgraphResults(
            available_nodes=list(self._available_nodes.values()),
            edges=edges, input_nodes=self._orignal_nodes,
            not_in_graph=self._not_in_graph
        )


# Map algorithm names to result classes
alg_manager_mapping = {
    shortest_simple_paths.__name__: ShortestSimplePathsResultManager,
    open_dijkstra_search.__name__: DijkstraResultManager,
    bfs_search.__name__: BreadthFirstSearchResultManager,
    'shared_targets': SharedInteractorsResultManager,
    'shared_regulators': SharedInteractorsResultManager,
    shared_parents.__name__: OntologyResultManager,
    get_subgraph_edges.__name__: SubgraphResultManager
}
