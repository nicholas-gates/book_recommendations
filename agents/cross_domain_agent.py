from typing import Dict, Optional
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from models import CrossDomainRecommendation
from utils import logger
from config import CROSS_DOMAIN_SCHEMA
from .base_agent import BaseAgent

class CrossDomainState(BaseModel):
    """State model for cross-domain recommendations."""
    selected_book: Dict[str, str]
    retry_count: int = 0
    error: Optional[str] = None
    cross_domain_recommendations: Optional[Dict] = None
    status: Optional[str] = None

class CrossDomainAgent(BaseAgent):
    """Agent for recommending related content across different domains."""

    def __init__(self):
        system_prompt = """You are an expert content recommender who can find thematic connections across different media types.
        Based on the given book, recommend ONE movie, ONE game, and ONE song that share similar themes, moods, or ideas.

        Guidelines for recommendations:
        1. Focus on thematic connections, not just genre matches
        2. Consider emotional resonance and core ideas
        3. Provide thoughtful explanations for each recommendation
        4. Be specific about why each item connects to the book
        5. Consider both classic and contemporary options

        Your response will be automatically formatted using the function call mechanism."""

        super().__init__(
            schema=CrossDomainRecommendation,
            function_name="recommend_cross_domain",
            system_prompt=system_prompt
        )

    def create_chain(self):
        """Create the processing chain for cross-domain recommendations."""
        human_template = """Here is the book to base recommendations on:
        Title: {title}
        Author: {author}
        Genre: {genre}
        Description: {description}

        Please recommend related content that shares themes with this book."""

        prompt = self.create_prompt(human_template)
        return (
            prompt
            | self.llm.bind(functions=[CROSS_DOMAIN_SCHEMA], function_call={"name": "recommend_cross_domain"})
            | self.process_response
        )

    @property
    def state_schema(self) -> BaseModel:
        """Return the state schema for the workflow."""
        return CrossDomainState

    def validate_input_state(self, state: CrossDomainState) -> bool:
        """Validate the input state has required book information."""
        selected_book = state.selected_book
        required_fields = ["title", "author", "genre", "description"]
        return all(selected_book.get(field) for field in required_fields)

    def create_workflow(self) -> StateGraph:
        """Create and configure the cross-domain recommendation workflow."""
        workflow = StateGraph(CrossDomainState)

        # Entry point node for initial state validation
        def recommend_cross_domain_entry(state: CrossDomainState) -> CrossDomainState:
            """Validate input state before processing."""
            if not self.validate_input_state(state):
                logger.error("Invalid input state: missing required book information")
                state.error = "Missing required book information"
                return state
            state.retry_count = 0
            return state

        # Main processing node with retry logic
        def recommend_related_content(state: CrossDomainState) -> CrossDomainState:
            """Generate cross-domain recommendations with retry logic."""
            if state.error:
                return state

            if state.retry_count >= 3:
                logger.error("Max retries reached for cross-domain recommendations")
                state.error = "Failed to generate recommendations after 3 attempts"
                return state

            try:
                selected_book = state.selected_book
                chain = self.create_chain()
                result = chain.invoke({
                    "title": selected_book["title"],
                    "author": selected_book["author"],
                    "genre": selected_book["genre"],
                    "description": selected_book["description"]
                })
                state.cross_domain_recommendations = result
                return state
            except Exception as e:
                logger.error(f"Error generating recommendations: {str(e)}")
                state.retry_count += 1
                return state

        # Error handling node
        def handle_error(state: CrossDomainState) -> CrossDomainState:
            """Process errors and prepare final error state."""
            if state.error:
                logger.error(f"Final error state: {state.error}")
                state.status = "error"
            return state

        # Add nodes
        workflow.add_node("recommend_cross_domain_entry", recommend_cross_domain_entry)
        workflow.add_node("recommend_related", recommend_related_content)
        workflow.add_node("handle_error", handle_error)

        # Configure edges with proper error handling
        workflow.add_conditional_edges(
            "recommend_cross_domain_entry",
            lambda state: "recommend_related" if not state.error else "handle_error",
            {
                "recommend_related": "recommend_related",
                "handle_error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "recommend_related",
            lambda state: (
                END if state.cross_domain_recommendations
                else "handle_error" if state.error or state.retry_count >= 3
                else "recommend_related"
            ),
            {
                "handle_error": "handle_error",
                "recommend_related": "recommend_related",
                END: END
            }
        )

        workflow.add_edge("handle_error", END)

        # Set entry point
        workflow.set_entry_point("recommend_cross_domain_entry")

        return workflow.compile()  # Compile the workflow before returning

def create_cross_domain_agent():
    """Factory function to create and compile the cross-domain agent."""
    agent = CrossDomainAgent()
    return agent.create_workflow()
