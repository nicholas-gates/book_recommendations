# Developer Notes

# LangSmith Tracing

## Automatic Tracing
LangSmith automatically traces these components without needing explicit `@traceable` decorators:

1. LangChain built-in components:
   - Chains (RunnableSequence)
   - LLM calls (ChatOpenAI)
   - Prompts (ChatPromptTemplate)

2. LangGraph components:
   - Graph nodes
   - Channel operations

## Manual Tracing
Use the `@traceable` decorator when you want to trace custom Python functions that aren't part of the built-in components. The decorator is useful for:
1. Adding visibility to custom business logic
2. Tracking specific function execution times
3. Adding custom metadata to spans
4. Breaking down complex operations into traceable steps

However, you need to explicitly use the @traceable decorator when you want to trace custom Python functions that aren't part of these built-in components. This is why we see process_book_recommendations in the trace - it has the decorator:

```python
@traceable(name="process_book_recommendations")
def process_response(self, response):
```

Looking at your trace, you can see this mix of automatic tracing (RunnableSequence, ChatOpenAI, etc.) and explicitly traced functions (process_book_recommendations).
