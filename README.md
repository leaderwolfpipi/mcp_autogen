# 构建镜像
docker build -t mcp-autogen .

# 运行容器
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key mcp-autogen

# 访问API文档
curl http://localhost:8000/docs