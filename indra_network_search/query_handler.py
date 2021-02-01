"""
The QueryHandler's job is to act as a middle layer between the network
search functionalities and the REST API that receives queries.
"""
import inspect
import networkx as nx
from typing import Optional, Dict, Callable, Any, List, Tuple, Set, Union

from indra_db.client.readonly.mesh_ref_counts import get_mesh_ref_counts
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search,\
    open_dijkstra_search
from depmap_analysis.network_functions.net_functions import \
    SIGN_TO_STANDARD, SIGNS_TO_INT_SIGN

from .util import get_mandatory_args
from .data_models import NetworkSearchQuery

__all__ = ['QueryHandler', 'Query', 'DijkstraQuery',
           'BreadthFirstSearchQuery', 'ShortestSimplePathsQuery']


class MissingParametersError(Exception):
    """Raise for missing query parameters"""


class InvalidParametersError(Exception):
    """Raise when conflicting or otherwise invalid parameters """


class Query:
    """Parent class to all Query classes

    The Query classes are helpers that make sure the methods of the
    IndraNetworkSearchAPI that are used receive the data needed from the
    NetworkSearchQuery
    """
    method_name: str = NotImplemented
    alg_func: Callable = NotImplemented

    def __init__(self, query: NetworkSearchQuery):
        self.query: NetworkSearchQuery = query
        self.query_hash: str = query.get_hash()

    def assert_query(self, run_options: Dict[str, Any]):
        """Checks if incoming query has the needed data for the api_method"""
        all_func_args = set(inspect.signature(self.alg_func).parameters)

        # Check that only args that match function are provided
        if not set(run_options.keys()).issubset(all_func_args):
            raise InvalidParametersError(
                'Invalid parameters provided: "%s"' %
                '", "'.join(set(run_options.keys()).difference(all_func_args))
            )

        # Check that any args that don't have default values are set,
        # except the graph argument:

        # 1. Get the args without defaults
        args_wo_defaults = set(get_mandatory_args(self.alg_func))

        # 2. Remove args with defaults from the provided options
        options_wo_defaults = set(run_options.keys()).difference(
            )

        # 3. The difference can only be 0 or 1 (allowing for the graph
        # argument)
        if len(args_wo_defaults.difference(options_wo_defaults)) > 1:
            raise MissingParametersError(
                f'Missing mandatory arguments for calling {self.method_name}'
            )

        return run_options

    def alg_options(self) -> Dict[str, Any]:
        """Returns the options for the algorithm used, excl mesh options"""
        raise NotImplementedError

    def api_options(self) -> Dict[str, Any]:
        """These options are used when IndraNetworkSearchAPI handles the query

        The options here impact decisions on which extra search algorithms
        to include and which graph to pick
        """
        return {'sign': SIGNS_TO_INT_SIGN.get(self.query.sign),
                'fplx_expand': self.query.fplx_expand,
                'user_timout': self.query.user_timeout,
                'two_way': self.query.two_way,
                'shared_regulators': self.query.shared_regulators,
                'format': self.query.format}

    def _get_mesh_options(self, get_func: bool = True) \
            -> Tuple[Set, Union[Callable, None]]:
        """Get the necessary mesh options"""
        if len(self.query.mesh_ids) > 0:
            raise InvalidParametersError('No mesh ids provided, but method '
                                         'for getting mesh options was called')
        hash_mesh_dict: Dict[Any, Dict] = get_mesh_ref_counts(
            self.query.mesh_ids)
        related_hashes: Set = set(hash_mesh_dict.keys())
        ref_counts_from_hashes = \
            _get_ref_counts_func(hash_mesh_dict) if get_func else None
        return related_hashes, ref_counts_from_hashes

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Any]:
        """Return algorithm specific mesh options"""
        raise NotImplementedError

    def run_options(self):
        """Combines all options to one dict that can be sent to algorithm"""
        return self.assert_query({**self.alg_options(), **self.mesh_options()})


class ShortestSimplePathsQuery(Query):
    """Check queries that will use the shortest_simple_paths algorithm"""
    # Get graph from API; so ignore here
    # Args that need some pre-processing:
    #   -
    method_name: str = shortest_simple_paths.__name__
    alg_func: Callable = shortest_simple_paths

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        """Match input to shortest_simple_paths from query"""
        options = {'source': self.query.source,
                   'target': self.query.target,
                   'ignore_nodes': self.query.node_blacklist,
                   'weight': 'weight' if self.query.weighted else None,
                   'readonly': False}
        # Set 'readonly' to True if running in a parallel/threading context
        return options

    def mesh_options(self, graph: Optional[nx.DiGraph] = None) \
            -> Dict[str, Union[Set, Callable]]:
        """Match input to shortest_simple_paths

        Returns
        -------
        Tuple[Set, Callable]
        """
        # If any mesh ids are provided:
        if len(self.query.mesh_ids) > 0:
            hashes, ref_counts_func = self._get_mesh_options()
        else:
            hashes, ref_counts_func = None, None
        return {
            'hashes': hashes,
            'ref_counts_function': ref_counts_func,
            'strict_mesh_id_filtering': self.query.strict_mesh_id_filtering,
            'const_c': self.query.const_c,
            'const_tk': self.query.const_tk
        }


class BreadthFirstSearchQuery(Query):
    """Check queries that will use the bfs_search algorithm"""
    method_name: str = bfs_search.__name__
    alg_func: Callable = bfs_search

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        pass

    def mesh_options(self) -> Dict[str, Any]:
        pass


class DijkstraQuery(Query):
    """Check queries that will use the open_dijkstra_search algorithm"""
    method_name = open_dijkstra_search.__name__
    alg_func: Callable = open_dijkstra_search

    def __init__(self, query: NetworkSearchQuery):
        super().__init__(query)

    def alg_options(self) -> Dict[str, Any]:
        pass

    def mesh_options(self) -> Dict[str, Any]:
        pass


class QueryHandler:
    """Maps queries from the REST API to a method of the IndraNetworkSearchAPI

    The QueryHandler's job is to act as a middle layer between the methods
    of the IndraNetworkSearchAPI and the REST API.
    """

    def __init__(self, rest_query: NetworkSearchQuery):
        self.rest_query: NetworkSearchQuery = rest_query
        self.signed: bool = SIGN_TO_STANDARD.get(rest_query.sign) in ('+', '-')
        self.open: bool = bool(rest_query.source) ^ bool(rest_query.target)
        self.weighted: bool = bool(rest_query.weighted)
        self.mesh: bool = bool(rest_query.mesh_ids)
        self.strict_mesh: bool = rest_query.strict_mesh_id_filtering
        self.api_method: Optional[str] = None
        self._query: Optional[Query] = None

    def _map_to_query_type(self):
        """This method maps the query to an API method"""
        # If not open, run shortest_simple_paths
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

    def get_options(self) -> Dict:
        """Get the run options matching the query"""
        asq: Query = self.get_query()
        return asq.alg_options()


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


def _get_ref_counts_func(hash_mesh_dict: Dict):
    def _func(graph: nx.DiGraph, u: str, v: str):
        # Get hashes for edge
        hashes = [d['stmt_hash'] for d in graph[u][v]['statements']]

        # Get all relevant mesh counts
        dicts: List[Dict] = [hash_mesh_dict.get(h, {'': 0, 'total': 1})
                             for h in hashes]

        # Count references
        ref_counts: int = sum(sum(v for k, v in d.items() if k != 'total')
                              for d in dicts)
        total: int = sum(d['total'] for d in dicts) or 1
        return ref_counts, total
    return _func
