from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, AsyncGenerator, Generator
import json
import asyncio
import logging
import subprocess
import os

from core.tool_registry import ToolRegistry
from core.requirement_parser import RequirementParser
from core.tool_orchestrator import ToolOrchestrator
from core.pipeline_composer import PipelineComposer
from core.code_generator import CodeGenerator
from core.task_engine import TaskEngine
from core.unified_tool_manager import get_unified_tool_manager
from core.output_validator import OutputValidator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置工作目录为项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
logger = logging.getLogger(__name__)
logger.info(f"设置工作目录为: {project_root}")

# 初始化数据库连接
app = FastAPI(title="MCP AutoGen API")

# 挂载静态文件
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logging.warning(f"静态文件目录挂载失败: {e}")

# 初始化数据库连接
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "")
PG_DB = os.environ.get("PG_DB", "mcp")
db_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# 初始化核心组件
registry = ToolRegistry(db_url)
parser = RequirementParser(use_llm=True, llm_model="gpt-4o")
orchestrator = ToolOrchestrator(registry)
composer = PipelineComposer(registry)
codegen = CodeGenerator(use_llm=True, llm_model="gpt-4o")
# 初始化统一工具管理器和任务引擎
unified_tool_manager = get_unified_tool_manager(registry)
task_engine = TaskEngine(unified_tool_manager, max_depth=5)
validator = OutputValidator()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_tools():
    """自动导入tools.yaml中的工具集合"""
    try:
        subprocess.run(["python", "cmd/import_tools.py"], check=True)
        logger.info("工具导入成功")
    except Exception as e:
        logger.error(f"自动导入工具失败: {e}")

def _generate_mermaid_diagram(execution_steps: List[Dict[str, Any]]) -> str:
    """Generates a robust, simple Mermaid flowchart for reliable rendering."""
    # Always use Left-to-Right layout
    mermaid_code = ["graph LR"]

    if not execution_steps:
        # If no nodes, just show start to end
        mermaid_code.extend([
            "    Start[Start] --> End[End]",
            "",
            "    classDef endpoint fill:#e0e7ff,stroke:#4f46e5,stroke-width:1px,color:#4f46e5;",
            "    class Start,End endpoint;"
        ])
        return "\n".join(mermaid_code)

    # Define all nodes first
    mermaid_code.append("")
    mermaid_code.append("    %% Node definitions")
    for i, step in enumerate(execution_steps):
        node_id = f"Node{i+1}"
        tool_name = step.get('tool_name', 'Unknown Tool').replace('"', '')
        mermaid_code.append(f'    {node_id}["{tool_name}"]')
    
    # Define connections
    mermaid_code.append("")
    mermaid_code.append("    %% Connections")
    mermaid_code.append("    Start[Start] --> Node1")
    
    for i, step in enumerate(execution_steps):
        node_id = f"Node{i+1}"
        if i < len(execution_steps) - 1:
            mermaid_code.append(f"    {node_id} --> Node{i+2}")
        else:
            mermaid_code.append(f"    {node_id} --> End[End]")

    # Define styles
    mermaid_code.extend([
        "",
        "    %% Styles",
        "    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;",
        "    classDef success fill:#d4edda,stroke:#155724,stroke-width:1px,color:#155724;",
        "    classDef failure fill:#f8d7da,stroke:#721c24,stroke-width:1px,color:#721c24;",
        "    classDef endpoint fill:#e0e7ff,stroke:#4f46e5,stroke-width:1px,color:#4f46e5;",
        "",
        "    class Start,End endpoint;"
    ])

    # Apply styles to nodes based on status
    for i, step in enumerate(execution_steps):
        status_class = "success" if step.get("status") == "success" else "failure"
        mermaid_code.append(f"    class Node{i+1} {status_class};")
        
    return "\n".join(mermaid_code)

def _format_node_result_markdown(node_result: Dict[str, Any], current: int, total: int) -> str:
    """格式化节点结果为 Markdown"""
    node_id = node_result.get("node_id", "unknown")
    tool_name = node_result.get("tool_name", "unknown")
    status = node_result.get("status", "success")
    execution_time = node_result.get("execution_time", 0)
    result_summary = node_result.get("result_summary", "")
    
    # 状态图标
    status_icon = "✅" if status == "success" else "❌"
    
    # 构建 markdown 内容
    markdown = f"""### {status_icon} 步骤 {current}/{total}: {tool_name}

**执行时间**: {execution_time:.2f}秒  
**状态**: {status}"""
    
    # 显示结果摘要
    if result_summary:
        markdown += f"\n\n**执行结果**: {result_summary}"
    
    # 如果有输出内容，格式化显示重要信息
    output = node_result.get("output")
    if output:
        formatted_output = _format_output_for_display(output)
        if formatted_output:
            markdown += f"\n\n**详细输出**:\n{formatted_output}"
    
    return markdown

