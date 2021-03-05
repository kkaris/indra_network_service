from typing import Optional, List, Union, Callable, Tuple, Set

from pydantic import BaseModel, validator

from indra_network_search.util import get_query_hash


__all__ = ['NetworkSearchQuery', 'ShortestSimplePathOptions', 'ApiOptions']


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
    user_timeout: Optional[Union[float, bool]] = None
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

    def get_hash(self):
        """Get the corresponding query hash of the query"""
        return get_query_hash(self.dict(), ignore_keys=['format'])

    def reverse_search(self) -> BaseModel:
        """Return a copy of the query with source and target switched"""
        model_copy = self.copy(deep=True)
        model_copy.target = self.source
        model_copy.source = self.target
        return model_copy


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


