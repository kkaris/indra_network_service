"""
This file contains data models for queries, results and arguments to algorithm
functions.

todo:
 - Use constr(to_lower=True) in appropriate places to enforce lowercase:
    + node_blacklist
    + allowed_ns
    + stmt_filter (excluded statement types)
 - Figure out how to use conlist and other con* enforcers for e.g.:
    + Enfore hashes to be int and/or str
 - In FilterOptions, set overall weighted based on values of weighted
   context weighted. See here for more info:
   https://stackoverflow.com/q/54023782/10478812
"""
from typing import Optional, List, Union, Callable, Tuple, Set, Dict

from pydantic import BaseModel, validator

from .util import get_query_hash, is_weighted, is_context_weighted

__all__ = ['NetworkSearchQuery', 'ApiOptions', 'ShortestSimplePathOptions',
           'BreadthFirstSearchOptions', 'DijkstraOptions',
           'SharedInteractorsOptions', 'OntologyOptions', 'Node',
           'StmtData', 'EdgeData', 'Path', 'PathResultData', 'OntologyResults',
           'SharedInteractorsResults', 'Results', 'FilterOptions']


# Models for API options and filtering options
class ApiOptions(BaseModel):
    """Options that determine API behaviour"""
    sign: Optional[int] = None
    fplx_expand: Optional[bool] = False
    user_timout: Optional[Union[float, bool]] = False
    two_way: Optional[bool] = False
    shared_regulators: Optional[bool] = False
    format: Optional[str] = 'json'


class FilterOptions(BaseModel):
    """Options for filtering out nodes or edges"""
    exclude_stmts: List[str] = []
    hash_blacklist: List[int] = []
    allowed_ns: List[str] = []
    node_blacklist: List[str] = []
    path_length: Optional[int] = None
    belief_cutoff: float = 0.0
    curated_db_only: bool = False
    max_paths: int = 50
    weighted: bool = False
    context_weighted: bool = False
    overall_weighted: bool = False

    def no_filters(self) -> bool:
        """Return True if all filter options are set to defaults"""
        return len(self.exclude_stmts) == 0 and \
            len(self.hash_blacklist) == 0 and \
            len(self.allowed_ns) == 0 and \
            len(self.node_blacklist) == 0 and \
            self.path_length is None and \
            self.belief_cutoff == 0.0 and \
            self.curated_db_only is False

    def no_stmt_filters(self):
        """Return True if the stmt filter options allow all statements"""
        return self.belief_cutoff == 0.0 and len(self.exclude_stmts) == 0 and \
            len(self.hash_blacklist) == 0 and self.curated_db_only is False

    def no_node_filters(self):
        """Return True if the node filter options allow all nodes"""
        return len(self.node_blacklist) == 0 and len(self.allowed_ns) == 0


