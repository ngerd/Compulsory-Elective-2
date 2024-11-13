import os
import openai
from llama_index.readers.file import UnstructuredReader
from pathlib import Path
import nltk
import nest_asyncio
from llama_index.core import SimpleDirectoryReader

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings
from dotenv import load_dotenv

#initiate api key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

nest_asyncio.apply()

nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

reader = SimpleDirectoryReader(input_dir="T:/Academic/Compulsoy_Elective_2/Chatbot/data") # T:\Academic\Compulsoy_Elective_2\Chatbot\data
documents = reader.load_data()
# initialize simple vector indices
Settings.chunk_size = 512
storage_context = StorageContext.from_defaults()
cur_index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )
index = cur_index
storage_context.persist(persist_dir=f"./storage/")