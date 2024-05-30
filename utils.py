from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.llm import LLMChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

#os.environ['OPENAI_API_KEY'] = os.getenv('api_key')





async def get_documents_from_file(*urls):
    """
        The function extracts the text content from the file at the specified URL and splits it into fragments.

        Args:
            url/path (str): The URL of the file to process. Supported file formats:
                       - PDF (.pdf)
                       - XLSX (.xlsx)


        Returns:
            List[Document]: A list containing fragments of the extracted text content.

        """
    # Choosing a loader depending on the file format
    docs = []
    for url in urls:

        if url.endswith('pdf'):
            loader = PyPDFLoader(url)
            try:
                docs = loader.load() + docs
            except Exception as error:
                raise f"Error uploading the file: {error}"
        else:
            loader = UnstructuredExcelLoader(url)
            try:
                docs = loader.load() + docs
            except Exception as error:
                raise f"Error uploading the file: {error}"


        #Read file contents




    # Splitting text into fragments
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )

    splitDocs = splitter.split_documents(docs)
    # print(splitDocs)
    return splitDocs



async def create_db(docs):
    """
        The function creates a database of vectors from a list of documents.

        Args:
            docs (List[Document]): List of documents.

        Returns:
            vectorStore: A FAISS object containing document vectors.

        """
    # Loading the Hugging Face Model
    #try:
    #embedding = HuggingFaceEmbeddings(model_kwargs={'device': 'cpu'})
    embedding = OpenAIEmbeddings(api_key=os.getenv('api_key'))
    #except Exception as error:
    #    return f"Error loading Hugging Face model: {error}"


    # Creating a FAISS database
    #try:
    vectorStore = await FAISS.afrom_documents(docs, embedding=embedding)
    #except Exception as error:
    #    raise f"Error when creating the FAISS database: {error}"


    return vectorStore


async def create_chain_hist(vectorStore, llm, mode='context', memory=None):
    """
            the function returns a chain with a history.

            Args:
                vectorStore (FAISS object): database

            Returns:
                 CallablePipeline: retrieval_chain.
            """
    model = llm
    if mode == 'context':
        prompt = ChatPromptTemplate.from_template(
            """ Your name is {name}.
                Your traits are '{traits}'. Use it during answers.
                Your expertises skills are '{expertises}'. Use it during answers.
            "Answer the user's questions based on the context and chat_history.": 
            Context:
            {context}

            Chat_history:
            {chat_history}

            Question:
            {input}

            Answer:
            """)

        chain = create_stuff_documents_chain(
            llm=model,
            prompt=prompt
        )

        # Replace retriever with history aware retriever
        retriever = vectorStore.as_retriever(search_kwargs={"k": 7})

        retriever_prompt = ChatPromptTemplate.from_template(
            """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone 
                question.

            Chat_history:
            {chat_history}

            Input:
            {input}

            Answer:
            """)

        history_aware_retriever = create_history_aware_retriever(
            llm=model,
            retriever=retriever,
            prompt=retriever_prompt,

        )

        # retriever, Replace with History Aware Retriever
        retrieval_chain = create_retrieval_chain(

            history_aware_retriever,
            chain
        )
    else:
        prompt = ChatPromptTemplate.from_template(
            """ Your name is {name}.
                Your traits are {traits}. Use it during answers.
                Your expertises skills are {expertises}. Use it during answers.
            "Answer the user's questions based on the chat_history. Never say that you are a bot unless you are directly asked about it.": 


            Question:
            {input}

            Chat_history:
            {chat_history}

            Answer:
            """)
        retrieval_chain = LLMChain(llm=model, prompt=prompt, memory=memory)

    return retrieval_chain




async def process_chat(chain, question, chat_history, name, traits, expertises, mode='context'):
    response = await chain.ainvoke({
        'expertises': expertises,
        'traits': traits,
        'name': name,
        "chat_history": chat_history,
        "input": question,
    })
    if mode == 'context':
        return response["answer"]
    return response['text']