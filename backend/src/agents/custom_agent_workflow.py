import os, json
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext
)
from llama_index.core.tools import (
    QueryEngineTool,
    ToolMetadata
)
from llama_index.core.workflow import (
    step,
    Context,
    Workflow,
    Event,
    StartEvent,
    StopEvent
)
from llama_index.core.agent import ReActAgent, FunctionCallingAgent
from llama_index.llms.openai import OpenAI
from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core.node_parser import SentenceSplitter

from agents.llama_index_agent import ControlledFunctionTool
from agents.utils import clear_all_index_cache, create_index_cache, load_cached_index, is_index_cached
from helpers.slack_helper import post_to_slack

from llama_index.embeddings.openai import OpenAIEmbedding, OpenAIEmbeddingModelType
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage

from dotenv import load_dotenv
load_dotenv()

llm = OpenAI(model=os.getenv("OPENAI_MODEL"))
embed_model = OpenAIEmbedding(model=OpenAIEmbeddingModelType.TEXT_EMBED_3_SMALL)
Settings.embed_model = embed_model
Settings.llm = llm



class QueryEvent(Event):
    question: str

class AnswerEvent(Event):
    question: str
    answer: str

class ActionEvent(Event):
    instructions: str
    combined_answer: str

class SubQuestionQueryEngine(Workflow):

    @step(pass_context=True)
    async def query(self, ctx: Context, ev: StartEvent) -> QueryEvent:
        if (hasattr(ev, "query")):
            ctx.data["original_query"] = ev.query
            print(f"Query is {ctx.data['original_query']}")

        if (hasattr(ev, "llm")):
            ctx.data["llm"] = ev.llm

        if (hasattr(ev, "tools")):
            ctx.data["tools"] = ev.tools

        response = ctx.data["llm"].complete(f"""
            Given a user question, and a list of tools, output a list of
            relevant sub-questions and special instructions, such that the answers to all the
            sub-questions put together will answer the question.
            Identify and specify any special instructions unique to this query that may guide tool usage, such as post the results, add to my calender, etc. Avoid general instructions like summarizing or simply answering the question.
                                                                                        
            If the user question is a simple question then the user question itself can be a sub-question. 
            If the user question is a combination of questions, then divide each question as relevant sub-question.
            If the user question is a complex question, then use your knowledge to break it down into relevant sub-questions.
            Always list the least possible number of question to the given user query.    
            
            Respond in pure JSON without any markdown, like this:
            {{
                "sub_questions": [
                    "What is the population of San Francisco?",
                    "What is the budget of San Francisco?",
                    "What is the GDP of San Francisco?"
                ],
                "special_instructions":[
                    "post the results to twitter"    
                ],    
            }}
            Here is the user question: {ctx.data['original_query']}

            And here is the list of tools: {ctx.data['tools']}
            """)

        print(f"Sub-questions & Instructions are {response}")

        response_obj = json.loads(str(response))
        sub_questions = response_obj["sub_questions"]
        spl_instructions = response_obj["special_instructions"]

        ctx.data["sub_question_count"] = len(sub_questions)
        ctx.data["instructions_count"] = len(spl_instructions)
        ctx.data["spl_instructions"] = spl_instructions
        
        for question in sub_questions:
            self.send_event(QueryEvent(question=question))

        return None

    @step(pass_context=True)
    async def sub_question(self, ctx: Context, ev: QueryEvent) -> AnswerEvent:
        print(f"Sub-question is {ev.question}")

        agent = FunctionCallingAgent.from_tools(
            ctx.data["tools"], 
            llm=ctx.data["llm"], 
            verbose=True, 
            )
        response = agent.chat(ev.question)

        return AnswerEvent(question=ev.question,answer=str(response))

    @step(pass_context=True)
    async def combine_answers(self, ctx: Context, ev: AnswerEvent) -> ActionEvent | None | StopEvent:
        ready = ctx.collect_events(ev, [AnswerEvent]*ctx.data["sub_question_count"])
        if ready is None:
            return None

        answers = "\n\n".join([f"Question: {event.question}: \n Answer: {event.answer}" for event in ready])

        prompt = f"""
            You are given an overall question that has been split into sub-questions,
            each of which has been answered.
            
            If the original question is a simple question, then just output the json question and answer pair. 
            If the original question is a combination of questions, then just output the json Sub-questions and answers pairs. 
            If the original question is a complex question, then use 'Sub-questions and answers' to answer the original complex question and return json original question & answer pair.

            Original question: {ctx.data['original_query']}

            Sub-questions and answers:
            {answers}
        """

        print(f"Final prompt is {prompt}")

        response = ctx.data["llm"].complete(prompt)

        print("Final response is", response)
        if ctx.data["spl_instructions"]:
            instructions = str(ctx.data["spl_instructions"])
            return ActionEvent(instructions=instructions, combined_answer=str(response))
        else:
            return StopEvent(result=str(response))
    
    @step(pass_context=True)
    async def execute_instructions(self, ctx: Context, ev: ActionEvent) -> StopEvent:
        
        agent = FunctionCallingAgent.from_tools(
            ctx.data["tools"], 
            llm=ctx.data["llm"], 
            verbose=True, 
            )
        prompt = f"""
            Having the combined answer already deduced, follow the given special instructions.
            {ev.instructions}

            Combined Answer:
            {ev.combined_answer}

        """
        response = agent.query(prompt)

        return StopEvent(result=str(response))
    

async def process_custom_agent_request(request_id: str, user_id: str, file: str, user_query: str):
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
        description="This is the tool to helpful for answering a single question at a time on the provided document.",
        return_direct=True
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

    custom_tools = [doc_vector_tool, slack_post_tool]

    engine = SubQuestionQueryEngine(timeout=120, verbose=True)

    result = await engine.run(
        llm=llm,
        tools=custom_tools,
        query=user_query
    )

    return result