# #MCP server
# from mcp.server.fastmcp import FastMCP

# # Create an MCP server
# mcp = FastMCP()

# # Add an addition tool
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers"""
#     print(f"Adding {a} and {b}")
#     return a + b

# # More tools can be added here

# #### Resources ####
# # Add a static resource
# @mcp.resource("resource://some_static_resource")
# def get_static_resource() -> str:
#     """Static resource data"""
#     return "Any static data can be returned"

# # Add a dynamic greeting resource
# @mcp.resource("greeting://{name}")
# def get_greeting(name: str) -> str:
#     """Get a personalized greeting"""
#     return f"Hello, {name}!"

# #### Prompts ####
# @mcp.prompt()
# def review_code(code: str) -> str:
#     return f"Please review this code:\n\n{code}"

# @mcp.prompt()
# def debug_error(error: str) -> list[tuple]:
#     return [
#         ("user", "I'm seeing this error:"),
#         ("user", error),
#         ("assistant", "I'll help debug that. What have you tried so far?"),
#     ]

# if __name__ == "__main__":
#     # Initialize and run the server
#     mcp.run(transport='sse')

#-------------client.py------------------

# #MCP client
# from mcp import ClientSession
# from mcp.client.sse import sse_client


# async def run():
#     async with sse_client(url="http://localhost:8000/sse") as streams:
#         async with ClientSession(*streams) as session:

#             await session.initialize()

#             # List available tools
#             tools = await session.list_tools()
#             print(tools)

#             # Call a tool
#             result = await session.call_tool("add", arguments={"a": 4, "b": 5})
#             print("------------------------------------")
#             print(result.content[0].text)

#             # List available resources
#             resources = await session.list_resources()
#             print("------------------------------------")
#             print("resources", resources)

#             # Read a resource
#             content = await session.read_resource("resource://some_static_resource")
#             print("------------------------------------")
#             print("content", content.contents[0].text)

#             # Read a resource
#             content = await session.read_resource("greeting://balaji")
#             print("------------------------------------")
#             print("content", content.contents[0].text)

#             # List available prompts
#             prompts = await session.list_prompts()
#             print("------------------------------------")
#             print("prompts", prompts)

#             # Get a prompt
#             prompt = await session.get_prompt(
#                 "review_code", arguments={"code": "print(\"Hello world\")"}
#             )
#             print("------------------------------------")
#             print("prompt", prompt)

#             prompt = await session.get_prompt(
#                 "debug_error", arguments={"error": "SyntaxError: invalid syntax"}
#             )
            
#             print("prompt", prompt)


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(run())

