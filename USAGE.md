# MCP AutoGen 统一接口使用说明

## 快速开始

### 1. 启动服务

```bash
# 方式1: 使用启动脚本
python start_api.py

# 方式2: 直接使用uvicorn
python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 访问服务

- **API文档**: http://localhost:8000/docs
- **演示页面**: http://localhost:8000/
- **WebSocket**: ws://localhost:8000/ws/execute_task

### 3. 测试接口

```bash
# 运行测试脚本
python test_unified_api.py

# 或者使用测试客户端
python test_client.py
```

## 接口说明

### 统一接口 `/execute_task`

这是新的统一接口，将原来的多个步骤合并为一个接口调用：

**HTTP流式响应:**
```bash
curl -X POST "http://localhost:8000/execute_task" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "请帮我翻译这段文字：Hello, how are you?",
    "input_data": null
  }'
```

**WebSocket:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/execute_task');
ws.send(JSON.stringify({
    user_input: "请帮我翻译这段文字：Hello, how are you?",
    input_data: null
}));
```

### 响应格式

每个响应都是一个JSON对象，包含以下字段：

```json
{
    "status": "progress|success|error",
    "step": "步骤名称",
    "message": "描述信息",
    "data": "相关数据"
}
```

### 执行步骤

1. **导入工具** - 自动导入预定义工具
2. **解析需求** - 使用LLM解析用户输入
3. **决策工具** - 分析需要的工具组合
4. **生成工具** - 自动生成缺失的工具（如果需要）
5. **创建流水线** - 构建执行流水线
6. **执行流水线** - 执行具体任务
7. **验证结果** - 验证执行结果
8. **完成任务** - 返回最终结果

## 示例任务

### 文本翻译
```
请帮我翻译这段文字：Hello, how are you?
```

### 图片处理
```
请帮我处理这张图片，提取其中的文字并翻译成中文
```

### 代码生成
```
请帮我生成一个Python函数来计算斐波那契数列
```

## 优势

1. **简化调用**: 一个接口完成整个流程
2. **实时反馈**: 流式输出显示执行进度
3. **自动工具生成**: 缺失工具自动生成
4. **多种协议**: 支持HTTP和WebSocket
5. **向后兼容**: 保留原有接口

## 注意事项

1. 确保数据库连接正常
2. 配置正确的OpenAI API密钥
3. 确保tools.yaml文件存在
4. WebSocket适合长时间任务
5. HTTP流式适合短时间任务 