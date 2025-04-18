# client.py

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_client():
    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            # Get the query from the user
            natural_query = input("Enter your query: ")

            results = await session.call_tool("query_neo4j_with_llm", arguments={"natural_query": natural_query})

            if results and results.content:
                print("Query Results:")
                print(results.content)
            else:
                print("No valid results received.")

if __name__ == "__main__":
    asyncio.run(run_client())