def _format_output_for_display(output: Any) -> str:
    """格式化输出内容用于显示"""
    if output is None:
        return ""
    
    if isinstance(output, str):
        # 如果是长文本，截取前300字符
        if len(output) > 300:
            return f"```\n{output[:300]}...\n```"
        else:
            return f"```\n{output}\n```"
    
    elif isinstance(output, dict):
        # 提取关键信息显示
        if 'results' in output and isinstance(output['results'], list):
            results_count = len(output['results'])
            # 如果是搜索结果，显示前几个结果的标题
            if results_count > 0 and isinstance(output['results'][0], dict):
                sample_titles = []
                for i, result in enumerate(output['results'][:3]):
                    if 'title' in result:
                        sample_titles.append(f"{i+1}. {result['title'][:50]}...")
                    elif 'name' in result:
                        sample_titles.append(f"{i+1}. {result['name'][:50]}...")
                if sample_titles:
                    return f"📊 找到 {results_count} 个结果:\n" + "\n".join(sample_titles)
            return f"📊 返回了 {results_count} 个结果"
        
        elif 'formatted_text' in output:
            text_preview = output['formatted_text'][:200] + "..." if len(output['formatted_text']) > 200 else output['formatted_text']
            return f"📝 格式化文本:\n```\n{text_preview}\n```"
        
        elif 'report_content' in output:
            content_preview = output['report_content'][:300] + "..." if len(output['report_content']) > 300 else output['report_content']
            return f"📄 生成报告:\n```\n{content_preview}\n```"
        
        elif 'primary_data' in output:
            # 标准化输出格式
            primary_data = output['primary_data']
            if isinstance(primary_data, dict):
                if 'results' in primary_data:
                    return f"📊 处理完成，返回 {len(primary_data['results'])} 个结果"
                elif 'report_content' in primary_data:
                    content = primary_data['report_content']
                    preview = content[:200] + "..." if len(content) > 200 else content
                    return f"📄 生成报告:\n```\n{preview}\n```"
                else:
                    # 显示主要数据的关键信息
                    key_info = []
                    for key, value in primary_data.items():
                        if isinstance(value, (str, int, float)):
                            key_info.append(f"**{key}**: {value}")
                        elif isinstance(value, list):
                            key_info.append(f"**{key}**: {len(value)} 项")
                    return "\n".join(key_info[:3])  # 只显示前3个关键信息
        
        elif 'status' in output and output['status'] == 'success':
            # 成功状态的输出
            if 'message' in output:
                return f"✅ {output['message']}"
            else:
                return "✅ 执行成功"
        
        else:
            # 其他字典类型，显示关键字段
            key_info = []
            important_keys = ['title', 'name', 'content', 'result', 'data', 'message', 'summary']
            for key in important_keys:
                if key in output:
                    value = output[key]
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        key_info.append(f"**{key}**: {preview}")
                    elif isinstance(value, (int, float)):
                        key_info.append(f"**{key}**: {value}")
                    elif isinstance(value, list):
                        key_info.append(f"**{key}**: {len(value)} 项")
            
            if key_info:
                return "\n".join(key_info[:3])
            else:
                return f"📋 字典数据，包含 {len(output)} 个字段"
    
    elif isinstance(output, list):
        return f"📋 列表，包含 {len(output)} 个项目"
    
    else:
        return f"🔢 {type(output).__name__} 类型数据"

