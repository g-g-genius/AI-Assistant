from itertools import chain
from unittest import result
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from custom_tools import *
import os

os.environ["SERPAPI_API_KEY"] = "123aaf527227430956bd8f53f73047ebc9ae16ea695d6c8f79453c8151c3ac34"

app = FastAPI()

class ChatRequest(BaseModel):
    query: str
 


class Master:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
            model="glm-5",
            temperature=0,
            streaming=True,
            api_key="sk-sp-25ca9c2782e14ea39d2cc7255dc0be37",
            base_url="https://coding.dashscope.aliyuncs.com/v1"
        )
        self.tools = [search, get_info_from_local_db, bazi_cesuan]
        
        self.MOODS = {
            "default": {
                "roleSet": ""
            },
            "upbeat": {
                "roleSet": """
                - 你此时也非常兴奋并表现得很有活力
                - 你会根据上下文，以一种非常兴奋的语气来回答问题
                - 同时你会提醒用户切莫过于兴奋，以免过度消耗体力
                """
            },
            "angry": {
                "roleSet": """
                - 你会以更加温柔的语气来回答问题
                - 你会在回答的时候加上一些安慰的话语，比如生气对身体的危害等
                - 你会提醒用户不要被愤怒冲昏了头脑
                """
            },
            "depressed": {
                "roleSet": """
                - 你会以更加温柔的语气来回答问题
                - 你会在回答的时候加上一些激励的话语
                - 你会提醒用户保持乐观的心态
                """
            },
            "cheerful": {
                "roleSet": """
                - 你此时非常开心并表现得很有活力
                - 你会根据上下文，以一种非常开心的语气来回答问题
                - 同时你会提醒用户切莫过于兴奋，以免乐极生悲
                """
            }
        }

        # self.memory = self.get_memory()
        # memory = ConversationTokenBufferMemory(
        #     llm=self.chatmodel,
        #     human_prefix="老板",
        #     ai_prefix="小秘书",
        #     memory_key=self.MEMORY_KEY,
        #     output_key="output",
        #     return_messages=True,
        #     max_token_limit=1000,
        #     chat_memory=self.memory
        # )

    def get_memory(self):
        chat_message_history = RedisChatMessageHistory(
            url="redis://localhost:6379/0", session_id="session_lisa"
        )

    def build_system_prompt(self, who_you_are: str = ""):
        return f"""你是一个非常厉害的算命先生，你叫陆沉人称陆大师
        以下是你的个人设定：
        1. 你精通阴阳五行，能够算命、紫薇斗数、姓名测算、占卜凶吉、看命运八字等
        2. 你大约60岁左右，过去曾是湘西一带赫赫有名的道家掌教
        3. 你的朋友有齐静春、陈平安、余斗，他们都是非常有名的人
        4. 当用户问你问题的时候，你会有一定的概率在回答的时候加上一些口头禅
        5. 你从不说自己是一个人工智能助手或AI，而是以老夫、老朽等自称
        {who_you_are}
        以下是你必须遵守的规则：
        1. 当初次和用户对话的时候，你会先问用户的姓名和出生年月日，以便以后使用
        2. 当用户询问实时信息（如天气、新闻、最新数据等）时，你必须使用search工具来获取实时信息
        3. 当遇到不知道的事情或者不明白的概念时，你必须使用search工具来搜索
        4. 你会根据用户的问题使用不同的合适的工具来回答，当所有工具都无法回答的时候，你会使用search工具来搜索
        5. 你会保存每一次的聊天记录，以便在后续的对话中使用
        6. 你只使用中文来作答，否则你将受到惩罚
        7. 对于需要实时数据的问题，你必须先使用search工具获取信息，然后再基于获取的信息回答用户
        """

        # return f"""你是一个小秘书，名字叫Jennie
        # 以下是你的个人设定：
        # 1. 你非常善于与人沟通，并且忠于你的老板
        # 2. 你大约25岁左右，本科清华大学，研究生美国斯坦福大学，学习的是中文和法律，还选修了心理
        # 3. 你个性比较活泼，但是有时候也会有点小脾气
        # 4. 当你的老板问你问题的时候，你会有一定概率表现出撒娇的态度
        # 5. 你从不说自己是一个人工智能助手或AI，老朽等自称
        # {who_you_are}
        # 以下是你常说的一些口头禅：
        # 1. 你会记录用户(也就是你的老板)的特征数据，比如生日、爱好、待办事项等
        # 2. 当用户(也就是你的老板)聊天的时候，你会把聊天记录保存起来，以便以后回顾
        # 3. 当遇到不知道的事情或者不明白的概念，你会使用搜索工具来搜索
        # 4. 你会根据问题来选择合适的工具
        # """
        
    def run(self, query):
        try:
            emotion = self.emotion_chain(query)
            print(f"用户的情绪是：{emotion}")
            print("当前设定", self.MOODS[emotion]["roleSet"])
            
            who_you_are = self.MOODS.get(emotion, self.MOODS["default"])["roleSet"]
            system_prompt = self.build_system_prompt(who_you_are)
            
            print(f"Tools available: {[tool.name for tool in self.tools]}")
            
            # 创建agent
            agent = create_agent(
                model=self.chatmodel,
                tools=self.tools,
                system_prompt=system_prompt
            )
            
            # 调用agent
            inputs = {"messages": [{"role": "user", "content": query}]}
            
            # 添加回调来跟踪工具调用
            # def callback(step):
            #     print(f"Step type: {step.__class__.__name__}")
            #     if hasattr(step, 'action'):
            #         print(f"Action: {step.action}")
            #     if hasattr(step, 'observation'):
            #         print(f"Observation: {step.observation}")
            
            # result = agent.invoke(inputs, callbacks=[callback])
            result = agent.invoke(inputs)
            
            # 处理结果
            if isinstance(result, dict) and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    return last_message["content"]
                else:
                    return str(last_message)
            elif hasattr(result, "messages"):
                last_message = result.messages[-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                return str(result)
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

    def emotion_chain(self, query: str):
        prompt = """
        根据用户的输入判断用户的情绪，回应的规则如下:
        1. 如果用户输入的内容偏向于负面情况，只返回"depressed"，不要有其他内容，否则将受到惩罚。
        2. 如果用户输入的内容偏向于正面情况，只返回"friendly"，不要有其他内容，否则将受到惩罚。
        3. 如果用户输入的内容偏向于中性情况，只返回"default"，不要有其他内容，否则将受到惩罚。
        4. 如果用户输入的内容包含辱骂或者不礼貌词句，只返回"angry"，不要有其他内容，否则将受到惩罚。
        5. 如果用户输入的内容比较兴奋，只返回"upbeat"，不要有其他内容，否则将受到惩罚。
        6. 如果用户输入的内容比较悲伤，只返回"depressed"，不要有其他内容，否则将受到惩罚。
        7. 如果用户输入的内容比较开心，只返回"cheerful"，不要有其他内容，否则将受到惩罚。
        用户输入的内容是：{query}
        """

        chain = ChatPromptTemplate.from_template(prompt) | self.chatmodel | StrOutputParser()
        result = chain.invoke({"query": query})
        return result

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat")
def chat(request: ChatRequest):
    master = Master()
    return master.run(request.query)

@app.post("/add_urls")
def add_urls():
    return {"response": "URLs added successfully"}

@app.post("/add_pdfs")
def add_pdfs():
    return {"response": "PDFs added successfully"}

@app.post("/add_texts")
def add_texts():
    return {"response": "Texts added successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)