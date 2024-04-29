import logging

from colorama import Fore, Style

from meadow.agent.schema import AgentMessage
from meadow.client.client import Client
from meadow.client.schema import ChatResponse, LLMConfig, ToolSpec

lgger = logging.getLogger(__name__)


def print_message(message: AgentMessage, from_agent: str, to_agent: str) -> None:
    """Print a message with color based on the agent."""
    if to_agent == "User":
        content = message.display_content
    else:
        content = message.content
    if from_agent == "User":
        color = Fore.GREEN
    elif from_agent == "Controller":
        color = Fore.BLUE
    else:
        color = Fore.RED
    to_print = f"{from_agent} -> {to_agent}: {content}"
    print(color + to_print + Style.RESET_ALL)


def has_termination_condition(content: str, termination_message: str) -> bool:
    """Check if the message is the termination message."""
    return content.strip().endswith(termination_message) or content.strip().startswith(
        termination_message
    )


async def generate_llm_reply(
    client: Client,
    messages: list[AgentMessage],
    tools: list[ToolSpec],
    system_message: AgentMessage,
    model: str = None,
    llm_config: LLMConfig = LLMConfig(),
    overwrite_cache: bool = False,
) -> ChatResponse:
    """Generate a reply using autogen.oai."""
    serialized_messages = [system_message.model_dump(include={"role", "content"})]
    serialized_messages += [m.model_dump(include={"role", "content"}) for m in messages]
    # for msg in serialized_messages[1:]:
    #     print(msg["role"], "-----", msg["content"])
    # print("*********")
    chat_response = await client.chat(
        messages=serialized_messages,
        tools=tools,
        model=model,
        seed=llm_config.seed,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        overwrite_cache=overwrite_cache,
    )
    # logger.info(
    #     "Ran model",
    #     prompts=serialized_messages,
    #     response=chat_response.choices[0].message,
    #     tools=serialized_tools,
    #     config=self._llm_config,
    # )
    return chat_response
