
from google import genai
from dotenv import load_dotenv
import os
from tools import tools, search_policies_function, get_booking_function, calculate_refund_function

load_dotenv()

SYSTEM_PROMPT = f"""You are the CityWheels help desk assistant. CityWheels is a bike rental shop.
 
Rules:
1. Answer ONLY from tool results. Never use your general knowledge about bike rentals.
2. For any question about rules, prices, hours, cancellations or FAQ: call search_policies first.
3. For any question about a specific booking: call get_booking. Never guess booking details.
4. For any question about how much money the customer gets back: call calculate_refund.
   NEVER calculate or estimate amounts yourself. Quote the amount returned by the tool.
5. If a booking is not found, tell the customer that the booking was not found and ask them
   to check the number or contact the staff.
6. If the documents and bookings do not answer the question, or the question is not about
   CityWheels, say that you cannot help with that and tell the customer to contact the staff.
7. Reply in the language the customer wrote in. Be short and concrete.
"""

AI_MODEL = "gemini-3.1-flash-lite"
MAX_TOOL_CALLS = 3

def execute_tool(name, arguments):
    """Execute the requested tool and return its result."""

    if name == "search_policies":
        return search_policies_function()

    elif name == "get_booking":
        return get_booking_function(**arguments)

    elif name == "calculate_refund":
        return calculate_refund_function(**arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")


def handle_message(message, client, tool_trace=None):
    
    if tool_trace is None:
        tool_trace = []

    response = client.interactions.create(
        model=AI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        input=message,
        tools=tools,
    )

    tool_call_count = 0

    while response.status == "requires_action":

        function_calls = [
            step for step in response.steps
            if step.type == "function_call"
        ]

        if not function_calls:
            raise RuntimeError(
                "Gemini requires an action but returned no function calls."
            )

        function_results = []

        for step in function_calls:

            tool_call_count += 1

            if tool_call_count > MAX_TOOL_CALLS:
                raise RuntimeError(
                    "Maximum number of tool calls exceeded."
                )
            
            tool_trace.append(step.name)


            result = execute_tool(step.name, step.arguments)

            function_results.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [
                    {
                        "type": "text",
                        "text": str(result),
                    }
                ],
            })

        response = client.interactions.create(
            model=AI_MODEL,
            system_instruction=SYSTEM_PROMPT,
            input=function_results,
            previous_interaction_id=response.id,
            tools=tools,
        )

    if response.output_text:
        return response.output_text

    raise RuntimeError(
        f"Gemini finished without a text response. "
        f"Status: {response.status}"
    )  
        
def main():
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")

    client = genai.Client(api_key=api_key)

    while True:
        try:
            message = input("> ")

            if not message:
                continue

            if message == "exit":
                break

            print(f"Agent: {handle_message(message, client)}")

        except KeyboardInterrupt:
          
            break


if __name__ == "__main__":
    main()

    

        