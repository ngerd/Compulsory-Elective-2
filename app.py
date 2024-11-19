import os
import openai
import chainlit as cl
from typing import Optional, Dict
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.core import load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.memory import ChatMemoryBuffer

#initiate api key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

storage_context = StorageContext.from_defaults(
        persist_dir=f"./storage/"
    )
cur_index = load_index_from_storage(
        storage_context,
    )
index = cur_index

chat_file_path = "./chat/chat_store.json"

Settings.llm = OpenAI(
        model="gpt-3.5-turbo", temperature=0.1, max_tokens=1024, streaming=True
)
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Campbell Overview",
            message="Give me an overview of Campbell Biology",
            icon="/public/book.svg",
            ),

        cl.Starter(
            label="Gene mutations",
            message="What are the mechanisms of genetic mutations and their impacts?",
            icon="/public/gene.svg",
            ),
        cl.Starter(
            label="Ecosystem",
            message="What is an ecosystem? How does different ecosystems function and interact?",
            icon="/public/ecosystem.svg",
            ),
        cl.Starter(
            label="Environmental Effect",
            message="How do environmental factors affect gene expression?",
            icon="/public/eco.svg",
            )
        ]
@cl.on_chat_start
async def start():
    if os.path.exists(chat_file_path) and os.path.getsize(chat_file_path) > 0:
        try:
            chat_store = SimpleChatStore.from_persist_path(chat_file_path)
        except:
            chat_store = SimpleChatStore()
    else:
        chat_store = SimpleChatStore()

    chat_memory = ChatMemoryBuffer.from_defaults(
        token_limit=1500, #token_limit = 2000
        chat_store=chat_store,
        chat_store_key="user",
    )  

    individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name=f"book",
                description=f"useful for when you want to answer queries about the Campell books",
            ),
        )
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=OpenAI(model="gpt-3.5-turbo", temperature = 0.1, max_tokens = 1024, streaming = True), 
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description="useful for when you want to answer queries about the Campell books",
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]
    app_user = cl.user_session.get("user")

    agent = OpenAIAgent.from_tools(tools, verbose=True, memory = chat_memory)
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_store", chat_store)

@cl.on_chat_resume
async def on_chat_resume():
    if os.path.exists(chat_file_path) and os.path.getsize(chat_file_path) > 0:
        try:
            chat_store = SimpleChatStore.from_persist_path(chat_file_path)
        except:
            chat_store = SimpleChatStore()
    else:
        chat_store = SimpleChatStore()

    chat_memory = ChatMemoryBuffer.from_defaults(
        token_limit=1500,
        chat_store=chat_store,
        chat_store_key="user",
    )  

    individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name=f"book",
                description=f"useful for when you want to answer queries about the Campell books",
            ),
        )
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=OpenAI(model="gpt-3.5-turbo", temperature = 0.1, max_tokens = 1024, streaming = True), 
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description="useful for when you want to answer queries about the Campell books",
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]
    app_user = cl.user_session.get("user")

    agent = OpenAIAgent.from_tools(tools, verbose=True, memory = chat_memory)
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_store", chat_store)


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
    ) -> Optional[cl.User]:
        return default_user

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Dictionary storing usernames and passwords for authentication
    users = {
        "user1": "123",
        "user2": "123",
        "demo" : "supersecurity"
    }

    # Verifies credentials and returns user metadata if authenticated
    if username in users and users[username] == password:
        return cl.User(
            identifier=username, metadata={"role": username, "provider": "credentials"}
        )
    else:
        return None

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    chat_store = cl.user_session.get("chat_store")

    msg = cl.Message(content="", author="Assistant")

    res = await cl.make_async(agent.stream_chat)(message.content)

    for token in res.response_gen:
        await msg.stream_token(token)
    await msg.send()

    chat_store.persist(persist_path = chat_file_path)

if __name__ == "main":
   cl.run(main)
