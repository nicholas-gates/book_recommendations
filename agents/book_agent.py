from typing import List, Dict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.callbacks import CallbackManager
from langsmith.run_helpers import traceable

from models import BookRecommendations
from utils import logger
from config import RECOMMEND_BOOKS_SCHEMA
from .base_agent import BaseAgent
import json

class BookState(BaseModel):
    messages: List[dict]
    input: str
    recommendations: List[dict]

class BookAgent(BaseAgent):
    """Agent for recommending books based on user preferences."""

    @property
    def state_schema(self) -> BaseModel:
        """Return the BookState schema for the workflow."""
        return BookState

    def __init__(self):
        system_prompt = """You are an expert librarian and book recommender. Your task is to recommend books based on the user's input.
        Provide thoughtful recommendations that match the user's interests, whether they specify an author, genre, theme, or other criteria.

        Guidelines for recommendations:
        1. Provide 3-5 high-quality recommendations
        2. Ensure each book genuinely matches the user's interests
        3. Include a mix of well-known and potentially overlooked books
        4. Verify all book information is accurate
        5. Write clear, informative descriptions
        6. Explain specifically why each book matches the request

        Your response will be automatically formatted into JSON using the function call mechanism."""

        super().__init__(
            schema=BookRecommendations,
            function_name="recommend_books",
            system_prompt=system_prompt
        )
        # Create the chain during initialization
        self._chain = self.create_chain()

    @traceable(name="create_book_recommendations_chain")
    def create_chain(self):
        """Create the processing chain for book recommendations."""
        prompt = self.create_prompt("{input}")
        prompt.messages.insert(1, MessagesPlaceholder(variable_name="messages"))
        
        chain = (
            prompt
            | self.llm.bind(
                functions=[RECOMMEND_BOOKS_SCHEMA],
                function_call={"name": "recommend_books"}
            )
            | self.process_response
        )
        
        return chain

    @traceable(name="process_book_recommendations")
    def process_response(self, response):
        """Process the LLM response and validate against schema."""
        try:
            function_call = response.additional_kwargs.get("function_call", {})
            if not function_call or "arguments" not in function_call:
                return {"error": "Invalid response format"}

            try:
                args = json.loads(function_call["arguments"])
                recommendations = self.schema(**args)
                return recommendations
            except (json.JSONDecodeError, ValidationError) as e:
                return {"error": f"Invalid response: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}

    def create_workflow(self) -> StateGraph:
        """Create and configure the book recommendation workflow."""
        # Create fresh workflow instead of inheriting from base
        workflow = StateGraph(BookState)

        def recommend_books(state: BookState) -> BookState:
            """Generate book recommendations based on user input."""
            logger.info("Starting book recommendation process")
            messages = state.messages
            user_input = state.input
            logger.info(f"Processing request with input: {user_input}")

            # Use the pre-created chain
            logger.info("Invoking LLM chain for recommendations")
            result = self._chain.invoke({
                "messages": messages,
                "input": user_input
            })
            logger.info(f"Raw output from LLM: {result}")
            logger.info(f"Received {len(result.recommendations)} recommendations from LLM")

            # Update the state with recommendations
            new_state = BookState(
                messages=messages, 
                input=user_input, 
                recommendations=[rec.model_dump() for rec in result.recommendations]
            )
            logger.info("Updated state with new recommendations")
            return new_state

        workflow.add_node("recommend_books", recommend_books)
        workflow.set_entry_point("recommend_books")
        workflow.add_edge("recommend_books", END)
        return workflow

def create_book_agent():
    """Factory function to create and compile the book agent."""
    agent = BookAgent()
    workflow = agent.create_workflow()
    return workflow.compile()
