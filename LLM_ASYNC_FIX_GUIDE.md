# LLM 报告生成器异步问题修复指南

## 问题诊断

### 错误信息
```
WARNING - 处理模块 llm_report_generator 时出错: 'await' outside async function (llm_report_generator.py, line 366)
```

### 根本原因
在 `tools/llm_report_generator.py` 第366行，代码在同步函数中使用了 `await` 关键字：

```python
def _call_llm_api(prompt: str) -> str:  # 同步函数定义
    # ... 其他代码 ...
    response = await client.chat.completions.create(...)  # 第366行：在同步函数中使用 await
```

这违反了Python异步编程的基本规则：**`await` 只能在 `async` 函数内部使用**。

## 生产级解决方案

### 方案1：使用同步客户端（推荐）

修改 `_call_llm_api` 函数，使用同步版本的API客户端：

```python
def _call_llm_api(prompt: str) -> str:
    """调用LLM API - 修复版本"""
    try:
        # 尝试使用OpenAI GPT-4
        try:
            import openai
            import os
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise Exception("未设置OPENAI_API_KEY环境变量")
            
            # 使用同步客户端
            client = openai.OpenAI(api_key=api_key)  # 同步版本
            response = client.chat.completions.create(  # 同步调用，无需 await
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的报告撰写专家..."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9
            )
            return response.choices[0].message.content
            
        except Exception as openai_error:
            logging.warning(f"OpenAI API调用失败: {openai_error}")
            
            # 尝试使用百度文心一言
            try:
                # 优先使用同步版本
                from erniebot import ErnieBot  # 同步版本
                
                api_key = os.getenv('ERNIE_API_KEY')
                if not api_key:
                    raise Exception("未设置ERNIE_API_KEY环境变量")
                
                client = ErnieBot(api_key=api_key)
                response = client.chat.completions.create(  # 同步调用
                    model="ernie-bot-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3
                )
                return response.choices[0].message.content
                
            except ImportError:
                # 如果只有异步版本，使用方案2的方法
                return _handle_async_ernie_in_sync_context(prompt)
                
    except Exception as e:
        logging.error(f"所有LLM API调用都失败: {e}")
        return _generate_enhanced_fallback_report(prompt)
```

### 方案2：在同步函数中运行异步代码

如果必须使用异步客户端，可以使用 `asyncio.run()` 在同步环境中运行异步代码：

```python
def _handle_async_ernie_in_sync_context(prompt: str) -> str:
    """在同步上下文中处理异步文心一言调用"""
    import asyncio
    import concurrent.futures
    from erniebot import AsyncErnieBot
    
    async def _async_ernie_call():
        api_key = os.getenv('ERNIE_API_KEY')
        if not api_key:
            raise Exception("未设置ERNIE_API_KEY环境变量")
        
        client = AsyncErnieBot(api_key=api_key)
        response = await client.chat.completions.create(
            model="ernie-bot-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        return response.choices[0].message.content
    
    try:
        # 检查是否已经在事件循环中
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已经在事件循环中，在新线程中运行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _async_ernie_call())
                return future.result(timeout=30)
        else:
            # 如果没有事件循环，直接运行
            return asyncio.run(_async_ernie_call())
    except Exception as e:
        logging.warning(f"异步调用失败: {e}")
        raise
```

### 方案3：重构为异步函数（长期方案）

为了更好的性能和一致性，可以创建完全异步的版本：

