# AI Assistant Server

A FastAPI server that receives text messages, stores them in a database, and triggers agentic processing to generate todo items.

## Features

- **Message Processing**: Receive and store text messages with debounced processing
- **Agentic Todo Generation**: Background agent processes messages to create todo items
- **Database Integration**: Uses PostgreSQL (Neon) for persistent storage
- **APM & Monitoring**: Built-in application performance monitoring with structured logging
- **Production Ready**: Configured for deployment on Render with proper containerization

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Debounce        │    │  Agent          │
│   Endpoints     │───▶│  Service         │───▶│  Service        │
│                 │    │                  │    │                 │
│ POST /messages/ │    │ 60s debounce     │    │ Process msgs    │
│ GET  /todos/    │    │ timer            │    │ Generate todos  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                              ┌─────────────────┐
│   PostgreSQL    │                              │   Agent Logs    │
│   Database      │                              │   Table         │
│                 │                              │                 │
│ • Messages      │◀─────────────────────────────│ • Thoughts      │
│ • Todos         │                              │ • Actions       │
│ • Senders       │                              │ • Decisions     │
│ • Chats         │                              │                 │
└─────────────────┘                              └─────────────────┘
```

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd ai-assistant-server
```

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your IDE

- **VS Code/Windsurf**: `Cmd+Shift+P` → "Python: Select Interpreter" → Choose `./venv/bin/python3`

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string

## Quick Start

### Local Development

1. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your database URL and other settings
   ```

2. **Run the server**

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Test the API**

   ```bash
   # Send a message
   curl -X POST "http://localhost:8000/api/v1/messages/" \
        -H "Content-Type: application/json" \
        -d '{"text": "I need to buy groceries tomorrow"}'

   # Check todos (after 60 seconds)
   curl "http://localhost:8000/api/v1/todos/"
   ```

### Production Deployment (Render)

1. **Connect your GitHub repository to Render**
2. **Create a new Web Service**
3. **Use the provided `render.yaml` configuration**
4. **Set up Neon PostgreSQL database and add connection string**

## API Endpoints

### Messages

- `POST /api/v1/messages/` - Create a new message
- `GET /api/v1/messages/` - List messages with filtering
- `GET /api/v1/messages/{id}` - Get specific message
- `PATCH /api/v1/messages/{id}` - Update message
- `DELETE /api/v1/messages/{id}` - Delete message

### Todos

- `POST /api/v1/todos/` - Create a new todo
- `GET /api/v1/todos/` - List todos with filtering
- `GET /api/v1/todos/{id}` - Get specific todo
- `PATCH /api/v1/todos/{id}` - Update todo
- `DELETE /api/v1/todos/{id}` - Delete todo
- `POST /api/v1/todos/{id}/complete` - Mark todo as complete
- `POST /api/v1/todos/{id}/reopen` - Reopen completed todo

### Health & Monitoring

- `GET /health` - Health check endpoint
- Structured logging with request tracing
- Prometheus metrics available

## Database Schema

The application uses the following main tables:

- **messages**: Stores incoming text messages
- **todos**: Generated todo items from messages
- **senders**: Message senders/users
- **chats**: Chat sessions
- **agent_logs**: Detailed logs of agent thought processes

## Agent Processing

The agentic process follows this flow:

1. **Message Reception**: Messages are stored with `pending` status
2. **Debounced Triggering**: After 60 seconds of inactivity, agent processing begins
3. **Message Analysis**: Agent analyzes pending messages for actionable items
4. **Todo Generation**: Creates appropriate todo items with priorities
5. **Logging**: All agent thoughts and actions are logged to the database

## Development Notes

### TODO: Implement Actual Agentic Logic

The current implementation includes placeholder logic for message processing. To complete the agentic functionality:

1. **Replace `_extract_todos_from_message()` method** with actual AI/LLM integration
2. **Add natural language processing** for better task extraction
3. **Implement priority and due date detection**
4. **Add context awareness** across multiple messages
5. **Integrate with your preferred AI/LLM service**

### File Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application setup
├── api/
│   └── routes/
│       ├── messages.py     # Message endpoints
│       └── todos.py        # Todo endpoints
├── core/
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database setup
│   └── middleware.py      # APM and logging middleware
├── models/                # SQLAlchemy models
│   ├── message.py
│   ├── todo.py
│   ├── sender.py
│   ├── chat.py
│   └── agent_log.py
├── schemas/               # Pydantic schemas
│   ├── message.py
│   ├── todo.py
│   ├── sender.py
│   └── chat.py
└── services/              # Business logic
    ├── agent_service.py   # Agentic processing
    └── debounce_service.py # Debounced execution
```

