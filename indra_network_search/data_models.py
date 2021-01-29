from typing import Optional, List, Union

from pydantic import BaseModel, validator

from indra_network_search.util import get_query_hash


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
    weighted: Optional[bool] = None
    belief_cutoff: Optional[Union[float, bool]] = None
    curated_db_only: Optional[bool] = None
    fplx_expand: Optional[bool] = None
    k_shortest: Optional[Union[int, bool]] = None
    max_per_node: Optional[Union[int, bool]] = None
    cull_best_node: Optional[int] = None
    mesh_ids: Optional[List[str]] = None
    strict_mesh_id_filtering: Optional[bool] = None
    const_c: Optional[int] = None
    const_tk: Optional[int] = None
    user_timeout: Optional[Union[float, bool]] = None
    two_way: Optional[bool] = None
    shared_regulators: Optional[bool] = None
    terminal_ns: Optional[List[str]] = None
    format: Optional[str] = None

    @validator('path_length')
    def is_positive_int(cls, pl: int):
        """Validate path_length >= 1 if given"""
        if pl is not None and pl < 1:
            raise ValueError('path_length must be positive integer')
        return pl

    def get_hash(self):
        """Get the corresponding query hash of the query"""
        # todo: Check if self.__hash__ might be any good here?
        return get_query_hash(self.dict())
