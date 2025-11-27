# Prompt Configuration Benchmark Framework

A comprehensive framework for testing and comparing different LLM configurations (GPT-5 variants) across various prompts. Features a modern web interface for creating prompts, managing configurations, running experiments, and using AI-assisted ranking to find optimal LLM settings.

## Features

- **Modern Web UI**: Interactive React interface for managing prompts, configs, and rankings
- **Multi-Run Sessions**: Execute multiple experiment batches with automatic AI evaluation after each run
- **AI-Assisted Ranking**: Use GPT-5 to automatically evaluate and rank experiment results
- **Interactive Ranking**: Drag-and-drop interface for human ranking with time tracking
- **Custom Evaluation Templates**: Create review prompts to define custom AI evaluation criteria
- **Config Management**: Clone, edit, and compare LLM configurations with performance statistics
- **Real-Time Progress**: Monitor running experiments with live progress updates
- **Comprehensive Metrics**: Track response time, token usage, costs, and AI/human rankings
- **SQLite Storage**: Persistent storage with full experiment history
- **REST API**: FastAPI backend with automatic OpenAPI documentation

## Quick Start

### 1. Installation

**Prerequisites:**
- Python 3.9 or higher
- Node.js 16+ and npm
- OpenAI API key

**Backend Setup:**
```bash
# Clone repository
git clone <repository-url>
cd prompt_config_benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -e .

# Initialize data directories and database
benchmark init

# Configure API key in .env
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

**Frontend Setup:**
```bash
cd frontend
npm install
cd ..
```

### 2. Start the Application

**Terminal 1 - Start Backend Server:**
```bash
source venv/bin/activate
benchmark serve --reload
```
Backend runs at: http://localhost:8000
API documentation at: http://localhost:8000/docs

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs at: http://localhost:5173

**Open your browser to:** http://localhost:5173

## Web UI Usage

The web interface is the primary way to use this framework. It provides four main pages for managing your LLM benchmarking workflow.

### Prompt Library Page

The home page for managing prompts and running experiments.

**Features:**
- View all prompts with their experiment runs organized chronologically
- Create new prompts using a JSON editor (OpenAI messages format)
- Edit or delete existing prompts
- Run all active LLM configs against a prompt to create an experiment run
- **Multi-Run Sessions**: Execute 1-10 sequential runs with automatic AI evaluation after each run
- Monitor progress of active sessions with real-time updates (polls every 2 seconds)
- View status of each run (running, completed, failed) with experiment counts
- Navigate to Compare page for detailed analysis and ranking
- Trigger AI evaluation for specific runs
- Delete runs and their associated experiments

**Creating a Prompt:**
Prompts use the OpenAI messages format:
```json
{
  "name": "summarize-article",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant that summarizes articles concisely."
    },
    {
      "role": "user",
      "content": "Summarize the following article:\n\n{article_text}"
    }
  ],
  "metadata": {
    "description": "Summarize articles",
    "category": "text-processing"
  }
}
```

**Multi-Run Workflow:**
1. Click "Run Multi-Session" on a prompt
2. Configure number of runs (1-10) and select review prompt for AI evaluation
3. System executes runs sequentially, evaluating each with GPT-5
4. Monitor progress in real-time
5. Review AI rankings for each run
6. Navigate to Compare page to add human rankings

### Configs Page

Manage and optimize LLM configurations.

**Features:**
- View all configurations with aggregated performance statistics
- Sort configs by multiple criteria:
  - **AI Score**: Average score from AI evaluations
  - **Time**: Average response duration
  - **Cost**: Average API cost
  - **Unacceptable Count**: Number of unacceptable responses
  - **Model**: Group by model type (GPT-5, GPT-5-mini, GPT-5-nano)
- View detailed stats for each config:
  - Average AI score with evaluation count
  - Average duration in seconds
  - Average cost in USD
  - Number of unacceptable responses across all experiments
- Create new configurations with custom parameters
- Edit existing configurations (model, max_output_tokens, verbosity, reasoning_effort)
- Clone configurations to quickly create variants
- Delete configurations (soft delete - maintains experiment history)
- Copy configuration JSON to clipboard

**Configuration Format:**
```json
{
  "model": "gpt-5",
  "max_output_tokens": 8000,
  "verbosity": "medium",
  "reasoning_effort": "high"
}
```

**GPT-5 Specific Parameters:**
- `verbosity`: "low" | "medium" | "high" - Controls output detail level
- `reasoning_effort`: "minimal" | "low" | "medium" | "high" - Controls internal reasoning depth
- `max_output_tokens`: Token budget for completion (includes reasoning tokens)
  - Recommended: 8000+ for GPT-5 due to reasoning overhead
  - Lower values may result in truncated responses

**Performance Optimization:**
Use the Configs page to identify best-performing configurations:
1. Sort by AI Score to find highest quality configs
2. Sort by Cost to find most economical options
3. Sort by Time to find fastest responses
4. Clone high-performing configs and adjust parameters
5. Test modified configs on your prompts

### Review Prompts Page

Create and manage AI evaluation templates.

**Features:**
- Create custom review prompts that define how GPT-5 evaluates experiment results
- Define evaluation criteria (accuracy, clarity, tone, completeness, etc.)
- Specify output format and scoring methodology
- Search prompts by name or description
- View usage statistics for each review prompt
- Duplicate existing prompts to create variants
- Edit and update review prompt templates
- Validate templates before use
- Delete unused review prompts

**Review Prompt Structure:**
Review prompts are templates that tell the AI evaluator how to assess results. They can include:
- Evaluation criteria and their definitions
- Scoring scales (e.g., 1-10 or categorical)
- Output format requirements (structured JSON, narrative, etc.)
- Specific aspects to focus on
- Examples of good vs. poor responses

**Creating Effective Review Prompts:**
1. Define clear, specific evaluation criteria
2. Provide concrete examples when possible
3. Specify the output format for structured analysis
4. Include context about what makes a response acceptable
5. Use consistent scoring methodology across evaluations

**Usage in Workflow:**
Review prompts are selected when:
- Starting a multi-run session (automatic AI evaluation after each run)
- Manually triggering batch AI evaluation from Compare page
- The selected review prompt determines how GPT-5 scores each experiment

### Compare Page

Interactive ranking and analysis interface for experiment results.

**Features:**
- **Drag-and-Drop Ranking Carousel**: Visually rank experiment results by dragging cards into preferred order
- View all experiments for a prompt side-by-side
- See full experiment details: prompt, response, config, timing, tokens, cost
- Toggle experiment acceptability (mark as acceptable/unacceptable)
- Multiple sorting options:
  - AI Score (from AI evaluations)
  - Human Score (from saved rankings)
  - Time (response duration)
  - Price (API cost)
  - Tokens (total token usage)
- **AI-Assisted Evaluation**:
  - Start batch evaluation using selected review prompt
  - Uses GPT-5 with reasoning for scoring
  - Auto-polls for completion (checks every 5 seconds)
  - View AI scores and structured feedback
- **Save Human Rankings**:
  - Drag cards to rank by preference
  - System tracks time spent ranking
  - Calculates agreement with AI rankings (Kendall tau correlation)
  - Saves ranking with timestamp
- View AI recommendation for best config based on combined rankings
- Filter experiments by specific run_id using URL parameter
- View original prompt messages and all experiment metadata

**Ranking Workflow:**
1. Open Compare page from Prompt Library
2. Review all experiment results for the prompt
3. Optionally start AI evaluation to get initial rankings
4. Drag experiment cards to rank by preference (best at top)
5. Click "Save Ranking" to persist your preferences
6. System calculates agreement between your ranking and AI ranking
7. View recommended config based on combined human + AI rankings

**Understanding the Ranking:**
- The carousel shows experiments as draggable cards
- Top position = best/preferred result
- Bottom position = worst/least preferred result
- You can drag any card to any position
- Ranking order determines which configs are recommended

**Filtering by Run:**
- Add `?run_id=<run_id>` to URL to view only experiments from a specific run
- Useful for comparing results across different experimental sessions
- Navigate from Prompt Library by clicking on specific runs

## Common Workflows

### Workflow 1: Create and Test a New Prompt

1. **Create Prompt**
   - Go to Prompt Library page
   - Click "Create New Prompt"
   - Enter prompt name and messages in JSON format
   - Add optional metadata (description, category)
   - Click "Create Prompt"

2. **Run Experiments**
   - Click "Run All Configs" on your new prompt
   - System creates an experiment run and executes all active configs
   - Monitor progress in real-time (shows running, completed, failed counts)

3. **Analyze Results**
   - Click "Go to Compare" when experiments complete
   - Review all experiment outputs
   - Mark unacceptable responses
   - Sort by cost, time, or quality to identify patterns

### Workflow 2: AI-Assisted Ranking

1. **Set Up Review Prompt**
   - Go to Review Prompts page
   - Create a review prompt defining your evaluation criteria
   - Include scoring methodology and output format
   - Save the review prompt

2. **Run Multi-Session Experiments**
   - Go to Prompt Library
   - Click "Run Multi-Session" on a prompt
   - Select number of runs (e.g., 5 runs)
   - Choose your review prompt from dropdown
   - Click "Start Multi-Run Session"

3. **Automatic Evaluation**
   - System runs first batch of experiments
   - GPT-5 evaluates results using your review prompt
   - Repeats for remaining runs
   - Each run gets AI scores and rankings

4. **Add Human Ranking**
   - Navigate to Compare page
   - Review AI scores and feedback
   - Use drag-and-drop to create your own ranking
   - Save ranking to calculate human-AI agreement

5. **View Recommendation**
   - System combines AI and human rankings
   - Displays recommended config at top of page
   - Use recommendation to guide future config selection

### Workflow 3: Config Optimization

1. **Baseline Performance**
   - Go to Configs page
   - Review statistics for all configs
   - Identify best performers by AI score, cost, or time

2. **Create Variant**
   - Clone a high-performing config
   - Modify parameters:
     - Increase `max_output_tokens` for longer responses
     - Change `verbosity` to adjust detail level
     - Adjust `reasoning_effort` to balance quality vs. speed
   - Save new config

3. **Test Variant**
   - Go to Prompt Library
   - Run experiments on representative prompts
   - Compare new config performance to baseline

4. **Analyze Trade-offs**
   - Use Compare page to evaluate quality differences
   - Check Configs page for cost and time impacts
   - Iterate on parameters to optimize for your use case

### Workflow 4: Custom Evaluation Criteria

1. **Define Criteria**
   - Go to Review Prompts page
   - Create review prompt with specific criteria:
     - Technical accuracy
     - Tone and style
     - Completeness
     - Formatting
     - Domain-specific requirements

2. **Create Evaluation Template**
   - Structure output format (e.g., JSON with scores per criterion)
   - Define scoring scale (1-10, pass/fail, etc.)
   - Include examples of good responses
   - Save review prompt

3. **Apply to Experiments**
   - Go to Prompt Library
   - Run multi-session with your review prompt
   - OR go to Compare page and start batch evaluation
   - Review structured AI feedback for each experiment

4. **Refine Over Time**
   - Duplicate existing review prompts
   - Adjust criteria based on results
   - A/B test different evaluation approaches
   - Track which review prompts give most useful insights

## Configuration Format

### Langfuse Configuration (JSON)

Configurations use the Langfuse format for storing LLM parameters:

**Standard Parameters:**
```json
{
  "model": "gpt-4-turbo-preview",
  "temperature": 0.7,
  "max_output_tokens": 1500,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**GPT-5 Extended Format:**
```json
{
  "model": "gpt-5",
  "max_output_tokens": 8000,
  "verbosity": "medium",
  "reasoning_effort": "high"
}
```

**GPT-5 Important Notes:**
- GPT-5 does NOT support `temperature` parameter
- Use `max_completion_tokens` in API (automatically handled by executor)
- Reasoning tokens count toward `max_output_tokens` budget
- Empty responses with `finish_reason: length` indicate reasoning consumed entire token budget
- Recommended token limits: 8000+ for most use cases

Save configurations as JSON files in `data/configs/` or manage through the Web UI.

### Prompt Definitions (OpenAI Messages Format)

Prompts use the OpenAI messages format:

```json
{
  "name": "my-prompt",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Write a {style} description of {topic}"
    }
  ],
  "metadata": {
    "description": "Generate descriptions",
    "category": "creative",
    "tags": ["creative", "description"]
  }
}
```

**Message Roles:**
- `system`: Sets assistant behavior and context
- `user`: User messages and instructions
- `assistant`: Previous assistant responses (for multi-turn conversations)

Create and edit prompts through the Web UI or save as JSON files in `data/prompts/`.

## CLI Reference (Legacy)

**Note:** The CLI commands below are legacy tools from before the Web UI was developed. The Web UI is the recommended interface for all operations. These commands may not be fully maintained.

### Available Commands

```bash
# Initialize directories and example files
benchmark init

# Run experiments (superseded by Web UI "Run All Configs")
benchmark run
benchmark run --prompt my-prompt --config gpt5-standard

# Human evaluation (superseded by Web UI Compare page)
benchmark evaluate
benchmark evaluate --prompt my-prompt --evaluator "Your Name"

# AI evaluation (superseded by Web UI AI evaluation features)
benchmark ai-evaluate
benchmark ai-evaluate --model gpt-5 --prompt my-prompt

# Analysis (superseded by Web UI Configs and Compare pages)
benchmark analyze
benchmark analyze --prompt my-prompt --export results.csv

# Start API server (required for Web UI)
benchmark serve --reload
benchmark serve --host 0.0.0.0 --port 8000
```

For modern usage, use the Web UI instead of these CLI commands.

## API Documentation

The framework provides a comprehensive REST API built with FastAPI.

**Access API Documentation:**
- Interactive docs: http://localhost:8000/docs (Swagger UI)
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

**Key API Features:**
- 40+ REST endpoints for complete functionality
- Automatic request validation and serialization
- Background task processing for long-running experiments
- CORS enabled for frontend at localhost:5173 and localhost:3000
- Comprehensive error handling and logging

**Main Endpoint Categories:**
- `/api/experiments` - Run and manage experiments
- `/api/prompts` - CRUD operations for prompts
- `/api/configs` - CRUD operations for LLM configs
- `/api/review-prompts` - Manage AI evaluation templates
- `/api/ai-evaluate` - Batch AI evaluation
- `/api/rankings` - Save and retrieve human rankings
- `/api/recommendations` - Get config recommendations
- `/api/runs` - Experiment run management
- `/api/multi-run-sessions` - Multi-run session progress

For full API reference, visit http://localhost:8000/docs when the server is running.

## Metrics Tracked

For each experiment, the framework tracks:

- **Timing**: Total duration in seconds, timestamp
- **Token Usage**:
  - Prompt tokens (input)
  - Completion tokens (output)
  - Reasoning tokens (GPT-5 internal reasoning)
  - Total tokens
- **Cost**: Estimated cost in USD based on model pricing
- **Response**: Full LLM response text
- **Configuration**: Complete configuration used (model, parameters)
- **Success/Failure**: Whether the request succeeded
- **Errors**: Any error messages
- **Run Association**: Links to experiment run for grouping
- **Acceptability**: Human-marked acceptable/unacceptable flag
- **Evaluations**: AI and human scores and rankings

## Architecture

### System Overview

The framework consists of three main components:

**Backend (Python + FastAPI):**
- FastAPI REST API server
- SQLAlchemy ORM for database operations
- AsyncOpenAI for parallel experiment execution
- SQLite database for persistent storage
- Background task processing for long-running operations

**Frontend (React + TypeScript):**
- React 19 with TypeScript
- Vite for fast development and building
- TanStack Query for data fetching and caching
- React Router for navigation
- Tailwind CSS for styling
- Recharts for data visualization
- @dnd-kit for drag-and-drop ranking

**Storage:**
- SQLite database at `data/results/benchmark.db`
- Tables: experiments, experiment_runs, evaluations, rankings, review_prompts, prompts, configs
- JSON serialization for complex fields (config, messages, metadata)

### Data Flow

1. **User creates prompt** (Web UI) → POST /api/prompts/create → Stored in database
2. **User runs experiments** (Web UI) → POST /api/experiments/run-all-configs → Background task executes
3. **AsyncOpenAI executes configs in parallel** → Saves results incrementally → Updates run status
4. **User triggers AI evaluation** (Web UI) → POST /api/ai-evaluate/batch → GPT-5 scores experiments
5. **User ranks results** (Web UI drag-and-drop) → POST /api/rankings → Calculates AI agreement
6. **System generates recommendation** → GET /api/recommendations → Combines AI + human rankings

### Project Structure

```
prompt_config_benchmark/
├── src/
│   └── prompt_benchmark/
│       ├── __init__.py
│       ├── models.py              # Pydantic data models
│       ├── config_loader.py       # Load configs and prompts
│       ├── executor.py            # Run experiments (AsyncOpenAI)
│       ├── storage.py             # SQLAlchemy database operations
│       ├── evaluator.py           # AI evaluation logic
│       ├── analyzer.py            # Statistical analysis
│       ├── cli.py                 # Command-line interface (legacy)
│       └── api/
│           ├── server.py          # FastAPI application
│           ├── routes.py          # API endpoints
│           └── schemas.py         # API request/response models
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── pages/                 # Page components
│   │   ├── api/                   # API client
│   │   ├── types/                 # TypeScript types
│   │   ├── App.tsx                # Main app component
│   │   └── main.tsx               # Entry point
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── prompts/                   # Prompt JSON files
│   ├── configs/                   # Config JSON files
│   └── results/
│       └── benchmark.db           # SQLite database
├── tests/                         # Unit tests
├── scripts/                       # Utility scripts
├── requirements.txt
├── pyproject.toml
├── .env                           # Environment variables
└── README.md
```

## Environment Variables

Configure in `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Backend
DATABASE_URL=sqlite:///data/results/benchmark.db
```

For frontend configuration, create `frontend/.env`:
```bash
# Optional - Frontend (defaults to http://localhost:8000)
VITE_API_URL=http://localhost:8000/api
```

## Testing

Run the test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=prompt_benchmark --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

## Troubleshooting

### Backend Won't Start

**Error: OpenAI API key not provided**
- Ensure `OPENAI_API_KEY` is set in `.env` file in project root
- Verify `.env` file is in the same directory as where you run `benchmark serve`

**Error: Port 8000 already in use**
- Another process is using port 8000
- Stop the other process or use a different port: `benchmark serve --port 8001`

**Error: Database locked**
- Close any other processes accessing the database
- If persists, restart both backend and frontend

### Frontend Won't Connect to Backend

**Error: Network Error or Failed to Fetch**
- Ensure backend is running at http://localhost:8000
- Check backend logs for errors
- Verify CORS settings allow localhost:5173
- Check `frontend/.env` if using custom VITE_API_URL

**Error: 404 on API calls**
- Backend may not be running
- Check that backend is at http://localhost:8000, not another port
- Try accessing http://localhost:8000/docs to verify backend is up

### Experiments Not Running

**No results appear after clicking "Run All Configs"**
- Check browser console for errors
- Check backend logs for OpenAI API errors
- Ensure you have active configs (Configs page)
- Verify OpenAI API key is valid and has credits

**Empty responses with `finish_reason: length`**
- GPT-5 reasoning consumed all tokens in budget
- Increase `max_output_tokens` in config (try 8000+)
- Edit config on Configs page

### AI Evaluation Issues

**AI evaluation never completes**
- Check backend logs for errors
- Verify review prompt template is valid
- Ensure sufficient OpenAI API credits
- Check that experiments exist to evaluate

**AI scores seem incorrect**
- Review your review prompt template
- Ensure criteria are clearly defined
- Test review prompt with smaller batch first
- Check GPT-5 model is available in your OpenAI account

### Database Issues

**Database errors or corruption**
- Backup current database: `cp data/results/benchmark.db data/results/benchmark.db.backup`
- Delete database: `rm data/results/benchmark.db`
- Restart backend to create fresh database
- Re-run experiments

**Missing data after restart**
- Check that `data/results/benchmark.db` exists
- Verify DATABASE_URL in `.env` points to correct location
- Ensure database file has read/write permissions

## Advanced Features

### Programmatic Usage

You can use the framework programmatically from Python:

```python
from prompt_benchmark.config_loader import ConfigLoader, PromptLoader
from prompt_benchmark.executor import ExperimentExecutor
from prompt_benchmark.storage import ResultStorage
from prompt_benchmark.analyzer import BenchmarkAnalyzer

# Load configurations
config = ConfigLoader.load_config_from_file("data/configs/gpt5-standard.json")
prompt = PromptLoader.load_prompt_from_file("data/prompts/my-prompt.json")

# Initialize components
storage = ResultStorage()
executor = ExperimentExecutor()

# Run experiment
result = executor.run_experiment(
    prompt=prompt,
    config=config,
    config_name="gpt5-standard"
)

# Save result
storage.save_result(result)

# Analyze
analyzer = BenchmarkAnalyzer(storage)
comparison = analyzer.analyze_prompt("my-prompt")
analyzer.print_comparison(comparison)
```

### Batch Processing

Run multiple prompts with multiple configs programmatically:

```python
executor = ExperimentExecutor()
results = executor.run_full_benchmark(
    prompts=prompts_dict,
    configs=configs_dict
)
```

### Custom Evaluation Models

Change the AI evaluator model in review prompts or via API:

```python
# In Web UI: Edit review prompt and change model field
# Or via API:
POST /api/ai-evaluate/batch
{
  "prompt_name": "my-prompt",
  "review_prompt_id": 1,
  "model": "gpt-4"  // Use different model for evaluation
}
```

## Cost Estimation

The framework tracks estimated costs based on current OpenAI pricing:

- Model-specific pricing per 1M tokens
- Separate input/output token pricing
- Actual token counts from API responses
- Reasoning tokens included in cost calculations for GPT-5

**View Costs:**
- Individual experiment costs on Compare page
- Aggregate costs per config on Configs page
- Total costs on Dashboard (when implemented)

**Note:** Pricing is updated periodically in `executor.py` but may not reflect the latest OpenAI pricing changes. Check `MODEL_PRICING` dict in source code for current values.

## Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Backend Development

```bash
# Install in editable mode
pip install -e .

# Run with auto-reload
benchmark serve --reload

# View logs
tail -f benchmark_api.log
```

### Code Style

The project uses:
- Black for Python code formatting
- Ruff for Python linting
- ESLint for TypeScript/React linting

Format code:
```bash
# Python
black src/ tests/

# TypeScript (in frontend/)
npm run lint
```

## Support

For issues and questions:
- Check this README and Web UI documentation
- Review API documentation at http://localhost:8000/docs
- Check existing configurations in `data/configs/` for examples
- Review example prompts in `data/prompts/`

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with FastAPI and Pydantic for the backend
- React and TypeScript for the frontend
- SQLAlchemy for database management
- TanStack Query for data fetching
- Vite for frontend tooling
- Inspired by Langfuse configuration format
