from typing import Dict, List
from agents.book_agent import create_book_agent
from agents.cross_domain_agent import create_cross_domain_agent
from utils import logger

def get_book_recommendations(user_input: str) -> List[Dict]:
    """Get book recommendations using the book agent"""
    logger.info("Creating recommendation agent")
    graph = create_book_agent()

    # Initialize the state
    state = {
        "messages": [],
        "input": user_input,
        "recommendations": []
    }
    logger.info(f"Initialized state with input: {user_input}")

    # Run the graph
    logger.info("Running recommendation graph")
    result = graph.invoke(state)
    logger.info("Received recommendations from graph")

    return result["recommendations"]

def get_cross_domain_recommendations(selected_book: Dict) -> Dict:
    """Get cross-domain recommendations using the cross-domain agent"""
    cross_domain_graph = create_cross_domain_agent()

    # Initialize state with selected book
    state = {"selected_book": selected_book}

    # Get cross-domain recommendations
    result = cross_domain_graph.invoke(state)
    return result.get("cross_domain_recommendations", {})