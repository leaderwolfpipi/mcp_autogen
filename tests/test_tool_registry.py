import unittest
from core.tool_registry import ToolRegistry

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry("config/tools.yaml")

    def test_list_tools(self):
        tools = self.registry.list_tools()
        self.assertTrue(len(tools) > 0)

    def test_find_tool(self):
        tool = self.registry.find_tool("text_translator")
        self.assertIsNotNone(tool)

if __name__ == "__main__":
    unittest.main()
