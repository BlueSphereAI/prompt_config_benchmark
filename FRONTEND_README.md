# Prompt Benchmark Web UI

A React-based web interface for viewing and analyzing LLM benchmark results.

## Features

- **Dashboard**: Overview of all experiments with summary statistics
- **Experiments List**: Sortable, filterable table of all experiment runs
- **Experiment Details**: View full prompts, responses, configurations, and add evaluations
- **Analysis**: Visual comparison of configurations with charts and detailed statistics
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatically adapts to system preferences

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for backend)
- Existing benchmark data in SQLite database

### Installation

1. **Install Backend Dependencies**:
   ```bash
   # From project root
   pip install -e .
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the Backend API Server**:
   ```bash
   # From project root
   benchmark serve

   # Or with auto-reload for development
   benchmark serve --reload

   # Custom port
   benchmark serve --port 8080
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

2. **Start the Frontend Dev Server** (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

   The UI will be available at `http://localhost:5173`

3. **Open your browser** to `http://localhost:5173`

## Development

### Frontend Structure

```
frontend/
├── src/
│   ├── api/          # API client for backend communication
│   ├── components/   # Reusable React components
│   ├── hooks/        # Custom React hooks (React Query)
│   ├── pages/        # Page components (Dashboard, Experiments, etc.)
│   ├── types/        # TypeScript type definitions
│   ├── App.tsx       # Main app component with routing
│   └── main.tsx      # Entry point
├── .env              # Environment variables (API URL)
└── package.json      # Dependencies and scripts
```

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000/api
```

For production, update this to your deployed API URL.

## Backend API

The backend is built with FastAPI and provides the following endpoints:

- `GET /api/experiments` - List all experiments (with filters)
- `GET /api/experiments/{id}` - Get single experiment details
- `GET /api/prompts` - List distinct prompt names
- `GET /api/configs` - List distinct config names
- `GET /api/analysis/prompt/{name}` - Analyze specific prompt
- `GET /api/analysis/overall` - Overall rankings
- `GET /api/evaluations/{experiment_id}` - Get evaluations
- `POST /api/evaluations` - Create new evaluation
- `GET /api/dashboard` - Dashboard statistics

Full API documentation: `http://localhost:8000/docs`

## Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

This creates optimized static files in `frontend/dist/`.

### Serve Frontend

You can serve the built frontend with any static file server:

```bash
# Using Python's built-in server
cd frontend/dist
python -m http.server 3000

# Or use nginx, Apache, Vercel, Netlify, etc.
```

### Deploy Backend

```bash
# Production server
uvicorn prompt_benchmark.api.server:app --host 0.0.0.0 --port 8000

# With multiple workers
uvicorn prompt_benchmark.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### CORS Configuration

Update `frontend/src/api/client.ts` with your production API URL, and ensure the backend's CORS settings in `src/prompt_benchmark/api/server.py` include your frontend domain.

## Troubleshooting

### Backend not connecting
- Ensure the backend is running on port 8000
- Check `.env` file has correct `VITE_API_URL`
- Verify CORS settings in backend

### No data showing
- Run some experiments first: `benchmark run`
- Check database exists at `data/results/benchmark.db`
- Verify API returns data: `http://localhost:8000/api/experiments`

### Build errors
- Delete `node_modules` and `package-lock.json`, then `npm install`
- Clear cache: `npm cache clean --force`
- Ensure Node.js version is 18+

## Contributing

1. Make changes in `frontend/src/`
2. Test with `npm run dev`
3. Build with `npm run build` to check for errors
4. Submit pull request

## License

Same as main project.
