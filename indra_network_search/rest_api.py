"""
The IndraNetworkSearch REST API
"""
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from depmap_analysis.util.io_functions import file_opener
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


# Todo: move to file loader that finds latest iteration of files
dir_graph_file = \
    's3://depmap-analysis/graphs/2021-01-26/indranet_dir_graph.pkl'
sign_node_graph_file = \
    's3://depmap-analysis/graphs/2021-01-26/indranet_sign_node_graph.pkl'

network_search_api = IndraNetworkSearchAPI(
    unsigned_graph=file_opener(dir_graph_file),
    signed_node_graph=file_opener(sign_node_graph_file)
)

HEALTH.status = 'available'
