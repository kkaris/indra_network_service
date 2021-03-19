"""
The IndraNetworkSearch REST API
"""
from fastapi import FastAPI

from depmap_analysis.util.io_functions import file_opener
from .data_models import Results, NetworkSearchQuery
from .search_api import IndraNetworkSearchAPI

app = FastAPI()


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
