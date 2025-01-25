from typing import Dict, TypeVar, Generic, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, ValidationError
import json
from functools import cached_property

from utils import logger
from config import MODEL_NAME, TEMPERATURE

StateType = TypeVar('StateType')

class BaseAgent(Generic[StateType]):
    """Base class for all recommendation agents providing common functionality."""

    def __init__(self,
                 schema: BaseModel,
                 function_name: str,
                 system_prompt: str,
                 entry_point: Optional[str] = None,
                 finish_point: Optional[str] = None):
        """
        Initialize the base agent with enhanced configuration.

        Args:
            schema: Pydantic model for response validation
            function_name: Name of the function to call
            system_prompt: System prompt for the LLM
            entry_point: Optional custom entry point name for workflow
            finish_point: Optional custom finish point name for workflow
        """
        self.schema = schema
        self.function_name = function_name
        self.system_prompt = system_prompt
        self._entry_point = entry_point or f"{function_name}_entry"
        self._finish_point = finish_point or f"{function_name}_finish"

    @cached_property
    def llm(self) -> ChatOpenAI:
        """Initialize and configure the LLM with caching."""
        return ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
        )

    def create_prompt(self, human_template: str) -> ChatPromptTemplate:
        """
        Create a standardized prompt template with improved type safety.

        Args:
            human_template: The human message template

        Returns:
            Configured ChatPromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", human_template)
        ])

    def process_response(self, response) -> Dict:
        """
        Process and validate the LLM response with enhanced error handling.

        Args:
            response: Raw LLM response

        Returns:
            Dictionary with validated response data

        Raises:
            ValueError: If response format is invalid
            ValidationError: If schema validation fails
        """
        try:
            logger.info(f"Validating {self.function_name} response")
            if not hasattr(response, 'additional_kwargs'):
                logger.warning(f"No additional_kwargs in {self.function_name} response")
                return {}

            function_call = response.additional_kwargs.get('function_call')
            if not function_call:
                logger.warning(f"No function call found in {self.function_name} response")
                return {}

            args = json.loads(function_call.get('arguments', '{}'))
            self.schema(**args)  # Validate with Pydantic
            logger.info(f"Successfully validated {self.function_name} response")
            return args

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.function_name} response: {e}")
            raise ValueError("Invalid JSON format in response") from e
        except ValidationError as e:
            logger.error(f"Schema validation failed for {self.function_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {self.function_name} response: {e}")
            raise

    @property
    def state_schema(self) -> BaseModel:
        """Return the state schema for the workflow."""
        raise NotImplementedError("Derived classes must implement state_schema property")

    def create_workflow(self) -> StateGraph:
        """Create a basic workflow with configurable entry and finish points."""
        workflow = StateGraph(self.state_schema)
        workflow.set_entry_point(self._entry_point)
        workflow.set_finish_point(self._finish_point)
        return workflow