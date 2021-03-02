"""
The QueryHandler's job is to act as a middle layer between the network
search functionalities and the REST API that receives queries.
"""
import networkx as nx
from typing import Optional, Dict

from indra.explanation.pathfinding import shortest_simple_paths, bfs_search,\
    open_dijkstra_search
from depmap_analysis.network_functions.net_functions import SIGN_TO_STANDARD

from .query import Query, ShortestSimplePathsQuery, BreadthFirstSearchQuery, \
    DijkstraQuery
from .data_models import NetworkSearchQuery

__all__ = ['QueryHandler', 'Query', 'DijkstraQuery',
           'ShortestSimplePathsQuery', 'BreadthFirstSearchQuery']


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
        self.api_method: Optional[str] = None
        self._query: Optional[Query] = None

    def _map_to_query_type(self):
        """This method maps the query to an API method"""
        # If not open, run shortest_simple_paths and other queries
        if not self.open:
            self.api_method = shortest_simple_paths.__name__
        # If open: check if weighted options
        else:
            if _is_weighted(weight=self.weighted,
                            mesh_ids=self.mesh,
                            strict_mesh_id_filtering=self.strict_mesh):
                self.api_method = open_dijkstra_search.__name__
            else:
                self.api_method = bfs_search.__name__

    def get_query_type(self) -> str:
        """Get the query type for the"""
        if not self.api_method:
            self._map_to_query_type()
        return self.api_method

    def get_query(self) -> Query:
        """Returns the Query type associated with the search type

        Returns
        -------
        Query

        Raises
        ------
        ValueError
            Raised for unknown query types
        """
        if not self._query:
            query_type = self.get_query_type()
            if query_type == bfs_search.__name__:
                query = BreadthFirstSearchQuery(self.rest_query)
            elif query_type == open_dijkstra_search.__name__:
                query = DijkstraQuery(self.rest_query)
            elif query_type == shortest_simple_paths.__name__:
                query = ShortestSimplePathsQuery(self.rest_query)
            else:
                raise ValueError(f'Unknown query type {query_type}')
            self._query = query

        return self._query

    def get_options(self, graph: nx.DiGraph) -> Dict:
        """Get the run options matching the query"""
        asq: Query = self.get_query()
        return asq.run_options(graph=graph)


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
