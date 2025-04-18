# server.py

from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase
import openai
import json

mcp = FastMCP()

NEO4J_URI = "your-uri"
NEO4J_USER = "your-username"
NEO4J_PASSWORD = "your-password"

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

openai.api_key = "your-openai-api-key"

@mcp.tool()
def query_neo4j_with_llm(natural_query: str, create_nodes: bool = False, row: dict = None) -> str:
    """Generates and executes a Cypher query using LLM and optionally creates nodes, printing output locally."""

    if create_nodes and row:
        try:
            driver = get_neo4j_driver()
            results = []

            def execute_create_query(tx, query, params):
                result = tx.run(query, params)
                return [record.data() for record in result]

            create_query = """
                CREATE (n:Name {name: $name})
                CREATE (mk:Make {name: $make})
                CREATE (cc:CC {value: $cc})
                CREATE (year:Year {value: $year})
                CREATE (km:Kilometers {value: $km})
                CREATE (p:Place {name: $place})
                CREATE (lot:LotNumber {lot_number: $lot_number})
                CREATE (sp:StartPrice {amount: $start_price})
                CREATE (minPrice:MinPrice {amount: $predictedminbid})
                CREATE (maxPrice:MaxPrice {amount: $predictedmaxbid})

                CREATE (n)-[:HAS_CC]->(cc)
                CREATE (cc)-[:BELONGS_TO]->(n)
                CREATE (mk)-[:MANUFACTURES]->(n)
                CREATE (n)-[:HAS_YEAR]->(year)
                CREATE (year)-[:YEAR_OF]->(n)
                CREATE (n)-[:HAS_KM]->(km)
                CREATE (km)-[:KILOMETERS_OF]->(n)
                CREATE (lot)-[:HAS_PLACE]->(p)
                CREATE (p)-[:LOCATION_OF]->(lot)
                CREATE (lot)-[:ASSIGNED_TO]->(n)
                CREATE (n)-[:HAS_LOT]->(lot)
                CREATE (lot)-[:HAS_START_PRICE]->(sp)
                CREATE (sp)-[:START_PRICE_OF]->(lot)
                CREATE (lot)<-[:BID_MIN]-(minPrice)
                CREATE (minPrice)-[:BELONGS_TO_LOT]->(lot)
                CREATE (lot)<-[:BID_MAX]-(maxPrice)
                CREATE (maxPrice)-[:BELONGS_TO_LOT]->(lot)
            """

            params = {
                "name": row.get("name"),
                "make": row.get("make"),
                "cc": row.get("cc"),
                "year": row.get("year"),
                "km": row.get("km"),
                "place": row.get("place"),
                "lot_number": row.get("lot_number"),
                "start_price": row.get("start_price"),
                "predictedminbid": row.get("predictedminbid"),
                "predictedmaxbid": row.get("predictedmaxbid"),
            }

            with driver.session() as session:
                results = session.execute_write(execute_create_query, create_query, params)

            driver.close()

            formatted_results = [dict(record) for record in results]
            print("Node Creation Output:")
            print(json.dumps(formatted_results, indent=2))
            return json.dumps({"result": formatted_results})

        except Exception as e:
            error_message = f"Error creating nodes: {e}"
            print("Node Creation Error:")
            print(error_message)
            return json.dumps({"error": error_message})

    else:
        schema = """
            CREATE (cc)-[:BELONGS_TO]->(n)
            CREATE (mk)-[:MANUFACTURES]->(n)
            CREATE (n)-[:HAS_YEAR]->(year)
            CREATE (year)-[:YEAR_OF]->(n)
            CREATE (n)-[:HAS_KM]->(km)
            CREATE (km)-[:KILOMETERS_OF]->(n)
            CREATE (lot)-[:HAS_PLACE]->(p)
            CREATE (p)-[:LOCATION_OF]->(lot)
            CREATE (lot)-[:ASSIGNED_TO]->(n)
            CREATE (n)-[:HAS_LOT]->(lot)
            CREATE (lot)-[:HAS_START_PRICE]->(sp)
            CREATE (sp)-[:START_PRICE_OF]->(lot)
            CREATE (lot)-[:BID_MIN]->(minPrice)
            CREATE (lot)-[:BID_MAX]->(maxPrice)
        """

        system_prompt = f"""
{schema}

Your goal is to convert user questions into syntactically correct Cypher queries using the schema provided. Follow these strict instructions:

GENERAL RULES:

1. Always use undirected relationships in MATCH clauses, like:
    MATCH (a)-[:RELATION]-(b)
    Do NOT use directional arrows ('->' or '<-').

2. Use only the nodes and relationships explicitly defined in the schema above.
    Do NOT create new node labels, properties, or relationships.

3. Always use the **most direct path possible** between nodes, based strictly on the schema.

4. If there are multiple valid traversal paths to reach the same node, **prefer paths that minimize the number of hops** and stay semantically closest to the user query.

5. You may include intermediate nodes **only when necessary** to follow the schema accurately.

6. When returning node properties:
    - If the property name is one of "startprice", "min price", or "max price", return it with the alias `.amount`.
    - For all other properties, return them using their original name (e.g., `.name`, `.year`).
    Never return raw relationship names like `n HAS_CC`.
    Example: Use `RETURN n.name, s.amount` or `RETURN n.model, y.year`.

7. Do NOT include explanations, markdown, or natural language—only return a JSON object with the "cypher" key.

8. Important: For any queries related to the make of a car:
    - Always use the following pattern:
        MATCH (m:Make)-[:MANUFACTURES]->(n:Name)
    - Do not reverse this direction or use `[:MADE_BY]`. Only `MANUFACTURES` is valid and directional in this case.

TRAVERSAL GUIDELINES:

- MATCH must reflect only allowed traversals. 
- Do NOT jump from unrelated nodes.
- MAKE RULE: Always use MATCH (m:Make)-[:MANUFACTURES]->(n:Name) for make queries.

EXAMPLES:

1. Valid Cypher:
    {{ "cypher": "MATCH (n:Name)-[:HAS_LOT]-(l:LotNumber)-[:HAS_START_PRICE]-(s:StartPrice) RETURN n.name, s.amount" }}

2. Invalid Cypher:
    {{ "cypher": "MATCH (n:Name)-[:HAS_LOT]->(l:LotNumber) RETURN l" }}

3. Valid Cypher (correct MAKE path):
    {{ "cypher": "MATCH (m:Make)-[:MANUFACTURES]->(n:Name) RETURN m.name, n.name" }}

IF UNANSWERABLE:

If the user’s question cannot be answered with the available schema, return this:
{{ "cypher": "" }}

STRICT OUTPUT FORMAT:

Only respond with a single valid JSON object. No commentary. No markdown. No explanation.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_query},
                ],
                temperature=0
            )
            cypher_json = response.choices[0].message.content
            cypher_result = json.loads(cypher_json)
            cypher_query = cypher_result.get("cypher", "")

            print("LLM Generated Cypher Query:")
            print(cypher_query)

            if not cypher_query:
                error_message = "Query cannot be answered with the available schema."
                print(error_message)
                return json.dumps({"result": error_message})

            driver = get_neo4j_driver()

            def execute_read_query(tx, query):
                result = tx.run(query)
                return [dict(record) for record in result]

            with driver.session() as session:
                neo4j_results = session.execute_read(execute_read_query, cypher_query)

            driver.close()

            print("Neo4j Query Output:")
            print(json.dumps({"result": neo4j_results}, indent=2))
            return json.dumps({"result": neo4j_results})

        except Exception as e:
            error_message = f"Error: {e}"
            print("LLM Error:")
            print(error_message)
            return json.dumps({"error": error_message})
        
if __name__ == "__main__":
    mcp.run(transport='sse')