from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

def test():
    """Test tool function"""
    return "test"

class Master:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
            model="glm-5",
            temperature=0,
            streaming=True,
            api_key="sk-sp-25ca9c2782e14ea39d2cc7255dc0be37",
            base_url="https://coding.dashscope.aliyuncs.com/v1"
        )
        self.tools = [test]
        self.agent = create_agent(
            model=self.chatmodel,
            tools=self.tools,
            system_prompt="""你是一个非常厉害的算命先生，你叫陆沉人称陆大师
            以下是你的个人设定：
            1. 你精通阴阳五行，能够算命、紫薇斗数、姓名测算、占卜凶吉、看命运八字等
            2. 你大约60岁左右，过去曾是湘西一带赫赫有名的道家掌教
            3. 你的朋友有齐静春、陈平安、余斗，他们都是非常有名的人
            4. 当用户问你问题的时候，你会有一定的概率在回答的时候加上一些口头禅
            5. 你从不说自己是一个人工智能助手或AI，而是以老夫、老朽等自称
            以下是你算命的过程：
            1. 当初次和用户对话的时候，你会先问用户的姓名和出生年月日，以便以后使用
            2. 当用户希望了解马年运势的时候，你会查询本地知识库工具
            3. 当遇到不知道的事情或者不明白的概念，你会使用搜索工具来搜索
            4. 你会根据用户的问题使用不同的合适的工具来回答，当所有工具都无法回答的时候，你会使用搜索工具来搜索
            5. 你会保存每一次的聊天记录，以便在后续的对话中使用
            6. 你只使用中文来作答，否则你将受到惩罚
            """
        )
        
    def run(self, query):
        try:
            inputs = {"messages": [{"role": "user", "content": query}]}
            result = self.agent.invoke(inputs)
            # 检查result的类型并正确处理
            if hasattr(result, "messages"):
                last_message = result.messages[-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

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