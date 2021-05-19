"""
The IndraNetworkSearch REST API
"""
import logging
import networkx as nx
from os import environ

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .util import load_indra_graph
from .data_models import Results, NetworkSearchQuery, SubgraphRestQuery, \
    SubgraphResults
from .search_api import IndraNetworkSearchAPI
from depmap_analysis.network_functions.net_functions import bio_ontology

DEBUG = environ.get('API_DEBUG') == "1"

app = FastAPI()

origins = [
    'http://localhost',
    'http://localhost:8080',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


class Health(BaseModel):
    """Health status"""
    status: str


USE_CACHE = bool(environ.get('USE_CACHE', False))
HEALTH = Health(status='booting')


@app.get('/')
async def root_redirect():
    """Redirect to docs

    This is a temporary solution until the Vue frontend is in place
    """
    return RedirectResponse(app.root_path + '/redoc')


@app.get('/health', response_model=Health)
async def health():
    """Returns health status

    Returns
    -------
    Health
    """
    logger.info('Got health check')
    return HEALTH


@app.post('/query', response_model=Results)
def query(search_query: NetworkSearchQuery):
    """Interface with IndraNetworkSearchAPI.handle_query

    Parameters
    ----------
    search_query : NetworkSearchQuery
        Query to the NetworkSearchQuery

    Returns
    -------
    Results
    """
    logger.info(f'Got NetworkSearchQuery: {search_query.dict()}')
    results = network_search_api.handle_query(rest_query=search_query)
    return results


@app.post('/subgraph', response_model=SubgraphResults)
def sub_graph(search_query: SubgraphRestQuery):
    """Interface with IndraNetworkSearchAPI.handle_subgraph_query

    Parameters
    ----------
    search_query: SubgraphRestQuery
        Query to for IndraNetworkSearchAPI.handle_subgraph_query

    Returns
    -------
    SubgraphResults
    """
    logger.info(f'Got subgraph query with {len(search_query.nodes)} nodes')
    subgraph_results = network_search_api.handle_subgraph_query(
        subgraph_rest_query=search_query)
    return subgraph_results


if DEBUG:
    network_search_api = IndraNetworkSearchAPI(
        unsigned_graph=nx.DiGraph(),
        signed_node_graph=nx.DiGraph()
    )
else:
    # dir_graph, _, sign_node_graph, _ = \
    #     load_indra_graph(unsigned_graph=True, unsigned_multi_graph=False,
    #                      sign_node_graph=True, sign_edge_graph=False,
    #                      use_cache=USE_CACHE)
    #
    # network_search_api = IndraNetworkSearchAPI(
    #     unsigned_graph=dir_graph, signed_node_graph=sign_node_graph
    # )
    from depmap_analysis.util.io_functions import file_opener
    dir_graph = file_opener('s3://depmap-analysis/graphs/stmts/'
                            'indranet_dir_subgraph_latest.pkl')

    network_search_api = IndraNetworkSearchAPI(
        unsigned_graph=dir_graph, signed_node_graph=nx.DiGraph()
    )
    bio_ontology.initialize()
HEALTH.status = 'available'
