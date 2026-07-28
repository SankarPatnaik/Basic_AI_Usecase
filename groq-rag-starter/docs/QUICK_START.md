# 10-Minute Quick Start

## 1. Open a terminal in the project folder

## 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install packages

```bash
pip install -r requirements.txt
```

## 4. Create `.env`

```bash
cp .env.example .env
```

On Windows Command Prompt use:

```bat
copy .env.example .env
```

Put your Groq key into `.env`.

## 5. Ingest sample data

```bash
python ingest.py --reset
```

## 6. Run the website

```bash
streamlit run streamlit_app.py
```

## 7. Ask

```text
How many annual leave days do employees receive?
```

## 8. Stop

Press `Ctrl+C` in the terminal.
