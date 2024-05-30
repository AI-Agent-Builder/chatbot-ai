import os

from utils import get_documents_from_file, create_db, create_chain_hist, process_chat
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationSummaryBufferMemory
import asyncio
from langchain_openai import ChatOpenAI
from charact import traits_dct,expertises_dct
from dotenv import load_dotenv

load_dotenv()
from test_db import postr


class Assistant:
    def __init__(self, ):

        self.vectorStore = None
        self.chat_history = []

        self.llm = self.create_llm()

        self.memory = ConversationSummaryBufferMemory(llm=self.llm, memory_key="chat_history", input_key="input")
        self.urls = []
        self.template = """ Your name is {name}.
            Your traits are {traits}. Use it during answers.
            Your expertises skills are {expertises}. Use it during answers.
        "Respond to the question based on the chat_history:
        Human: 
        {input}  

        Current conversation:
        {history}

        Answer:
        """

    def update_name(self, name):
        self.model_name = name

    async def update_traits(self, *traits):
        postgres_traits, _ = await postr()

        s = ''
        for trait in postgres_traits:
            if trait[0] in traits:
                s+=trait[1]
        # for key in traits:
        #     s+=traits_dct.get(key,'')
        self.traits = s

    async def update_expertise(self, *expertises):
        _, postgres_expertises = await postr()

        s = ''
        for expertise in postgres_expertises:
            if expertise[0] in expertises:
                s += expertise[1]
        # for key in expertises:
        #     s += expertises_dct.get(key,'')
        self.expertises = s

    async def update_url(self, *urls):
        self.urls = urls
       # print(self.urls)
        docs = await get_documents_from_file(*self.urls)
        self.vectorStore = await create_db(docs)

        self.hist_chain = await create_chain_hist(self.vectorStore, self.llm)

    def create_llm(self):
        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv('api_key'))
        return llm

    async def setup(self):

        if len(self.urls) != 0:
            docs = await get_documents_from_file(self.urls)
            self.vectorStore = await create_db(docs)

            self.hist_chain = await create_chain_hist(self.vectorStore, self.llm)
        else:
            self.hist_chain = await create_chain_hist(self.vectorStore, self.llm, mode='nothing', memory=self.memory)

    async def ask(self, user_input):
        if len(self.urls) != 0:
            response = await process_chat(self.hist_chain, user_input, self.chat_history, self.model_name, self.traits,
                                          self.expertises,)
        else:
            response = await process_chat(self.hist_chain, user_input, self.chat_history, self.model_name, self.traits,
                                          self.expertises, mode='nothing')

        self.chat_history.append(HumanMessage(content=user_input))

        self.chat_history.append(AIMessage(content=response))

        return response.strip()



if __name__ == "__main__":
    async def main():
        bot = Assistant()#'https://arxiv.org/pdf/1710.09829.pdf')
        bot.update_name('Jarwis')
        await bot.update_traits('Adaptive','Reliable')
        await bot.update_expertise('Innovation', 'Technology')
        await bot.setup()
        result1 = await bot.ask('Who is Elon Mask?')
        await bot.update_url('https://arxiv.org/pdf/1710.09829.pdf','https://ailab-ua.github.io/courses/resources/Attention_Vaswani_2017.pdf')

        result2 = await bot.ask('What is Your name? What are your traits? What is the Capsule?')
        return result1,result2
    print(asyncio.run(main()))


