import requests
import logging
from typing import List

def web_searcher(query: str, sources: List[str] = ["google", "baidu"]) -> dict:
    """
    Perform a web search using specified sources and return the results.
    
    This function takes a search query and a list of sources, performs the search on each source,
    and returns a dictionary containing the results from each source. Currently supports Google and Baidu.
    
    参数:
        query: The search query string.
        sources: A list of sources to perform the search on. Default is ["google", "baidu"].
    
    返回:
        A dictionary with source names as keys and search results as values.
    """
    logging.basicConfig(level=logging.DEBUG)
    results = {}

    if not query:
        logging.error("Query must not be empty.")
        return results

    if not sources:
        logging.error("Sources list must not be empty.")
        return results

    for source in sources:
        try:
            if source.lower() == "google":
                results["google"] = search_google(query)
            elif source.lower() == "baidu":
                results["baidu"] = search_baidu(query)
            else:
                logging.warning(f"Source '{source}' is not supported.")
        except Exception as e:
            logging.error(f"Error occurred while searching {source}: {e}")

    return results

def search_google(query: str) -> List[str]:
    """
    Simulate a Google search and return dummy results.
    
    This function simulates a Google search by returning a list of dummy URLs.
    
    参数:
        query: The search query string.
    
    返回:
        A list of dummy URLs representing search results.
    """
    # Simulating a search result
    return [f"https://www.google.com/search?q={query.replace(' ', '+')}"]

def search_baidu(query: str) -> List[str]:
    """
    Simulate a Baidu search and return dummy results.
    
    This function simulates a Baidu search by returning a list of dummy URLs.
    
    参数:
        query: The search query string.
    
    返回:
        A list of dummy URLs representing search results.
    """
    # Simulating a search result
    return [f"https://www.baidu.com/s?wd={query.replace(' ', '+')}"]