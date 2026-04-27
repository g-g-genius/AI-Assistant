from server import Master

# 创建Master实例
master = Master()

# 测试agent调用tools
query = "今天北京的天气怎么样"
print(f"测试查询: {query}")
result = master.run(query)
print(f"结果: {result}")
