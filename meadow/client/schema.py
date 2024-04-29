"""Language model request object."""

import json
from typing import Any, Literal

from pydantic import BaseModel, model_serializer

Role = Literal["assistant", "user", "system"]


class FunctionArgSpec(BaseModel):
    """A function argument spec."""

    name: str
    description: str
    type: str
    required: bool


class ToolSpec(BaseModel):
    """A LLM tool call spec.

    Passed as input to the LLM call.
    """

    name: str
    description: str
    function_args: list[FunctionArgSpec]

    @model_serializer
    def serialize_for_llm(self) -> dict[str, Any]:
        """Construct the message for LLM."""
        tool_dict: dict[str, Any] = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
        for arg in self.function_args:
            if arg.type.startswith("array"):
                subtype = arg.type.split("[")[1].split("]")[0]
                type_abj = {"type": "array", "items": {"type": subtype}}
            else:
                type_abj = {"type": arg.type}
            tool_dict["function"]["parameters"]["properties"][arg.name] = {
                "description": arg.description,
                **type_abj,
            }
            if arg.required:
                tool_dict["function"]["parameters"]["required"].append(arg.name)
        return tool_dict


class ToolCall(BaseModel):
    """Model response for which tool to call."""

    """
    The arguments to call the function with, as generated by the model in JSON
    format. Note that the model does not always generate valid JSON.
    """
    unparsed_arguments: str

    """The name of the function to call."""
    name: str

    @property
    def arguments(self) -> dict[str, Any]:
        """The arguments to call the function with."""
        try:
            return json.loads(self.unparsed_arguments)
        except json.JSONDecodeError:
            return {}


class ChatMessage(BaseModel):
    """The contents of the message."""

    content: str | None = None

    """The role of the author of this message."""
    role: Role

    """The tool calls generated by the model."""
    tool_calls: list[ToolCall] | None = None


class LLMConfig(BaseModel):
    """LLM configuration parameters.

    We keep as many parameters None as possible to let the client APIs define
    defaults."""

    """Seed."""
    seed: int | None = None

    """Temperature for generation."""
    temperature: float | None = None

    """Max tokens for generation."""
    max_tokens: int | None = None

    """Nucleus sampling taking top_p probability mass tokens."""
    top_p: float | None = None

    """Top k sampling taking top_k highest probability tokens."""
    top_k: int | None = None

    """Stop sequences."""
    stop: list[str] | None = None

    """Penalize resence."""
    presence_penalty: float | None = None

    """Penalize frequency."""
    frequency_penalty: float | None = None

    """Response format
    { "type": "json_object" } for JSON output."""
    response_format: dict[str, str] | None = None


class ChatRequest(LLMConfig):
    """Request object."""

    """Chat prompt."""
    messages: list[dict[str, str]]

    """Engine."""
    model: str

    """Number responses."""
    n: int = 1

    """Tools."""
    tools: list[ToolSpec] | None = None


class Usage(BaseModel):
    """Number of tokens in the generated completion."""

    completion_tokens: int

    """Number of tokens in the prompt."""
    prompt_tokens: int

    """Total number of tokens used in the request (prompt + completion)."""
    total_tokens: int


class Choice(BaseModel):
    """A single text response made by the model."""

    """The index of the choice in the list of choices."""
    index: int

    """A chat completion message generated by the model."""
    message: ChatMessage


class ChatResponse(BaseModel):
    """Chat completion response modelled from OpenAI."""

    """A unique identifier for the chat completion."""
    id: str

    """Whether the response was retrieved from the cache."""
    cached: bool

    """A list of chat completion choices.

    Can be more than one if `n` is greater than 1.
    """
    choices: list[Choice]

    """The Unix timestamp (in seconds) of when the chat completion was created."""
    created: int

    """The model used for the chat completion."""
    model: str

    """Usage statistics for the completion request."""
    usage: Usage | None = None
