# Local Qwen Assistant

A simple local chatbot project for students. It runs on your computer using Ollama and the `qwen2.5:3b` model.

This project is not RAG. It is a plain chatbot:

```text
User message -> Streamlit chat history -> Ollama local API -> qwen2.5:3b -> Reply
```

Use this when you want a private local helper for planning, writing, studying, coding, or general task support.

---

## What students will learn

1. How a local LLM server works.
2. How a chat message history is stored.
3. How a system prompt changes assistant behavior.
4. How Streamlit can become a local web app.
5. How a Python app calls Ollama through HTTP.

---

## Project files

```text
app.py            Streamlit local chatbot UI
cli.py            Terminal chatbot
chatbot.py        System prompts, modes and transcript export
ollama_client.py  Small HTTP client for Ollama
requirements.txt  Python packages
.env.example      Local model settings
tests/            Beginner-friendly tests
```

Read the files in this order:

1. `chatbot.py`
2. `ollama_client.py`
3. `app.py`
4. `cli.py`

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

The app runs locally on your machine.

---

## Optional - Run the terminal chatbot

```bash
python cli.py
```

Type `exit` to stop.

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

---

## Run tests

```bash
pytest -q
```

These tests do not call Ollama. They only check the local helper functions.

---

## How this differs from RAG

| Local chatbot | RAG app |
|---|---|
| Uses only the model's existing knowledge and chat history | Retrieves chunks from your documents |
| Good for general help | Good for answering from PDFs or private files |
| Simpler code | More complete AI architecture |
| No vector database | Uses embeddings and ChromaDB |

Start with this chatbot first, then teach the RAG app after students understand chat messages and system prompts.