class NetworkSearchQuery(BaseModel):
    """The query model for network searches"""
    source: str = ''
    target: str = ''
    stmt_filter: List[str] = []
    edge_hash_blacklist: List[int] = []
    allowed_ns: List[str] = []
    node_blacklist: List[str] = []
    path_length: Optional[int] = None
    sign: Optional[str] = None
    weighted: bool = False
    belief_cutoff: Union[float, bool] = 0.0
    curated_db_only: bool = False
    fplx_expand: bool = False
    k_shortest: Optional[int] = None
    max_per_node: int = 5
    cull_best_node: List[int] = []
    mesh_ids: List[str] = []
    strict_mesh_id_filtering: bool = False
    const_c: int = 1
    const_tk: int = 10
    user_timeout: Union[float, bool] = 30
    two_way: Optional[bool] = None
    shared_regulators: Optional[bool] = None
    terminal_ns: List[str] = []
    format: Optional[str] = None

    @validator('path_length')
    def is_positive_int(cls, pl: int):
        """Validate path_length >= 1 if given"""
        if isinstance(pl, int) and pl < 1:
            raise ValueError('path_length must be integer > 0')
        return pl

    @validator('max_per_node')
    def is_pos_int(cls, mpn: Union[int, bool]):
        """Validate path_length >= 1 if given"""
        if isinstance(mpn, int) and mpn < 1:
            raise ValueError('max_per_node must be integer > 0')
        return mpn

    class Config:
        allow_mutation = False  # Error for any attempt to change attributes

    def get_hash(self):
        """Get the corresponding query hash of the query"""
        return get_query_hash(self.dict(), ignore_keys=['format'])

    def reverse_search(self):
        """Return a copy of the query with source and target switched"""
        model_copy = self.copy(deep=True).dict(exclude={'source', 'target'})
        source = self.target
        target = self.source
        return self.__class__(source=source, target=target, **model_copy)

    def get_filter_options(self) -> FilterOptions:
        """Returns the filter options"""
        return FilterOptions(exclude_stmts=self.stmt_filter,
                             hash_blacklist=self.edge_hash_blacklist,
                             allowed_ns=self.allowed_ns,
                             node_blacklist=self.node_blacklist,
                             path_length=self.path_length,
                             belief_cutoff=self.belief_cutoff,
                             curated_db_only=self.curated_db_only,
                             max_paths=self.k_shortest,
                             overall_weighted=is_weighted(
                                 weighted=self.weighted,
                                 mesh_ids=self.mesh_ids,
                                 strict_mesh_filtering=
                                 self.strict_mesh_id_filtering
                             ),
                             weighted=self.weighted,
                             context_weighted=is_context_weighted(
                                 mesh_id_list=self.mesh_ids,
                                 strict_filtering=self.strict_mesh_id_filtering
                             ))


# Models for the run options
# Todo:
#  1. instead of manually setting defaults here, use introspection of
#     function and look up functions default:
#     >>> def func(par: int = 0):
#     ...     return par
#     >>> import inspect
#     >>> func_pars = inspect.signature(func).parameters
#     >>> arg = func_pars['par']
#     >>> arg.default
#  2. For "not-None" defaults: set value to default if None is provided:
#     https://stackoverflow.com/q/63616798/10478812
#     Good for e.g. max_paths
class ShortestSimplePathOptions(BaseModel):
    """Arguments for indra.explanation.pathfinding.shortest_simple_paths"""
    source: str
    target: str
    weight: Optional[str] = None
    ignore_nodes: Optional[Set[str]] = None
    ignore_edges: Optional[Set[Tuple[str, str]]] = None
    hashes: Optional[List[int]] = None
    ref_counts_function: Optional[Callable] = None
    strict_mesh_id_filtering: Optional[bool] = False
    const_c: Optional[int] = 1
    const_tk: Optional[int] = 10


class BreadthFirstSearchOptions(BaseModel):
    """Arguments for indra.explanation.pathfinding.bfs_search"""
    source_node: str
    reverse: Optional[bool] = False
    depth_limit: Optional[int] = 2
    path_limit: Optional[int] = None
    max_per_node: Optional[int] = 5
    node_filter: Optional[List[str]] = None
    node_blacklist: Optional[Set[str]] = None
    terminal_ns: Optional[List[str]] = None
    sign: Optional[int] = None
    max_memory: Optional[int] = int(2**29)
    hashes: Optional[List[int]] = None
    allow_edge: Optional[Callable] = None
    strict_mesh_id_filtering: Optional[bool] = False


class DijkstraOptions(BaseModel):
    """Arguments for open_dijkstra_search"""
    start: str
    reverse: Optional[bool] = False
    path_limit: Optional[int] = None
    # node_filter: Optional[List[str]] = None  # Currently not implemented
    hashes: Optional[List[int]] = None
    ignore_nodes: Optional[List[str]] = None
    ignore_edges: Optional[List[Tuple[str, str]]] = None
    terminal_ns: Optional[List[str]] = None
    weight: Optional[str] = None
    ref_counts_function: Optional[Callable] = None
    const_c: Optional[int] = 1
    const_tk: Optional[int] = 10


