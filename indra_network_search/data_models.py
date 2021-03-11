"""
This file contains data models for queries, results and arguments to algorithm
functions.
"""
from typing import Optional, List, Union, Callable, Tuple, Set, Dict

from pydantic import BaseModel, validator

from indra_network_search.util import get_query_hash

__all__ = ['NetworkSearchQuery', 'ApiOptions', 'ShortestSimplePathOptions',
           'BreadthFirstSearchOptions', 'DijkstraOptions',
           'SharedInteractorsOptions', 'OntologyOptions', 'Node',
           'StmtData', 'EdgeData', 'Path', 'PathResults',
           'OntologyResults', 'SharedInteractorsResults', 'Results']


class NetworkSearchQuery(BaseModel):
    """The query model for network searches"""
    source: Optional[str] = None
    target: Optional[str] = None
    stmt_filter: Optional[List[str]] = None
    edge_hash_blacklist: Optional[List[int]] = None
    allowed_ns: Optional[List[str]] = None
    node_blacklist: Optional[List[str]] = None
    path_length: Optional[int] = None
    sign: Optional[str] = None
    weighted: Optional[bool] = False
    belief_cutoff: Optional[Union[float, bool]] = None
    curated_db_only: Optional[bool] = None
    fplx_expand: Optional[bool] = None
    k_shortest: Optional[Union[int, bool]] = None
    max_per_node: Optional[Union[int, bool]] = None
    cull_best_node: Optional[int] = None
    mesh_ids: Optional[List[str]] = None
    strict_mesh_id_filtering: Optional[bool] = None
    const_c: Optional[int] = 1
    const_tk: Optional[int] = 10
    user_timeout: Optional[Union[float, bool]] = False
    two_way: Optional[bool] = None
    shared_regulators: Optional[bool] = None
    terminal_ns: Optional[List[str]] = None
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


# Model for API options
class ApiOptions(BaseModel):
    """Options that determine API behaviour"""
    sign: Optional[int] = None
    fplx_expand: Optional[bool] = False
    user_timout: Optional[Union[float, bool]] = False
    two_way: Optional[bool] = False
    shared_regulators: Optional[bool] = False
    format: Optional[str] = 'json'


# Models for the run options
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
    immediate_only: Optional[bool] = False
    is_a_part_of: Optional[Set[str]] = None


# Models and sub-models for the Results
class Node(BaseModel):
    """Data for a node"""
    name: str
    namespace: str
    identifier: str
    lookup: Optional[str] = ''


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


class EdgeData(BaseModel):
    """Data for one single edge"""
    edge: Tuple[str, str]  # Edge supported by stmts
    stmts: Dict[str, List[StmtData]]  # key by stmt_type
    belief: float  # Aggregated belief
    weight: float  # Weight corresponding to aggregated weight
    sign: Optional[int]  # Used for signed paths
    context_weight: Optional[Union[str, float]] = 'N/A'  # Set for context


class Path(BaseModel):
    """Results for a single path"""
    # The entries are assumed to be co-ordered
    # path = [a, b, c]
    # edge_data = [EdgeData(a, b), EdgeData(b, c)]
    path: List[Node]  # Contains the path
    edge_data: List[EdgeData]  # Contains supporting data, in same order as


class PathResults(BaseModel):
    """Results for any of the path algorithms"""
    # Results for bfs_search, shortest_simple_paths and open_dijkstra_search
    # It is assumed that at least one of source or target will be set
    source: Optional[Node] = None
    target: Optional[Node] = None
    paths: Dict[int, List[Path]]  # keyed by node count


class OntologyResults(BaseModel):
    """Results for shared_parents"""
    source: Node
    target: Node
    parents: List[Node]


class SharedInteractorsResults(BaseModel):
    """Results for shared targets and shared regulators"""
    # s->x; t->x
    source_data: List[EdgeData]
    target_data: List[EdgeData]
    interactor: str
    downstream: bool


class Results(BaseModel):
    """The model wrapping all results"""
    query_hash: str
    hashes: Optional[List[str]] = []  # Cast as string for JavaScript
    path_results: Optional[PathResults] = None
    ontology_results: Optional[OntologyResults] = None
    shared_target_results: Optional[SharedInteractorsResults] = None
    shared_regulators_results: Optional[SharedInteractorsResults] = None
