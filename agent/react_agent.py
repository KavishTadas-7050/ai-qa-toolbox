"""ReAct agent for CI failure analysis.

Uses LangChain's ReAct (Reason + Act) pattern to orchestrate tool calls.
The agent reasons about which tools to call and in what order, producing
a Thought -> Action -> Observation loop visible in verbose output.
"""

from __future__ import annotations

import json

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agent.llm_backend import get_llm
from agent.tools import classify_log_file, classify_log_text, list_sample_logs


# ReAct prompt template — instructs the LLM on the Thought/Action/Observation loop
REACT_PROMPT = PromptTemplate.from_template("""You are a CI failure analysis agent.
You have access to tools to read and classify test failure logs.

Use this format strictly:

Thought: think about what to do next
Action: the tool name to use (one of: {tool_names})
Action Input: the input to the tool
Observation: the result of the tool
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to give a final answer
Final Answer: a JSON object summarising the failure analysis

Available tools:
{tools}

Task: {input}
{agent_scratchpad}""")


def build_executor(verbose: bool = True) -> AgentExecutor:
    """Build and return a configured AgentExecutor."""
    llm = get_llm()
    tools = [classify_log_file, classify_log_text, list_sample_logs]
    agent = create_react_agent(llm, tools, REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        max_iterations=6,
        handle_parsing_errors=True,
    )


def run_agent(task: str) -> dict:
    """Run the ReAct agent with a natural language task description."""
    executor = build_executor(verbose=True)
    result = executor.invoke({"input": task})
    output = result.get("output", "")
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"output": output}


if __name__ == "__main__":
    result = run_agent(
        "List the available sample log files, then classify the first one "
        "and tell me the root cause and fix hint."
    )
    print("\n=== AGENT FINAL RESULT ===")
    print(json.dumps(result, indent=2))
