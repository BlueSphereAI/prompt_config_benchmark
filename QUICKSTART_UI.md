# Quick Start Guide - Web UI

Get the React web interface up and running in 3 steps.

## Prerequisites

- Python 3.9+ with virtual environment activated
- Node.js 18+
- Existing benchmark data (run `benchmark run` first if needed)

## Step 1: Install Dependencies

```bash
# Install backend dependencies (from project root)
pip install -e .

# Install frontend dependencies
cd frontend
npm install
cd ..
```

## Step 2: Start the Backend

```bash
# From project root
benchmark serve --reload
```

The API server will start at `http://localhost:8000`
- API docs available at: `http://localhost:8000/docs`

## Step 3: Start the Frontend

In a **new terminal**:

```bash
cd frontend
npm run dev
```

The web UI will start at `http://localhost:5173`

## Access the UI

Open your browser to: **http://localhost:5173**

You should see:
- **Dashboard**: Overview with stats and recent experiments
- **Experiments**: Searchable table of all runs
- **Analysis**: Charts comparing configurations

## Troubleshooting

### "No data" or empty tables
Run some experiments first:
```bash
benchmark run
```

### Backend connection errors
- Check backend is running: `curl http://localhost:8000/health`
- Verify `.env` file exists in `frontend/` with:
  ```
  VITE_API_URL=http://localhost:8000/api
  ```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Next Steps

- Click on any experiment to see full details
- Add evaluations directly in the UI
- Filter and sort experiments by prompt, config, cost, duration
- View visual comparisons in the Analysis tab

For full documentation, see [FRONTEND_README.md](FRONTEND_README.md)
