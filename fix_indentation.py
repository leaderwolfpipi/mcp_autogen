#!/usr/bin/env python3

# 读取文件
with open('core/task_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修复第34-47行的缩进
fix_lines = {
    35: "            try:\n",
    36: "                self.llm = OpenAIClient(\n", 
    37: "                    api_key=api_key,\n",
    38: "                    model=model,\n", 
    39: "                    base_url=base_url\n",
    40: "                )\n",
    41: "                self.logger.info(\"LLM客户端初始化成功\")\n"
}

for line_num, new_content in fix_lines.items():
    if line_num <= len(lines):
        lines[line_num - 1] = new_content

# 写回文件
with open('core/task_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 缩进修复完成")