```python
async def _call_llm_api_async(prompt: str) -> str:
    """调用LLM API的异步版本"""
    try:
        # 使用异步OpenAI客户端
        try:
            import openai
            import os
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise Exception("未设置OPENAI_API_KEY环境变量")
            
            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个专业的报告撰写专家..."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9
            )
            return response.choices[0].message.content
            
        except Exception as openai_error:
            logging.warning(f"OpenAI API调用失败: {openai_error}")
            
            # 使用异步文心一言
            try:
                from erniebot import AsyncErnieBot
                
                api_key = os.getenv('ERNIE_API_KEY')
                if not api_key:
                    raise Exception("未设置ERNIE_API_KEY环境变量")
                
                client = AsyncErnieBot(api_key=api_key)
                response = await client.chat.completions.create(
                    model="ernie-bot-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3
                )
                return response.choices[0].message.content
                
            except Exception as ernie_error:
                logging.warning(f"文心一言API调用失败: {ernie_error}")
                return _generate_enhanced_fallback_report(prompt)
                
    except Exception as e:
        logging.error(f"所有LLM API调用都失败: {e}")
        return _generate_enhanced_fallback_report(prompt)

# 提供同步包装器以保持向后兼容
def _call_llm_api(prompt: str) -> str:
    """同步版本的包装器"""
    try:
        import asyncio
        return asyncio.run(_call_llm_api_async(prompt))
    except Exception as e:
        logging.error(f"异步LLM调用失败: {e}")
        return _generate_enhanced_fallback_report(prompt)
```

## 实施建议

### 立即修复（推荐）
1. **使用方案1**：将第366行的 `await` 调用改为同步调用
2. 使用同步版本的API客户端（`openai.OpenAI` 而不是 `openai.AsyncOpenAI`）
3. 使用同步版本的文心一言客户端（`ErnieBot` 而不是 `AsyncErnieBot`）

### 中期优化
1. 实施方案2的错误处理机制
2. 添加超时控制和重试逻辑
3. 完善日志记录

### 长期架构
1. 考虑将整个工具链重构为异步架构
2. 使用方案3提供异步和同步两个版本
3. 统一异步编程模式

## 代码质量改进

### 错误处理增强
```python
def _call_llm_api_with_retry(prompt: str, max_retries: int = 3) -> str:
    """带重试机制的LLM API调用"""
    for attempt in range(max_retries):
        try:
            return _call_llm_api(prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"所有重试尝试失败: {e}")
                raise
            else:
                logging.warning(f"第{attempt + 1}次尝试失败，重试中: {e}")
                time.sleep(2 ** attempt)  # 指数退避
```

### 配置管理
```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    openai_api_key: Optional[str] = None
    ernie_api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: int = 30
    
    def __post_init__(self):
        self.openai_api_key = self.openai_api_key or os.getenv('OPENAI_API_KEY')
        self.ernie_api_key = self.ernie_api_key or os.getenv('ERNIE_API_KEY')

# 使用配置
config = LLMConfig()
```

### 监控和指标
```python
import time
from functools import wraps

def monitor_llm_call(func):
    """监控LLM调用的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logging.info(f"LLM调用成功，耗时: {duration:.2f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"LLM调用失败，耗时: {duration:.2f}秒，错误: {e}")
            raise
    return wrapper
```

## 测试验证

### 单元测试
```python
import unittest
from unittest.mock import patch, MagicMock

class TestLLMReportGenerator(unittest.TestCase):
    
    @patch('openai.OpenAI')
    def test_openai_success(self, mock_openai):
        # 模拟成功响应
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "测试报告"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = _call_llm_api("测试提示")
        self.assertEqual(result, "测试报告")
    
    @patch.dict('os.environ', {}, clear=True)
    def test_no_api_key(self):
        # 测试没有API密钥的情况
        result = _call_llm_api("测试提示")
        self.assertIn("回退", result)  # 应该使用回退方案
```

### 集成测试
```python
def test_integration():
    """集成测试"""
    # 使用真实的API密钥进行测试（在CI/CD中）
    if os.getenv('OPENAI_API_KEY'):
        result = _call_llm_api("生成一个简短的测试报告")
        assert len(result) > 0
        assert "报告" in result
```

## 部署检查清单

- [ ] 确保所有 `await` 调用都在 `async` 函数中
- [ ] 验证API密钥环境变量设置正确
- [ ] 测试所有API提供商的回退机制
- [ ] 验证超时和重试逻辑
- [ ] 检查日志记录是否完整
- [ ] 运行单元测试和集成测试
- [ ] 监控生产环境的错误率和响应时间

## 总结

这个问题是典型的Python异步编程错误。通过使用同步API客户端或正确处理异步调用，可以彻底解决这个问题。推荐使用方案1作为快速修复，然后逐步实施其他改进措施。 