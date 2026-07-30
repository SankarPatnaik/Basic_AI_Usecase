# Local Qwen Assistant

A simple local chatbot project for students. It runs on your computer using Ollama and the `qwen2.5:3b` model.

It has two features:

1. A general local chatbot.
2. An internet-assisted trip planner that reads travel web pages and asks Qwen to build a vacation plan.

The basic chatbot flow is:

```text
User message -> Streamlit chat history -> Ollama local API -> qwen2.5:3b -> Reply
```

The trip planner flow is:

```text
Trip details -> Search or pasted URLs -> Web page text -> Qwen prompt -> Itinerary
```

Use this when you want a private local helper for planning, writing, studying, coding, or general task support.

---

## What students will learn

1. How a local LLM server works.
2. How a chat message history is stored.
3. How a system prompt changes assistant behavior.
4. How Streamlit can become a local web app.
5. How a Python app calls Ollama through HTTP.
6. How a chatbot can use live web page text as context.

---

## Project files

```text
app.py            Streamlit local chatbot UI
cli.py            Terminal chatbot
chatbot.py        System prompts, modes and transcript export
ollama_client.py  Small HTTP client for Ollama
web_research.py   Lightweight web search and page text extraction
trip_planner.py   Travel-planning prompts and source context
requirements.txt  Python packages
.env.example      Local model settings
tests/            Beginner-friendly tests
```

Read the files in this order:

1. `chatbot.py`
2. `ollama_client.py`
3. `web_research.py`
4. `trip_planner.py`
5. `app.py`
6. `cli.py`

---

## Step 1 - Install Ollama

Install Ollama on your computer:

```text
https://ollama.com
```

After installing, verify it:

```bash
ollama --version
```

---

## Step 2 - Download Qwen 2.5 3B

```bash
ollama pull qwen2.5:3b
```

Optional quick test:

```bash
ollama run qwen2.5:3b
```

Ask a short question, then type `/bye` to exit.

---

## Step 3 - Create the Python environment

From this folder:

```bash
cd local-qwen-chatbot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd local-qwen-chatbot
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4 - Create local settings

```bash
cp .env.example .env
```

The default `.env` values are:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=120
```

---

## Step 5 - Start Ollama

Usually Ollama runs automatically after installation. If needed:

```bash
ollama serve
```

Keep that terminal open.

---

## Step 6 - Run the local web app

Open a new terminal in this folder and run:

```bash
streamlit run app.py --server.address 127.0.0.1 --server.port 8503
```

Open:

```text
http://127.0.0.1:8503
```

The app runs locally on your machine. Open the **Assistant chat** tab for normal chat, or the **Trip planner** tab for vacation planning with web research.

---

## Optional - Run the terminal chatbot

```bash
python cli.py
```

Type `exit` to stop.

---

## Use the trip planner

1. Open the Streamlit app.
2. Select the **Trip planner** tab.
3. Enter destination, dates, starting city, budget, pace and interests.
4. Keep **Search the web automatically** enabled, or paste specific travel websites to crawl.
5. Click **Research and plan trip**.
6. Review the itinerary and the **Web sources used** section.
7. Ask follow-up questions such as:

```text
Make this itinerary cheaper.
Add vegetarian restaurants.
Reduce the number of hotel changes.
Make day 2 slower and more family friendly.
```

The app can read normal web pages. It skips PDF URLs in the web crawler. For PDF-based RAG, use the separate `groq-rag-starter/` project.

Prefer official tourism, hotel, airline, train, museum and event pages when possible. Always verify prices, opening hours, visa rules, weather, safety information and booking availability before final travel decisions.

---

## How the code works

### `chatbot.py`

Stores assistant modes such as:

- General helper
- Study coach
- Code helper
- Writing helper
- Planning helper

The selected mode becomes the system message. The system message tells the model how to behave.

### `ollama_client.py`

Sends this request to Ollama:

```text
POST http://localhost:11434/api/chat
```

The request includes:

- the model name, `qwen2.5:3b`;
- the chat messages;
- temperature;
- maximum output tokens.

### `app.py`

Creates the Streamlit chat screen:

1. Store messages in `st.session_state.messages`.
2. Show old messages.
3. Read the new user message with `st.chat_input`.
4. Send the message history to Ollama.
5. Display and save the assistant reply.

### `web_research.py`

Provides a small crawler:

1. Build a travel search query.
2. Optionally search the web.
3. Fetch a small number of web pages.
4. Extract visible text from HTML.
5. Pass the text to Qwen as source context.

It uses Python standard-library modules so the code stays easy to explain.

### `trip_planner.py`

Builds the travel-planning prompt. The prompt asks Qwen to:

- use web research as the main source;
- create a day-by-day itinerary;
- include food, transport and booking tips;
- cite sources with `[WEB 1]`, `[WEB 2]`, etc.;
- remind the user to verify live details.

---

## Classroom demo script

1. Start Ollama.
2. Run the Streamlit app.
3. Ask: `Create a 5 step plan to learn Python basics.`
4. Change mode to **Study coach**.
5. Ask: `Explain functions with a simple example.`
6. Change mode to **Code helper**.
7. Ask: `Write a Python function to calculate simple interest.`
8. Download the transcript.

This shows that the same model can act differently when the system prompt changes.

## Trip planner classroom demo

1. Open the **Trip planner** tab.
2. Destination: `Singapore`.
3. Dates or duration: `3 days in December`.
4. Starting city: `Bengaluru`.
5. Interests: `food, gardens, public transport, family friendly attractions`.
6. Click **Research and plan trip**.
7. Open **Web sources used** and show students the extracted text.
8. Ask a follow-up: `Make this plan more budget friendly.`

This shows that the model is still local Qwen, but the answer improves because the prompt contains fresh web context.

---

## Troubleshooting

## `Cannot reach Ollama`

Start Ollama:

```bash
ollama serve
```

Then confirm the model is downloaded:

```bash
ollama list
```

## `model qwen2.5:3b not found`

Run:

```bash
ollama pull qwen2.5:3b
```

## The answer is too slow

Try:

- closing other heavy apps;
- lowering **Max output tokens**;
- using a smaller model if needed.

## The answer is too random

Lower **Temperature** in the sidebar.

## The answer is too short

Increase **Max output tokens** in the sidebar.

## Web search fails

Try:

- paste official travel URLs directly into **Optional websites to crawl**;
- reduce **Pages to read**;
- check your internet connection;
- try again later if a site blocks automated requests.

---

## Run tests

```bash
pytest -q
```

These tests do not call Ollama or the live internet. They only check the local helper functions.

---

## How this differs from RAG

| Local Qwen chatbot | Trip planner web context | RAG app |
|---|---|---|
| Uses chat history only | Reads current web pages and passes text to Qwen | Retrieves chunks from your documents |
| Good for general help | Good for vacation planning and current travel research | Good for answering from PDFs or private files |
| Simplest code | Adds web crawling and source context | Adds embeddings and ChromaDB |
| No vector database | No vector database | Uses a vector database |

Start with the basic chatbot, then teach the trip planner, then move to the RAG app after students understand chat messages, prompts and external context.
