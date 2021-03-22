"""
The IndraNetworkSearch REST API
"""
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from .util import load_indra_graph
from .data_models import Results, NetworkSearchQuery
from .search_api import IndraNetworkSearchAPI

app = FastAPI()

logger = logging.getLogger(__name__)


class Health(BaseModel):
    """Health status"""
    status: str


HEALTH = Health(status='booting')


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


dir_graph, _, sign_node_graph, _ = \
    load_indra_graph(unsigned_graph=True, unsigned_multi_graph=False,
                     sign_node_graph=True, sign_edge_graph=False)

network_search_api = IndraNetworkSearchAPI(unsigned_graph=dir_graph,
                                           signed_node_graph=sign_node_graph)

HEALTH.status = 'available'
