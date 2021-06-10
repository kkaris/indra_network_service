"""
The IndraNetworkSearch REST API
"""
import logging
from os import environ
from typing import List, Optional

import aiohttp

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .util import load_indra_graph
from .data_models import Results, NetworkSearchQuery, SubgraphRestQuery, \
    SubgraphResults
from .search_api import IndraNetworkSearchAPI
from depmap_analysis.network_functions.net_functions import bio_ontology

DEBUG = environ.get('API_DEBUG') == "1"

app = FastAPI()

logger = logging.getLogger(__name__)


class Health(BaseModel):
    """Health status"""
    status: str


class GildaMatch(BaseModel):
    """A Gilda sub model

    {'cap_combos': [['mixed', 'all_caps']],
     'dash_mismatches': ['query'],
     'exact': True,
     'query': 'M-eK',
     'ref': 'MEK',
     'space_mismatch': False}
    """
    cap_combos: List[List[str]]
    dash_mismatches: List[str]
    exact: bool
    query: str
    ref: str
    space_mismatch: bool


class GildaTerm(BaseModel):
    """A Gilda sub model

    {'db': 'FPLX',
     'entry_name': 'MEK',
     'id': 'MEK',
     'norm_text': 'mek',
     'source': 'famplex',
     'status': 'assertion',
     'text': 'MEK'}
    """
    db: str  # e.g. 'FPLX'
    entry_name: str  # e.g. 'MEK'
    id: str  # e.g. 'MEK'
    norm_text: str  # e.g. 'mek'
    source: str  # e.g. 'famplex'
    status: str  # e.g. 'assertion'
    text: str  # e.g. 'MEK'


class GildaResponse(BaseModel):
    """Gilda Response"""
    match: GildaMatch
    score: float  # Constrain to [0, 1.0]
    term: GildaTerm
    url: str


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


@app.get('/ground', response_model=List[GildaResponse])
async def ground(text: str, context: Optional[str] = None):
    """Ground entity names

    Parameters
    ----------
    text :
        Entity to ground
    context :
        Provide optional context for grounding

    Returns
    -------
    :
        The response from GILDA
    """
    jd = {'text': text}
    if context:
        jd['context'] = context
    async with aiohttp.ClientSession() as session:
        async with session.post(url='http://grounding.indra.bio/ground',
                                json=jd) as resp:
            resp_json = await resp.json()
            return [GildaResponse(**gr) for gr in resp_json]


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
    from .tests.util import _setup_graph, _setup_signed_node_graph
    dir_graph = _setup_graph()
    sign_node_graph = _setup_signed_node_graph(False)
    network_search_api = IndraNetworkSearchAPI(
        unsigned_graph=dir_graph, signed_node_graph=sign_node_graph
    )
else:
    dir_graph, _, sign_node_graph, _ = \
        load_indra_graph(unsigned_graph=True, unsigned_multi_graph=False,
                         sign_node_graph=True, sign_edge_graph=False,
                         use_cache=USE_CACHE)

    network_search_api = IndraNetworkSearchAPI(
        unsigned_graph=dir_graph, signed_node_graph=sign_node_graph
    )
    bio_ontology.initialize()
HEALTH.status = 'available'
