# CityWheels help desk agent

## 1. Installing and running

```bash
pip install -r requirements.txt
cp .env.example .env          
python citywheels.py          
```

Run the unit tests (no network, no API key needed):
 
```bash
pytest -v
```
 
Run the evaluation (needs the API key, makes real model calls). The report is written to `eval/results.md`:
 
```bash
python eval/run_eval.py
```
 
## 2. Model and provider
 
Gemini `gemini-3.1-flash-lite` through the official `google-genai` SDK, called directly without an agent framework.
 
- Free tier, so anyone can reproduce the project without paying.
- Native function calling, and server-side conversation state.
- A small, fast model is working just fine here.
- Higher models were either too slow or very limited for free tier use.


## 3. How the agent works
 
The loop (`handle_message` in `citywheels.py`):
 
1. Sends the customer's message to the model together with the system prompt and the tool declarations.
2. While the response status is `requires_action`, it takes every `function_call` step, runs the function, and sends the results back as `function_result` items (linked by `call_id` and `previous_interaction_id`).
3. When the model returns plain text, that is the answer.
4. Safety limits: at most `MAX_TOOL_CALLS = 3` tool calls per question, and an error if the model stops without any text. `handle_message` also records the names of the called tools in `tool_trace`, which the evaluation uses.

Tools (`tools.py`):
 
| Tool | What it does |
| --- | --- |
| `search_policies` | Returns the policy documents (`cancellations.md`, `faq.md`, `prices.md`) to the model. |
| `get_booking(booking id)` | Returns one booking as JSON, or a clear "not found" result. |
| `calculate_refund(booking id)` | Applies the cancellation rules in code: only `confirmed` bookings can be cancelled; 100% of the rental price at 48h or more before start, 50% at 24h or more, 0% below 24h; the deposit is always refunded; the booking fee never is. Voucher bookings are refunded as a voucher, not as money. |
 
The "current time" is a fixed constant (`2026-06-10 09:00 Europe/Warsaw`, as the task specifies).
 
Instructions to the model (`SYSTEM_PROMPT`): answer only from tool results; call `search_policies` for rules, prices and hours; call `get_booking` for booking details and never guess them; call `calculate_refund` for any money-back question and never calculate amounts itself; say plainly when a booking is not found; when the documents and bookings do not answer, or the question is not about CityWheels, say so and send the customer to the staff; reply in the customer's language, briefly.


## 4. Tests
 
- `test_tools.py`: runs against temporary data files. Covers `search_policies`, `get_booking` (found and not found) and each `calculate_refund` rule: below 24h, exactly 24h, exactly 48h, card and voucher, unknown booking, and the `cancelled` / `in_progress` / `completed` statuses.
- `test_citywheels.py`: tests the agent loop with a fake client (`MagicMock` returning scripted responses). Covers each tool being dispatched with the right arguments, a plain-text answer with no tool call, and an unknown tool name.

## 5. Evaluation results
 
`eval/questions.json` holds 13 questions in the categories policy, booking, refund and out of scope. Each has expected tools and expected text.
 
Last run: 12 of 13 passed. The failures:
 
- **E10** ("Why can't I get a refund for CW-1006?"): The check failed because the agent called `calculate_refund` instead of `get_booking`, and the test expects `get_booking` and `search_policies`. To fix this I could improve descriptions in tools declarations, or return a reason with an anwser in `calculate_refund`.
 
Problems with the evaluation itself:
 
- Each question is run once, so a pass can be luck.
- I didn't include questions that would try to break the agent, for ex. prompt injection.
- I could give more complex questions, and try to counfuse it.
- Some checks don't have expected output text, and have to be checked by hand.

## 6. How I used AI coding assistants

I have used AI like Claude and ChatGPT, to make me a plan for this task, to help me create unit tests and an evaluation, check for mistakes, explain errors with the agent loop, and give me ideas of what can i improve.
I have used it do things faster and more efficient. I didn't just copy and paste what it gave me, but tried to undestand it first, and then remake it to work with my code.

The AI coding assistants have worked very well, but often gave me too complex solutions at once, so I had to take one step at the time, to don't get tangled in new code. 
Once AI suggested to me to put the fixed current date `2026-06-10 09:00 Europe/Warsaw` to the agent prompt, so that it can anwser questions like `How much can i get back if i cancel my booking tommorow?`, but I quickly realized that it wouldn't be very usefull in real AI helper, and too much time consuming to make, so i decided that it's not worth it.


## 7. Limitations

- **No real retrieval.** `search_policies` returns all three documents. With three small files this is accurate and simple, but it does not scale.
- **No conversation memory.** Every message is handled independently, so follow-ups don't work.


## 8. What I would do next

My solution far from perfect, but I made it mainly myself and really know how it works. I could create a lot of new functions and greatly improve current ones.
 
- Add a tool for changing and cancelling bookings.
- Make the evaluation more robust: more questions testing the soft spots of this agent, 2-3 runs per question.
- Add real retrieval to `search_policies` (split by headings, rank by relevance, return source file and section).
- Add a cache system for speed optimatization (more important with bigger scale).
- Add conversation memory with `previous_interaction_id`.