## License

[Your License Here]

---

# NON LLM CONTENT BELOW - DO NOT ADD OR DELETE OR EDIT BELOW

On project start

- install ruff (if new computer) section below
- add .env variables (if new computer)
- create venv (if not started yet. Should see something like (venv) arochat@arochat14-mac ai-assistant-server %)
  - check python3 --version to make sure you have 3.13.xxx (if not use chatgpt to get it)
  - create the venv if it doesn't exist: python3 -m venv venv
  - OR cmd shift p -> python: create environment -> 3.13
  - activate it: source venv/bin/activate
- run: pip install -r requirements.txt for linter to see packages
  - new: docker compose up --build
    - this will start by running any migrations btw
    - its rebuilding the docker image and starting the container
- source venv/bin/activate
- uvicorn app.main:app --reload

Updating requirements

- add unversioned req to requirements.in
- create/start venv if not started: source venv/bin/activate
- run: pip install pip-tools
- run: pip-compile --upgrade requirements.in
- OLD: pip install -r requirements.txt
  - new: docker compose up --build
  - (without rebuilding deps): docker compose up

Ruff

- a good python linter that can be configured to fix things on autosave
- install extension
- go into workspace settings.json and add this key to the dict:
- ```json
  "[python]": {
      "editor.formatOnSave": true,
      "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
      },
      "editor.defaultFormatter": "charliermarsh.ruff"
    }
  ```

Alembic

- setup using: alembic init -t async alembic ONE TIME THING
- revision based on models using: alembic revision --autogenerate -m "migration message"
- run by just running docker container
  - docker compose up
  - to rebuild dependencies: docker compose up --build
- can also run by doing alembic upgrade head

Docker

- to rebuild dependencies and run: docker compose up --build
- to run without rebuild deps: docker compose up
- to terminate: docker compose down
- docker compose currently starts the server, and runs any migrations

pytest

- just type pytest and tests will run
- they use conftest to connect to database etc

project layout

- routes for API endpoints
- api schemas for input output schemas of endpoints
- core
  - not sure what config or database is doing
  - middleware is catching http requests and logging shit
- models is sqlalchemy (orm) defining DB schemas
- services will be where agent logic lives, right now its mostly nonsense
  - debounce service is what was copied from original plan
- main.py is the main orchestration file for this whole project
- alembic for database schema changes (migrations)
  - also creates alembic.ini
  - setup using alembic init -t async alembic

TODO

- the endpoint is working but need to validate that its working
  - direct message in new chat (and new users)
  - group message in new chat (and new users)
  - message in existing chat but update chat name
  - message in existing chat but new users
  - message with existing users but new names
  - look through the db schema and make sure all types are correct and such
- stress test test create message endpoint with curl
- get integration tests working
- deploy to github
- get working on render
- get alembic to work in render or wherever I deploy. the migration needs to work with the prod db
- make sure agent logging is capturing everything (another table for this)
- For logging in middleware, figure out what prometheus is doing... looks a bit sketchy
  - honestly need to figure out how logging everywhere works, right now its pretty confusing. theres a lot of logging words in main.py
- eventually need to create background task thats connected to render cron job
- setup API KEY and HTTPS for proper authentication with client
- understand how testing works... do people normally test with a developmentDB? but then whats to stop the developmentDB from getting all out of wack?
  - I want to use my development db for integration tests but then every time I add a new row my integration tests will "break" theoretically... so maybe I need
  - a base state for my development db? idek
  - according to neon I can have up to 10 branches so maybe I have a dev branch and a test branch
- look into why I have to create these weird global services in main.py. Why do I need to instantiate these classes
- figure out how to setup ruff and language server stuff on a new machine and add to readme setup

Long term TODO

- add better types to todo task/event type enum
