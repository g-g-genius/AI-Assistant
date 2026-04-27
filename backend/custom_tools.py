from itertools import chain
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import retriever, tool
from langchain_core.prompts import ChatPromptTemplate, prompt
from langchain_core.output_parsers import JsonOutputParser
import requests

@tool
def search(query: str):
    """用于搜索实时信息，如天气、新闻、最新数据等。当用户询问需要实时数据的问题时，必须使用此工具。"""
    try:
        serp = SerpAPIWrapper()
        result = serp.run(query)
        print("实时搜索结果", result)
        return result
    except ImportError:
        return "Error: SerpAPI is not installed"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_info_from_local_db(query: str):
    """只有回答与2026年运势或者马年运势相关的问题的时候，会使用这个工具。"""
    client = Qdrant(
        QdrantClient(path="/local_qdrant"),
        "local_documents",
        OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    retriever = client.as_retriever(search_type="mmr")
    result = retriever._get_relevant_documents(query)
    return result

@tool
def bazi_cesuan(query: str):
    """只有做八字排盘的时候，会使用这个工具。需要输入用户姓名和出生年月日时，如果缺少用户姓名和出生年月日时则不可用"""
    url = f"https://api.yuanfenju.com/index.php/v1/Bazi/cesuan"
    prompt = ChatPromptTemplate.from_template(
        """
        你是一个参数查询助手，根据用户输入内容找出相关的参数并按json格式返回。
        JSON字段如下-"api_ke":"K0I5WCmce7jlMZzTw7vilxsno",
        - "name":"姓名"
        - "sex”:"性别，0表示男，1表示女，根据姓名判断"
        - "type”:"日历类型，0农历，1公历，默认1"
        - "year”:"出生年份 例: 1998"
        - "month”:"出生月份例8"
        - "day":"出生日期，例: 8"
        - "hour":"出生小时，例: 14"
        - "minute":"0"，如果没有找到相关参数，则需要提醒用户告诉你这些内容，只返回数据结构，不要有其他的评论
        用户输入:{query}
        """
    )
    parser = JsonOutputParser()
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    chain = prompt | parser
    data = chain.invoke({"query":query})
    print("八字查询结果:", data)
    result = requests.post(url, data=data) 
    if result.status_code == 200:
        print("返回数据:", result.json())
        try:
            json = result.json()
            returnstring = f"八字为：{json['data']['bazi_info']['bazi']}"
            return returnstring
        except:
            return "八字查询失败，可能是你忘记询问用户的姓名和出生年月日时"
    else:
        return "技术错误，请告诉用户稍后再试"