def _format_final_result_markdown(final_output: Any, execution_time: float) -> str:
    """格式化最终结果为 Markdown"""
    markdown = f"""## ✅ 任务执行完成

**总执行时间**: {execution_time:.2f}秒

### 🎯 最终结果"""
    
    if final_output:
        if isinstance(final_output, str):
            # 如果是文本结果，直接显示（不截断，因为这是最终结果）
            markdown += f"\n\n{final_output}"
        elif isinstance(final_output, dict):
            # 处理字典类型的结果
            if 'primary_data' in final_output:
                primary_data = final_output['primary_data']
                if isinstance(primary_data, dict):
                    if 'results' in primary_data and isinstance(primary_data['results'], list):
                        # 搜索结果
                        results = primary_data['results']
                        markdown += f"\n\n📊 **找到 {len(results)} 个相关结果：**\n"
                        
                        for i, result in enumerate(results[:5], 1):  # 显示前5个结果
                            if isinstance(result, dict):
                                title = result.get('title', result.get('name', f'结果 {i}'))
                                url = result.get('url', result.get('link', ''))
                                snippet = result.get('snippet', result.get('description', result.get('content', '')))
                                
                                markdown += f"\n**{i}. {title}**\n"
                                if url:
                                    markdown += f"🔗 链接: {url}\n"
                                if snippet:
                                    # 限制摘要长度
                                    snippet_preview = snippet[:200] + "..." if len(snippet) > 200 else snippet
                                    markdown += f"📄 摘要: {snippet_preview}\n"
                                markdown += "\n"
                        
                        if len(results) > 5:
                            markdown += f"*... 还有 {len(results) - 5} 个结果未显示*\n"
                    
                    elif 'report_content' in primary_data:
                        # 报告内容
                        content = primary_data['report_content']
                        markdown += f"\n\n📄 **生成的报告：**\n\n{content}"
                    
                    else:
                        # 其他类型的主要数据
                        markdown += "\n\n📋 **执行结果：**\n"
                        for key, value in primary_data.items():
                            if isinstance(value, (str, int, float, bool)):
                                markdown += f"\n- **{key}**: {value}"
                            elif isinstance(value, list):
                                markdown += f"\n- **{key}**: {len(value)} 项"
                            elif isinstance(value, dict) and len(value) < 5:
                                markdown += f"\n- **{key}**: {value}"
            
            elif 'results' in final_output and isinstance(final_output['results'], list):
                # 直接的搜索结果
                results = final_output['results']
                markdown += f"\n\n📊 **找到 {len(results)} 个相关结果：**\n"
                
                for i, result in enumerate(results[:5], 1):
                    if isinstance(result, dict):
                        title = result.get('title', result.get('name', f'结果 {i}'))
                        url = result.get('url', result.get('link', ''))
                        snippet = result.get('snippet', result.get('description', result.get('content', '')))
                        
                        markdown += f"\n**{i}. {title}**\n"
                        if url:
                            markdown += f"🔗 {url}\n"
                        if snippet:
                            snippet_preview = snippet[:200] + "..." if len(snippet) > 200 else snippet
                            markdown += f"📄 {snippet_preview}\n"
                        markdown += "\n"
            
            else:
                # 其他类型的字典结果
                formatted_result = _format_output_for_display(final_output)
                markdown += f"\n\n{formatted_result}"
        
        elif isinstance(final_output, list):
            # 列表结果
            markdown += f"\n\n📋 **返回了 {len(final_output)} 个结果：**\n"
            
            for i, item in enumerate(final_output[:5], 1):
                if isinstance(item, dict):
                    title = item.get('title', item.get('name', f'项目 {i}'))
                    markdown += f"\n{i}. **{title}**"
                    
                    # 显示其他关键信息
                    for key in ['url', 'link', 'description', 'content', 'snippet']:
                        if key in item and item[key]:
                            value = str(item[key])
                            if len(value) > 100:
                                value = value[:100] + "..."
                            markdown += f"\n   - {key}: {value}"
                    markdown += "\n"
                elif isinstance(item, str):
                    preview = item[:100] + "..." if len(item) > 100 else item
                    markdown += f"\n{i}. {preview}\n"
            
            if len(final_output) > 5:
                markdown += f"\n*... 还有 {len(final_output) - 5} 个结果未显示*"
        
        else:
            # 其他类型的结果
            markdown += f"\n\n```\n{str(final_output)}\n```"
    else:
        markdown += "\n\n*无输出结果*"
    
    return markdown

# Pydantic模型
class TaskRequest(BaseModel):
    user_input: str
    input_data: Optional[Any] = None

class RequirementRequest(BaseModel):
    user_input: str

class PipelineRequest(BaseModel):
    requirement: Dict[str, Any]

class ExecuteRequest(BaseModel):
    pipeline: Dict[str, Any]
    input_data: Optional[Any] = None

class RegisterToolRequest(BaseModel):
    tool: Dict[str, Any]

class TaskResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None
    step: Optional[str] = None

