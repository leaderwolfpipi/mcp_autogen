# Schema驱动的Pipeline架构

## 问题背景

您提出的问题非常准确：**"解析系统不是应该根据工具的schema获取输出结构的吗？为啥每次需要工具去适配pipeline的结构？"**

这确实是一个架构设计问题。原来的实现存在以下问题：

### 原有架构的问题

1. **工具需要适配Pipeline结构**：每个工具都必须返回特定的字典格式
   ```python
   # 原来的做法 - 工具被迫适配Pipeline
   def smart_search(query: str) -> Dict[str, Any]:
       results = [...]  # 实际搜索结果
       return {"results": results}  # 强制包装
   
   def text_formatter(text: str) -> Dict[str, Any]:
       formatted = format_text(text)
       return {"formatted_text": formatted}  # 强制包装
   ```

2. **硬编码的字段名**：Pipeline期望固定的字段名
   ```python
   # Pipeline期望的固定格式
   search_node.output.results
   text_formatter_node.output.formatted_text
   report_generator_node.output.report_content
   ```

3. **缺乏灵活性**：如果工具的输出结构发生变化，Pipeline就会失败

## 新的Schema驱动架构

### 核心思想

**Pipeline应该根据工具的Schema来适配输出结构，而不是让工具适配Pipeline。**

### 实现方案

#### 1. 工具保持自然输出格式

```python
# 新的做法 - 工具保持自然格式
def smart_search(query: str) -> List[Dict[str, Any]]:
    results = [...]  # 实际搜索结果
    return results  # 直接返回列表

def text_formatter(text: str) -> str:
    formatted = format_text(text)
    return formatted  # 直接返回字符串

def report_generator(content: str) -> str:
    report = generate_report(content)
    return report  # 直接返回字符串
```

#### 2. Schema驱动的数据解析器

```python
class SchemaDrivenResolver:
    """Schema驱动的数据解析器"""
    
    def register_tool_schema(self, tool_name: str, tool_func: Callable):
        """注册工具的Schema"""
        # 自动分析函数签名和返回类型
        sig = inspect.signature(tool_func)
        schema = self._generate_output_schema(sig)
        self.tool_schemas[tool_name] = schema
    
    def extract_output_data(self, tool_name: str, tool_output: Any, 
                          requested_fields: List[str] = None) -> Dict[str, Any]:
        """根据工具的Schema提取输出数据"""
        schema = self.tool_schemas[tool_name]
        return self._schema_based_extraction(schema, tool_output, requested_fields)
```

#### 3. 智能字段映射

```python
def _extract_from_basic_type(self, return_type: Any, tool_output: Any, 
                            requested_fields: List[str] = None) -> Dict[str, Any]:
    """从基本类型中提取数据"""
    # 常见的字段映射规则
    field_mappings = {
        "results": ["results", "data", "items", "list"],
        "formatted_text": ["formatted_text", "text", "content", "output"],
        "report_content": ["report_content", "content", "report", "output"],
        "status": ["status", "success", "state"],
        "message": ["message", "msg", "description", "info"]
    }
    
    for requested_field in requested_fields:
        # 智能映射字段
        if requested_field == "results" and isinstance(tool_output, list):
            result[requested_field] = tool_output
        elif requested_field == "formatted_text" and isinstance(tool_output, str):
            result[requested_field] = tool_output
        # ... 更多智能映射规则
```

## 架构优势

### 1. **工具保持自然格式**
- 工具无需强制包装输出
- 代码更简洁、更易理解
- 工具可以专注于核心逻辑

### 2. **Pipeline自动适配**
- Pipeline根据Schema自动适配数据
- 支持智能字段映射和类型转换
- 提高了系统的灵活性

### 3. **更好的可维护性**
- 工具和Pipeline解耦
- 新增工具无需修改Pipeline
- 支持Schema的自动发现和注册

### 4. **类型安全**
- 基于函数签名的Schema生成
- 支持类型检查和验证
- 减少运行时错误

## 测试结果

### 工具自然输出
```python
# smart_search 返回列表
search_results = smart_search("李自成生平", 1)
print(f"类型: {type(search_results)}")  # <class 'list'>
print(f"内容: {len(search_results)} 个结果")

# text_formatter 返回字符串
formatted_text = text_formatter(search_results)
print(f"类型: {type(formatted_text)}")  # <class 'str'>
print(f"长度: {len(formatted_text)} 字符")

# report_generator 返回字符串
report_content = report_generator(formatted_text)
print(f"类型: {type(report_content)}")  # <class 'str'>
print(f"长度: {len(report_content)} 字符")
```

### Schema驱动的数据提取
```python
# 从smart_search输出中提取"results"字段
extracted_results = resolver.extract_output_data("smart_search", search_results, ["results"])
# 结果: {'results': [{'title': '李自成- 維基百科...', 'link': '...', ...}]}

# 从text_formatter输出中提取"formatted_text"字段
extracted_text = resolver.extract_output_data("text_formatter", formatted_text, ["formatted_text"])
# 结果: {'formatted_text': '【1. 李自成- 維基百科...'}

# 从report_generator输出中提取"report_content"字段
extracted_report = resolver.extract_output_data("report_generator", report_content, ["report_content"])
# 结果: {'report_content': '{\n  "content_length": 609,\n  ...}'}
```

## 使用方式

### 1. 注册工具Schema
```python
resolver = SchemaDrivenResolver()

# 自动注册Schema
resolver.register_tool_schema("smart_search", smart_search)
resolver.register_tool_schema("text_formatter", text_formatter)
resolver.register_tool_schema("report_generator", report_generator)
```

### 2. Pipeline适配
```python
# Pipeline期望的字段
pipeline_expectations = {
    "search_node": ["results"],
    "text_formatter_node": ["formatted_text"],
    "report_generator_node": ["report_content"]
}

# 使用Schema解析器适配输出
adapted_outputs = {}
for node_name, expected_fields in pipeline_expectations.items():
    tool_output = get_tool_output(node_name)
    adapted_outputs[node_name] = resolver.extract_output_data(
        tool_name, tool_output, expected_fields
    )
```

## 总结

这个Schema驱动的架构解决了您提出的核心问题：

1. **工具不再需要适配Pipeline**：工具保持自然的输出格式
2. **Pipeline根据Schema自动适配**：使用智能字段映射和类型转换
3. **提高了系统的灵活性**：支持任意工具的自然集成
4. **更好的可维护性**：工具和Pipeline解耦，各自独立演进

这种架构更符合软件设计的最佳实践，让系统更加灵活、可维护和可扩展。 