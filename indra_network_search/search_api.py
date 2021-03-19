"""
The INDRA Network Search API

This class represents an API that executes search queries

Queries for specific searches are found in indra_network_search.query
"""
from typing import Union

from networkx import DiGraph

from depmap_analysis.network_functions.famplex_functions import \
    get_identifiers_url
from indra.explanation.pathfinding import shortest_simple_paths, bfs_search, \
    open_dijkstra_search
from .data_models import *
from .query_handler import *
from .query import *
from .result_handler import *
from .pathfinding import *

__all__ = ['IndraNetworkSearchAPI']


class IndraNetworkSearchAPI:
    """Parent class for the unsigned and signed search classes"""
    def __init__(self, unsigned_graph: DiGraph, signed_node_graph: DiGraph):
        self._digraph: DiGraph = unsigned_graph
        self._sng: DiGraph = signed_node_graph

    def get_graph(self, signed: bool = False) -> DiGraph:
        """Returns the graph used for pathfinding"""
        if signed:
            return self._sng
        else:
            return self._digraph

    def handle_query(self, rest_query: NetworkSearchQuery) -> Results:
        """

        Parameters
        ----------
        rest_query

        Returns
        -------
        Results

        """
        query_handler = QueryHandler(rest_query=rest_query)
        eligible_queries = query_handler.get_queries()

        # Initialize results
        results = Results(query_hash=rest_query.get_hash())

        # Get result manager for path query
        result_managers = {}
        path_result_manager = self.path_query(eligible_queries['path_query'])

        for alg_name, query in eligible_queries.items():
            if alg_name == 'path_query':
                continue

            # Other results
            if isinstance(query, SharedTargetsQuery):
                result_managers[alg_name] = \
                    self.shared_targets(query)
            elif isinstance(query, SharedRegulatorsQuery):
                result_managers[alg_name] = \
                    self.shared_regulators(query)
            elif isinstance(query, OntologyQuery):
                result_managers[alg_name] = \
                    self.shared_parents(query)

        # Execute all get_results with the path query last, as it takes the
        # longest
        for alg_name, res_man in result_managers.items():
            if alg_name == 'shared_targets':
                results.shared_target_results = res_man.get_results()
            elif alg_name == 'shared_regulators':
                results.shared_regulators_results = res_man.get_results()
            elif alg_name == shared_parents.__name__:
                results.ontology_results = res_man.get_results()

        results.path_results = path_result_manager.get_results()

        return results

    def get_node(self, node_name: str) -> Union[Node, None]:
        """Returns an instance of a Node matching the input name,
        if it exists

        Parameters
        ----------
        node_name : str
            Name of node to look up
        """
        g = self.get_graph()
        db_ns = g.nodes.get(node_name, {}).get('ns')
        db_id = g.nodes.get(node_name, {}).get('id')
        lookup = get_identifiers_url(db_name=db_ns, db_id=db_id) or ''
        if db_id is None and db_ns is None:
            return None
        return Node(name=node_name, namespace=db_ns,
                    identifier=db_id, lookup=lookup)

    def path_query(self, path_query: Union[Query, PathQuery]) -> ResultManager:
        """Wrapper for the mutually exclusive path queries

        Parameters
        ----------
        path_query : Union[Query, PathQuery]
            An instance of a Query or PathQuery

        Returns
        -------
        ResultManager
        """
        if isinstance(path_query, ShortestSimplePathsQuery):
            return self.shortest_simple_paths(path_query)
        elif isinstance(path_query, DijkstraQuery):
            return self.dijkstra(path_query)
        elif isinstance(path_query, BreadthFirstSearchQuery):
            return self.breadth_first_search(path_query)
        else:
            raise ValueError(f'Unknown PathQuery of type '
                             f'{path_query.__class__}')

    def shortest_simple_paths(
            self, shortest_simple_paths_query: ShortestSimplePathsQuery
    ) -> ShortestSimplePathsResultManager:
        """Get results from running shortest_simple_paths

        Parameters
        ----------
        shortest_simple_paths_query : ShortestSimplePathsQuery
            The input query holding the options to the algorithm

        Returns
        -------
        ShortestSimplePathsResultManager
            An instance of the ShortestSimplePathsResultManager, holding
            results from running shortest_simple_paths_query
        """
        sspq = shortest_simple_paths_query
        graph = self.get_graph()
        path_gen = shortest_simple_paths(G=graph,
                                         **sspq.run_options(graph=graph))

        return ShortestSimplePathsResultManager(path_generator=path_gen,
                                                graph=graph,
                                                **sspq.result_options())

    def breadth_first_search(
            self, breadth_first_search_query: BreadthFirstSearchQuery
    ) -> BreadthFirstSearchResultManager:
        """Get results from running bfs_search

        Parameters
        ----------
        breadth_first_search_query : BreadthFirstSearchQuery
            The input query holding the options to the algorithm

        Returns
        -------
        BreadthFirstSearchResultManager
            An instance of the BreadthFirstSearchResultManager, holding
            results from running bfs_search
        """
        bfsq = breadth_first_search_query
        graph = self.get_graph()
        path_gen = bfs_search(g=graph, **bfsq.run_options(graph=graph))
        return BreadthFirstSearchResultManager(path_generator=path_gen,
                                               graph=graph,
                                               **bfsq.result_options())

    def dijkstra(self, dijkstra_query: DijkstraQuery) -> DijkstraResultManager:
        """Get results from running open_dijkstra_search

        Parameters
        ----------
        dijkstra_query : DijkstraQuery
            The input query holding options for open_dijkstra_search and
            DijkstraResultManager

        Returns
        -------
        DijkstraResultManager
            An instance of the DijkstraResultManager, holding results from
            running open_dijkstra_search

        """
        dq = dijkstra_query
        path_gen = open_dijkstra_search(g=self.get_graph(), **dq.run_options())
        graph = self.get_graph()
        return DijkstraResultManager(path_generator=path_gen,
                                     graph=graph,
                                     **dq.result_options())

    def shared_targets(self, shared_targets_query: SharedTargetsQuery) -> \
            SharedInteractorsResultManager:
        """Get results from running shared_interactors looking for targets

        Parameters
        ----------
        shared_targets_query
            The input query holding options for shared_interactors and
            SharedInteractorsResultManager

        Returns
        -------
        SharedInteractorsResultManager
            An instance of the ...Manager, holding results from
            running ...
        """
        stq = shared_targets_query
        graph = self.get_graph()
        path_gen = shared_interactors(graph=graph,
                                      **stq.run_options())
        return SharedInteractorsResultManager(path_generator=path_gen,
                                              graph=graph,
                                              **stq.result_options())

    def shared_regulators(
            self, shared_regulators_query: SharedRegulatorsQuery) -> \
            SharedInteractorsResultManager:
        """Get results from running

        Parameters
        ----------
        shared_regulators_query
            The input query holding options for ... and ...ResultManager

        Returns
        -------
        SharedInteractorsResultManager
            An instance of the ...Manager, holding results from
            running ...
        """
        srq = shared_regulators_query
        graph = self.get_graph()
        path_gen = shared_interactors(graph=graph,
                                      **srq.run_options())
        return SharedInteractorsResultManager(path_generator=path_gen,
                                              graph=graph,
                                              **srq.result_options())

    def shared_parents(self, ontology_query: OntologyQuery) -> \
            OntologyResultManager:
        """Get results from running

        Parameters
        ----------
        ontology_query
            The input query holding options for ... and ...ResultManager

        Returns
        -------
        OntologyResultManager
        """
        oq = ontology_query
        path_gen = shared_parents(**oq.run_options())
        graph = self.get_graph()
        return OntologyResultManager(path_generator=path_gen,
                                     graph=graph, **oq.result_options())