def execute_task_with_streaming(user_input: str, input_data: Any = None) -> Generator[str, None, None]:
    """
    执行完整任务的流式生成器（同步版本，用于HTTP流式响应）- 优化版本
    """
    try:
        # 步骤1: 导入工具
        import_tools()
        
        # 步骤2: 使用任务引擎执行任务
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(task_engine.execute(user_input, {}))
        finally:
            loop.close()
        
        if result["success"]:
            # 检查是否是闲聊情况
            if result.get("final_output") and not result.get("execution_steps"):
                # 💬 闲聊模式 - 只输出最终回答
                yield json.dumps({
                    "mode": "chat",
                    "status": "success",
                    "step": "chat_completed",
                    "message": result.get("final_output", ""),
                    "execution_time": result.get("execution_time", 0)
                }, ensure_ascii=False) + "\n"
            else:
                # 🔧 任务模式 - 完整流水线显示
                execution_steps = result.get("execution_steps", [])
                
                # 1. 输出模式标识和 Mermaid 流程图
                mermaid_diagram = _generate_mermaid_diagram(execution_steps)
                yield json.dumps({
                    "mode": "task",
                    "status": "progress",
                    "step": "pipeline_start",
                    "message": "## 🔧 任务执行模式\n\n### 📊 执行流程图",
                    "data": {
                        "mermaid": mermaid_diagram
                    }
                }, ensure_ascii=False) + "\n"
            
                # 2. 逐步显示节点执行结果
                for i, step_result in enumerate(execution_steps, 1):
                    yield json.dumps({
                        "mode": "task",
                        "status": "progress",
                        "step": f"node_{i}",
                        "message": f"### 🚀 步骤 {i}: {step_result.get('tool_name', 'Unknown')}",
                        "data": {
                            "step_index": step_result.get("step_index", i-1),
                            "tool_name": step_result.get("tool_name", "Unknown"),
                            "status": step_result.get("status", "unknown"),
                            "execution_time": step_result.get("execution_time", 0),
                            "purpose": step_result.get("purpose", "执行完成")
                        }
                    }, ensure_ascii=False) + "\n"

                # 3. 输出最终结果
                final_message = _format_final_result_markdown(result.get("final_output"), result.get("execution_time", 0))
                yield json.dumps({
                    "mode": "task",
                    "status": "success",
                    "step": "task_completed",
                    "message": final_message,
                    "data": {
                        "final_output": result.get("final_output"),
                        "execution_time": result.get("execution_time", 0),
                        "total_steps": len(execution_steps),
                        "successful_steps": len([r for r in execution_steps if r.get("status") == "success"])
                    }
                }, ensure_ascii=False) + "\n"
        else:
            # 执行失败
            yield json.dumps({
                "mode": "error",
                "status": "error",
                "step": "execution_failed",
                "message": f"## ❌ 执行失败\n\n{'; '.join(result.get('errors', ['未知错误']))}",
                "data": {
                    "errors": result.get("errors", []),
                    "execution_time": result.get("execution_time", 0)
                }
            }, ensure_ascii=False) + "\n"
        
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        yield json.dumps({
            "mode": "error",
            "status": "error",
            "step": "system_error",
            "message": f"## ❌ 系统错误\n\n{str(e)}",
            "data": {"error": str(e)}
        }, ensure_ascii=False) + "\n"

async def execute_task_with_streaming_async(user_input: str, input_data: Any = None) -> AsyncGenerator[str, None]:
    """
    执行完整任务的异步流式生成器 - 优化版本
    """
    try:
        # 步骤1: 导入工具
        import_tools()
        
        # 步骤2: 使用任务引擎执行任务
        result = await task_engine.execute(user_input, {})
        
        if result["success"]:
            # 检查是否是闲聊情况
            if result.get("final_output") and not result.get("execution_steps"):
                # 💬 闲聊模式 - 只输出最终回答
                yield json.dumps({
                    "mode": "chat",
                    "status": "success",
                    "step": "chat_completed",
                    "message": result.get("final_output", ""),
                    "execution_time": result.get("execution_time", 0)
                }, ensure_ascii=False) + "\n"
            else:
                # 🔧 任务模式 - 完整流水线显示
                execution_steps = result.get("execution_steps", [])
                
                # 1. 输出模式标识和 Mermaid 流程图
                mermaid_diagram = _generate_mermaid_diagram(execution_steps)
                yield json.dumps({
                    "mode": "task",
                    "status": "progress",
                    "step": "pipeline_start",
                    "message": "## 🔧 任务执行模式\n\n### 📊 执行流程图",
                    "data": {
                        "mermaid": mermaid_diagram,
                        "total_steps": len(execution_steps)
                    }
                }, ensure_ascii=False) + "\n"
                
                # 2. 逐个输出节点执行结果
                for i, step_result in enumerate(execution_steps, 1):
                    yield json.dumps({
                        "mode": "task", 
                        "status": "progress",
                        "step": f"step_{i}",
                        "message": f"### 🚀 步骤 {i}: {step_result.get('tool_name', 'Unknown')}",
                        "data": {
                            "step_index": step_result.get("step_index", i-1),
                            "tool_name": step_result.get("tool_name", "Unknown"),
                            "status": step_result.get("status", "unknown"),
                            "execution_time": step_result.get("execution_time", 0),
                            "purpose": step_result.get("purpose", "执行完成")
                        }
                    }, ensure_ascii=False) + "\n"
                
                # 3. 输出最终结果
                final_message = _format_final_result_markdown(result.get("final_output"), result.get("execution_time", 0))
                yield json.dumps({
                    "mode": "task",
                    "status": "success",
                    "step": "completed",
                    "message": final_message,
                    "execution_time": result.get("execution_time", 0)
                }, ensure_ascii=False) + "\n"
        else:
            # 执行失败
            yield json.dumps({
                "mode": "error",
                "status": "error",
                "step": "execution_failed", 
                "message": f"## ❌ 执行失败\n\n{'; '.join(result.get('errors', ['未知错误']))}",
                "data": {
                    "errors": result.get("errors", []),
                    "execution_time": result.get("execution_time", 0)
                }
            }, ensure_ascii=False) + "\n"
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        yield json.dumps({
            "mode": "error",
            "status": "error",
            "step": "system_error",
            "message": f"## ❌ 系统错误\n\n{str(e)}",
            "data": {"error": str(e)}
        }, ensure_ascii=False) + "\n"

