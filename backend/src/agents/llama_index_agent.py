from llama_index.core import VectorStoreIndex
from llama_index.core.agent import AgentRunner, FunctionCallingAgentWorker
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding, OpenAIEmbeddingModelType
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core import Settings
from llama_index.core.tools import ToolOutput
from llama_index.core.llms import ChatMessage
from agents.utils import clear_all_index_cache, create_index_cache, load_cached_index, is_index_cached
from helpers.slack_helper import post_to_slack

import os
from typing import Optional, List, Any
from dotenv import load_dotenv
load_dotenv()

import nest_asyncio
nest_asyncio.apply()


llm = OpenAI(model=os.getenv("OPENAI_MODEL"))
embed_model = OpenAIEmbedding(model=OpenAIEmbeddingModelType.TEXT_EMBED_3_SMALL)
Settings.embed_model = embed_model
Settings.llm = llm


class ControlledFunctionTool(FunctionTool):

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
            """Call."""
            tool_output = self._fn(*args, **kwargs)
            if tool_output.source_nodes:
                score = max([node.score for node in tool_output.source_nodes])
                if score < 0.25: # The threshould for relavent info in document found or not
                    tool_output.response = "Data Not Available"
            
            return ToolOutput(
                content=str(tool_output),
                tool_name=self.metadata.name,
                raw_input={"args": args, "kwargs": kwargs},
                raw_output=tool_output,
            )


def process_agent_request(request_id: str, user_id: str, file: str, user_query: str):
    """
    This function takes the request id, document & query. Returns the generated response from the agent.
    """
    
    if is_index_cached(file):
        index = load_cached_index(file=file)
    else:
        documents = SimpleDirectoryReader(input_files=[file]).load_data()
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        nodes = splitter.get_nodes_from_documents(documents)
        index = VectorStoreIndex(
            nodes=nodes,
        )
        create_index_cache(index=index, file=file)
        

    def vector_query(
        query: str
    ) -> str:
        """Use to answer questions over a given document.
    
        Useful if you have specific questions over the document.
    
        Args:
            query (str): the string query to be embedded.        
        """
           
        query_engine = index.as_query_engine(
            similarity_top_k=2,
        )
        response = query_engine.query(query)
        return response
    
    doc_vector_tool = ControlledFunctionTool.from_defaults(
        fn=vector_query,
        name="document_vector_tool",
        description="This is the tool to helpful for answering a single question at a time on the provided document."
    )

    def post_to_slack_override(message: str):
        """
        Useful for posting a message onto the slack channel.
        Args:
            message (str): The message that needs to be posted into the slack channel.  
        """
        post_to_slack(message=message, user_id=user_id, request_id=request_id)

    slack_post_tool = FunctionTool.from_defaults(
        fn=post_to_slack_override,
        name="Slack_post_tool",
        description="This is a tool helpul for posting a message onto the slack channel."
    )

    prefix_messages = [
        ChatMessage(
                role="system",
                content=(
                    f"You are now an agent answering to the questions one by one, only pertaining to the provided indexed document. "
                    "Only answer the questions that the user has explicitly provided. "
                    "The final response should be a json with indivudual questions as keys and the corresponding function output as value. "
                    "You should also be able to post the results to external channels if asked to do so."
                    "Do not make up any details."
                ),
            )
        ]
    
    agent_worker = FunctionCallingAgentWorker.from_tools(
        [doc_vector_tool, slack_post_tool],
        verbose=True,
        prefix_messages=prefix_messages
    )
    agent = AgentRunner(agent_worker)

    task = agent.create_task(user_query)
    step_output = agent.run_step(task.task_id)
    while True:
        if step_output.is_last:
            break
        step_output = agent.run_step(task.task_id)
    response = step_output
    return response