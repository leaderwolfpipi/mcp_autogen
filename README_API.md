# MCP AutoGen API 使用说明

## 概述

MCP AutoGen API 提供了一个统一的任务执行接口，支持流式输出，可以同时处理需求解析、工具生成、流水线创建和执行等完整流程。

## 新功能特性

### 1. 统一接口 `/execute_task`

将原来的多个接口（需求解析、流水线生成、执行）合并为一个接口，用户只需要提供任务描述，系统会自动完成整个流程。

### 2. 流式输出支持

- **HTTP流式响应**: 使用 `StreamingResponse` 实现实时进度反馈
- **WebSocket支持**: 提供实时双向通信，支持长时间任务

### 3. 自动工具生成

当检测到缺失工具时，系统会自动生成相应的工具代码并注册到数据库中。

## API 接口

### 1. HTTP 流式接口

**POST** `/execute_task`

**请求体:**
```json
{
    "user_input": "请帮我翻译这段文字：Hello, how are you?",
    "input_data": null
}
```

**响应格式:**
```
{"status": "progress", "step": "import_tools", "message": "正在导入工具集合...", "data": null}
{"status": "progress", "step": "parse_requirement", "message": "正在解析用户需求...", "data": null}
{"status": "progress", "step": "requirement_parsed", "message": "需求解析完成", "data": {...}}
...
{"status": "success", "step": "completed", "message": "任务执行完成", "data": {...}}
```

### 2. WebSocket 接口

**WebSocket URL:** `ws://localhost:8000/ws/execute_task`

**发送消息:**
```json
{
    "user_input": "请帮我翻译这段文字：Hello, how are you?",
    "input_data": null
}
```

**接收消息格式:** 与HTTP流式响应相同

### 3. 演示页面

访问 `http://localhost:8000/` 可以看到Web界面演示。

## 使用示例

### Python 客户端示例

```python
import requests
import json

# HTTP流式请求
def execute_task_http(user_input):
    url = "http://localhost:8000/execute_task"
    payload = {"user_input": user_input, "input_data": None}
    
    response = requests.post(url, json=payload, stream=True)
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            print(f"[{data['step']}] {data['message']}")
            if data['status'] in ['success', 'error']:
                break

# 使用示例
execute_task_http("请帮我翻译这段文字：Hello, how are you?")
```

### JavaScript WebSocket 示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/execute_task');

ws.onopen = () => {
    console.log('WebSocket连接成功');
    
    // 发送任务
    ws.send(JSON.stringify({
        user_input: "请帮我翻译这段文字：Hello, how are you?",
        input_data: null
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`[${data.step}] ${data.message}`);
    
    if (data.status === 'success') {
        console.log('任务完成:', data.data);
    }
};
```

## 执行步骤说明

1. **导入工具** (`import_tools`): 自动导入预定义的工具集合
2. **解析需求** (`parse_requirement`): 使用LLM解析用户输入为结构化需求
3. **需求解析完成** (`requirement_parsed`): 返回解析后的需求结构
4. **决策工具** (`decide_tools`): 分析需求并决定需要的工具组合
5. **工具决策完成** (`tools_decided`): 返回工具决策方案
6. **生成工具** (`generate_tools`): 如果缺少工具，开始自动生成
7. **生成工具中** (`generating_tool`): 正在生成特定工具
8. **工具生成完成** (`tool_generated`): 工具代码生成完成
9. **工具注册完成** (`tool_registered`): 工具已注册到数据库
10. **重新决策完成** (`tools_redecided`): 重新评估工具组合
11. **生成流水线** (`compose_pipeline`): 创建执行流水线
12. **流水线生成完成** (`pipeline_composed`): 流水线创建完成
13. **执行流水线** (`execute_pipeline`): 开始执行流水线
14. **流水线执行完成** (`pipeline_executed`): 流水线执行完成
15. **验证结果** (`validate_result`): 验证执行结果
16. **任务完成** (`completed`): 整个任务执行完成

## 状态说明

- `progress`: 执行中
- `success`: 执行成功
- `error`: 执行失败

## 向后兼容

原有的接口仍然保留：
- `POST /parse_requirement` - 需求解析
- `POST /generate_pipeline` - 生成流水线
- `POST /execute_pipeline` - 执行流水线
- `GET /tools` - 列出工具
- `POST /register_tool` - 注册工具

## 启动服务

```bash
# 启动API服务
python -m uvicorn api.api:app --host 0.0.0.0 --port 8000

# 访问API文档
curl http://localhost:8000/docs

# 访问演示页面
curl http://localhost:8000/
```

## 注意事项

1. 确保数据库连接正常
2. 配置正确的OpenAI API密钥
3. 确保tools.yaml文件存在且格式正确
4. WebSocket连接在长时间任务中更稳定
5. HTTP流式响应适合短时间任务 