def _send_node_result(node_result):
    """发送节点执行结果的回调函数"""
    # 这个函数会在SmartPipelineEngine中被调用
    # 用于实时发送每个工具的执行结果
    pass

@app.get("/")
async def root():
    """根路径，返回演示页面"""
    return FileResponse("static/demo.html")

@app.post("/execute_task")
async def execute_task(req: TaskRequest):
    """
    统一的任务执行接口 - HTTP流式响应
    """
    return StreamingResponse(
        execute_task_with_streaming(req.user_input, req.input_data),
        media_type="application/x-ndjson"
    )

@app.websocket("/ws/execute_task")
async def execute_task_websocket(websocket: WebSocket):
    """
    统一的任务执行接口 - WebSocket
    """
    await websocket.accept()
    
    try:
        # 接收任务请求
        data = await websocket.receive_text()
        request_data = json.loads(data)
        user_input = request_data.get("user_input", "")
        input_data = request_data.get("input_data", None)
        
        # 执行任务并流式发送结果
        async for message in execute_task_with_streaming_async(user_input, input_data):
            await websocket.send_text(message)
            
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket执行失败: {e}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "step": "websocket_error",
            "message": f"WebSocket执行失败: {str(e)}",
            "data": None
        }, ensure_ascii=False))

@app.post("/parse_requirement")
def parse_requirement(req: RequirementRequest):
    """解析需求"""
    try:
        requirement = parser.parse(req.user_input)
        return {"requirement": requirement}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/smart_execute")
async def smart_execute(req: TaskRequest):
    """智能Pipeline执行接口"""
    try:
        result = await task_engine.execute(req.user_input, {})
        return {
            "success": result["success"],
            "pipeline_result": result,
            "execution_time": result.get("execution_time", 0),
            "execution_steps": result.get("execution_steps", []),
            "final_output": result.get("final_output", ""),  # 添加final_output，包含闲聊回答
            "errors": result.get("errors", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate_pipeline")
def generate_pipeline(req: PipelineRequest):
    """生成流水线"""
    try:
        plan = orchestrator.decide(req.requirement)
        if plan["plan_type"] == "codegen":
            missing_tools = []
            for missing in plan["missing_tools"]:
                code = codegen.generate(missing)
                missing_tools.append({"tool": missing["tool"], "code": code})
            return {"plan": plan, "missing_tools": missing_tools}
        pipeline = composer.compose(plan)
        return {"plan": plan, "pipeline": pipeline}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/execute_pipeline")
def execute_pipeline(req: ExecuteRequest):
    """执行流水线"""
    try:
        # 使用SmartPipelineEngine执行pipeline
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(task_engine.execute(
                f"执行pipeline: {json.dumps(req.pipeline)}", {}
            ))
        finally:
            loop.close()
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tools")
def list_tools():
    """列出所有工具"""
    return {"tools": registry.list_tools()}

@app.post("/register_tool")
def register_tool(req: RegisterToolRequest):
    """注册新工具"""
    try:
        registry.register_tool(req.tool)
        return {"msg": "Tool registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))