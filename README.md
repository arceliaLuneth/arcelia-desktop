# Arcelia

Arcelia is a modern desktop AI assistant built with Python, PySide6, Ollama, and SQLite. The project focuses on providing a responsive local AI experience with a clean user interface, conversation management, and a modular architecture for future expansion.

---

## Overview

Arcelia is designed as a local-first desktop assistant capable of running large language models through Ollama while maintaining conversation history using SQLite. The project emphasizes responsiveness, maintainability, and scalability through a modular architecture.

---

## Features

- Modern desktop interface built with PySide6
- Local AI integration using Ollama
- Multi-conversation support
- SQLite conversation persistence
- Streaming AI responses
- Thread-safe generation using QThread
- Typing indicator
- Conversation rename and delete
- Responsive chat interface
- Modular project architecture

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| UI Framework | PySide6 |
| AI Backend | Ollama |
| Database | SQLite |
| Concurrency | QThread |
| Styling | Qt Style Sheets |

---

## Project Structure

```text
Arcelia/
├── ai/
├── assets/
├── data/
├── memory/
├── tools/
├── ui/
├── main.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository.

```bash
git clone https://github.com/arceliaLuneth/arcelia-desktop.git
cd arcelia-desktop
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the environment.

Linux/macOS

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Start Ollama.

```bash
ollama serve
```

Run the application.

```bash
python main.py
```

---

## Architecture

```
PySide6 UI
      │
      ▼
Chat Manager
      │
      ▼
Ollama Client
      │
      ▼
Ollama Server
      │
      ▼
Large Language Model

SQLite Database
      ▲
      │
Conversation History
```

---

## Roadmap

### Completed

- Desktop interface
- Local AI integration
- Streaming responses
- Conversation history
- SQLite storage
- Multi-chat management
- Threaded response generation

### Planned

- Markdown rendering
- Code syntax highlighting
- Model manager
- Theme manager
- File attachment support
- Voice interaction
- Long-term memory
- Plugin system
- RAG support
- MCP integration

---

## Development Goals

The primary objective of Arcelia is to provide a lightweight, local-first desktop AI assistant with a scalable architecture that can evolve into a complete productivity platform.

---

## License

This project is currently provided for educational and portfolio purposes.
