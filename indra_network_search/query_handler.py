"""
The QueryHandler's job is to act as a middle layer between the network
search functionalities and the REST API that receives queries.
"""
from typing import List, Tuple, Union, Dict

from depmap_analysis.network_functions.net_functions import SIGN_TO_STANDARD
from .query import Query, ShortestSimplePathsQuery, BreadthFirstSearchQuery, \
    DijkstraQuery, SharedTargetsQuery, OntologyQuery, SharedRegulatorsQuery
from .data_models import NetworkSearchQuery
from .pathfinding import shared_parents

__all__ = ['QueryHandler']


class QueryHandler:
    """Maps queries from the REST API to a method of the IndraNetworkSearchAPI

    The QueryHandler's job is to act as a middle layer between the methods
    of the IndraNetworkSearchAPI and the REST API. It figures out which
    queries are eligible from the input query.
    """

    def __init__(self, rest_query: NetworkSearchQuery):
        self.rest_query: NetworkSearchQuery = rest_query
        self.rest_query_hash: int = rest_query.get_hash()
        self.signed: bool = SIGN_TO_STANDARD.get(rest_query.sign) in ('+', '-')
        self.open: bool = bool(rest_query.source) ^ bool(rest_query.target)
        self.weighted: bool = bool(rest_query.weighted)
        self.mesh: bool = bool(rest_query.mesh_ids)
        self.strict_mesh: bool = rest_query.strict_mesh_id_filtering
        self._query_dict: Dict[str, Query] = {}

    def _get_queries(self) -> Dict[str, Query]:
        """This method maps the rest_query to different eligible queries"""
        query_dict: Dict[str, Query] = {}
        # If not open: Add shortest_simple_paths and add other queries
        if not self.open:
            query_dict['path_query'] = \
                ShortestSimplePathsQuery(self.rest_query)
            query_dict.update(self._aux_queries())
            if self.rest_query.two_way:
                query_dict['reverse_path_query'] = \
                    ShortestSimplePathsQuery(self.rest_query.reverse_search())
        # If open: check if weighted options
        else:
            if _is_weighted(weight=self.weighted,
                            mesh_ids=self.mesh,
                            strict_mesh_id_filtering=self.strict_mesh):
                query_dict['path_query'] = DijkstraQuery(self.rest_query)
                if self.rest_query.two_way:
                    query_dict['reverse_path_query'] = \
                        DijkstraQuery(self.rest_query.reverse_search())

            else:
                query_dict['path_query'] = \
                    BreadthFirstSearchQuery(self.rest_query)
            if self.rest_query.two_way:
                query_dict['reverse_path_query'] = \
                    BreadthFirstSearchQuery(self.rest_query.reverse_search())

        return query_dict

    def _aux_queries(self) -> \
            Dict[str, Union[SharedRegulatorsQuery, SharedTargetsQuery,
                            OntologyQuery]]:
        """Get shared interactors and ontological query"""
        aux_queries = \
            {'shared_targets': SharedTargetsQuery(self.rest_query),
             shared_parents.__name__: OntologyQuery(self.rest_query)}
        if self.rest_query.shared_regulators:
            aux_queries['shared_regulators'] = \
                SharedRegulatorsQuery(self.rest_query)

        return aux_queries

    def get_queries(self) -> Dict[str, Query]:
        """Returns a dict of {query name: Query} for all eligible queries

        Returns
        -------
        List[Tuple[str, Query]]
        """
        if not self._query_dict:
            self._query_dict = self._get_queries()
        return self._query_dict


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
