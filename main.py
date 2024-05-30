from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from model import Assistant
from test_db import postr
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)
chats ={}
summary = {}

@app.get("/start")
async def start(chat_id : str):
    # try:

    chats[chat_id] = Assistant()
    result = await chats[chat_id].setup()

    return {"message": result}

@app.get('/get_traits')
async def get_traits():
    postgres_traits, _ = await postr()

    traits_dct = {}

    for trait in postgres_traits:
            traits_dct[trait[0]]=trait[1]
    return traits_dct


@app.get('/get_expertises')
async def get_expertises():
    _, postgres_expertises = await postr()

    expertises_dct = {}

    for expertise in postgres_expertises:

        expertises_dct[expertise[0]] = expertise[1]
    return expertises_dct




@app.get('/ask')
async def ask(chat_id : str,question):
    response = await chats[chat_id].ask(question)

    return {"message": response}

# @app.get('/test')
# async def upd(**kwargs:str):
#
#     return {'answer':kwargs.values()}

@app.get('/update_name')
async def upd_name(chat_id : str,name):
    chats[chat_id].update_name(name)
    return {'message': 'name is created.'}



@app.get('/update_traits')
async def upd_traits(chat_id : str ,traits : str):
    traits = traits.split(',')
    summary['traits']=traits
   # print(traits)
    await chats[chat_id].update_traits(*traits)
    return {'message': 'traits were added.'}



@app.get('/update_expertise')
async def upd_expertise(chat_id : str,expertise : str):
    expertise = expertise.split(',')
    summary['expertise'] = expertise
    await chats[chat_id].update_expertise(*expertise)
    return {'message': 'expertises were added.'}



@app.get('/update_url')
async def upd_url(chat_id : str,urls : str):
    urls = urls.split(',')
    summary['urls']=urls
    #print(*urls)
    await chats[chat_id].update_url(*urls)
    return {'message': 'urls were added.'}


@app.get('/get_summary')
async def get_sum():
    return summary


@app.get("/del_chat")
async def del_history(chat_id : str):
    #try:
    del chats[chat_id]
    summary.clear()
    return {'message': 'chat was deleted'}


