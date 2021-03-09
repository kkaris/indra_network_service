"""
The QueryHandler's job is to act as a middle layer between the network
search functionalities and the REST API that receives queries.
"""
from typing import Optional, List, Tuple, Union

from indra.explanation.pathfinding import shortest_simple_paths, bfs_search,\
    open_dijkstra_search
from depmap_analysis.network_functions.net_functions import SIGN_TO_STANDARD

from .query import Query, ShortestSimplePathsQuery, BreadthFirstSearchQuery, \
    DijkstraQuery, SharedTargetsQuery, OntologyQuery, SharedRegulatorsQuery
from .data_models import NetworkSearchQuery
from .pathfinding import shared_parents

__all__ = ['QueryHandler']


class QueryHandler:
    """Maps queries from the REST API to a method of the IndraNetworkSearchAPI

    The QueryHandler's job is to act as a middle layer between the methods
    of the IndraNetworkSearchAPI and the REST API.
    """

    def __init__(self, rest_query: NetworkSearchQuery):
        self.rest_query: NetworkSearchQuery = rest_query
        self.rest_query_hash: int = rest_query.get_hash()
        self.signed: bool = SIGN_TO_STANDARD.get(rest_query.sign) in ('+', '-')
        self.open: bool = bool(rest_query.source) ^ bool(rest_query.target)
        self.weighted: bool = bool(rest_query.weighted)
        self.mesh: bool = bool(rest_query.mesh_ids)
        self.strict_mesh: bool = rest_query.strict_mesh_id_filtering
        self._query_list: Optional[List[Tuple[str, Query]]] = None
        self._queries: Optional[List[Query]] = None

    def _map_to_path_query(self):
        """This method maps the rest_query to API methods"""
        # If not open, run shortest_simple_paths and other queries
        if not self.open:
            self._query_list = [(shortest_simple_paths.__name__,
                                 ShortestSimplePathsQuery(self.rest_query))]
            self._query_list.extend(self._aux_queries())
        # If open: check if weighted options
        else:
            if _is_weighted(weight=self.weighted,
                            mesh_ids=self.mesh,
                            strict_mesh_id_filtering=self.strict_mesh):
                self._query_list = [open_dijkstra_search.__name__,
                                    DijkstraQuery(self.rest_query)]
            else:
                self._query_list = [bfs_search.__name__,
                                    BreadthFirstSearchQuery(self.rest_query)]

    def _aux_queries(self) -> \
            List[Tuple[str, Union[SharedRegulatorsQuery, OntologyQuery]]]:
        """Get shared interactors and ontological query"""
        aux_queries = \
            [('shared_regulators', SharedRegulatorsQuery(self.rest_query)),
             (shared_parents.__name__, OntologyQuery(self.rest_query))]
        if self.rest_query.shared_regulators:
            aux_queries.append(
                ('shared_targets', SharedTargetsQuery(self.rest_query))
            )

        return aux_queries

    def get_query_list(self) -> List[Tuple[str, Query]]:
        """Returns a list of (query name, Query) tuples

        Returns
        -------
        List[Tuple[str, Query]]
        """
        if not self._query_list:
            self._map_to_path_query()
        return self._query_list


def _is_context_weighted(mesh_id_list: bool, strict_filtering: bool):
    """Context weighted search: provide mesh ids without strict filtering"""
    if mesh_id_list and not strict_filtering:
        return True
    return False


def _is_weighted(weight: bool, mesh_ids: bool, strict_mesh_id_filtering: bool):
    """Any type of weighted search"""
    if mesh_ids:
        ctx_w = _is_context_weighted(mesh_id_list=mesh_ids,
                                     strict_filtering=strict_mesh_id_filtering)
        return weight or ctx_w
    else:
        return weight