class SharedInteractorsOptions(BaseModel):
    """Arguments for indra_network_search.pathfinding.shared_interactors"""
    source: str
    target: str
    allowed_ns: Optional[List[str]] = None
    stmt_types: Optional[List[str]] = None
    source_filter: Optional[List[str]] = None
    max_results: Optional[int] = 50
    regulators: Optional[bool] = False
    sign: Optional[int] = None


class OntologyOptions(BaseModel):
    """Arguments for indra_network_search.pathfinding.shared_parents"""
    source_ns: str
    source_id: str
    target_ns: str
    target_id: str
    max_paths: int = 50
    immediate_only: Optional[bool] = False
    is_a_part_of: Optional[Set[str]] = None


# Models and sub-models for the Results
class Node(BaseModel):
    """Data for a node"""
    name: str
    namespace: str
    identifier: str
    lookup: Optional[str] = ''


class SignedNode(BaseModel):
    """Data for a node"""
    name: str
    namespace: str
    identifier: str
    sign: int
    lookup: Optional[str] = ''

    def get_unsigned_node(self) -> Node:
        """Get unsigned version of this node instance"""
        return Node(**self.dict(exclude={'sign'}, exclude_defaults=True))


class StmtData(BaseModel):
    """Data for one statement supporting an edge"""
    stmt_type: str
    evidence_count: int
    stmt_hash: int
    source_counts: Dict[str, int]
    belief: float
    curated: bool
    english: str
    weight: Optional[float] = None
    residue: Optional[str] = ''
    position: Optional[str] = ''
    initial_sign: Optional[int] = None


class EdgeData(BaseModel):
    """Data for one single edge"""
    edge: Tuple[Node, Node]  # Edge supported by stmts
    stmts: Dict[str, List[StmtData]]  # key by stmt_type
    belief: float  # Aggregated belief
    weight: float  # Weight corresponding to aggregated weight
    sign: Optional[int]  # Used for signed paths
    context_weight: Union[str, float] = 'N/A'  # Set for context

    def is_empty(self) -> bool:
        """Return True if len(stmts) == 0"""
        return len(self.stmts) == 0


class Path(BaseModel):
    """Results for a single path"""
    # The entries are assumed to be co-ordered
    # path = [a, b, c]
    # edge_data = [EdgeData(a, b), EdgeData(b, c)]
    path: List[Node]  # Contains the path
    edge_data: List[EdgeData]  # Contains supporting data, same order as path

    def is_empty(self) -> bool:
        """Return True if len(path) == 0 or len(edge_data) == 0"""
        return len(self.path) == 0 or len(self.edge_data) == 0


class PathResultData(BaseModel):
    """Results for any of the path algorithms"""
    # Results for bfs_search, shortest_simple_paths and open_dijkstra_search
    # It is assumed that at least one of source or target will be set
    source: Optional[Node] = None
    target: Optional[Node] = None
    paths: Dict[int, List[Path]]  # keyed by node count

    def is_empty(self) -> bool:
        """Return True if paths list is empty"""
        return len(self.paths) == 0


class OntologyResults(BaseModel):
    """Results for shared_parents"""
    source: Node
    target: Node
    parents: List[Node]

    def is_empty(self) -> bool:
        """Return True if parents list is empty"""
        return len(self.parents) == 0


class SharedInteractorsResults(BaseModel):
    """Results for shared targets and shared regulators"""
    # s->x; t->x
    source_data: List[EdgeData]
    target_data: List[EdgeData]
    downstream: bool

    def is_empty(self):
        """Return True if both source and target data is empty"""
        return len(self.source_data) == 0 and len(self.target_data) == 0


class Results(BaseModel):
    """The model wrapping all results"""
    query_hash: str
    hashes: List[str] = []  # Cast as string for JavaScript
    path_results: Optional[PathResultData] = None
    ontology_results: Optional[OntologyResults] = None
    shared_target_results: Optional[SharedInteractorsResults] = None
    shared_regulators_results: Optional[SharedInteractorsResults] = None
