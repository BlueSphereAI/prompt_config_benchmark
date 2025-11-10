import { useState } from 'react';
import { Play, Trash2, Edit, BarChart2, XCircle } from 'lucide-react';
import type { ExperimentRun } from '../types/index';
import { api } from '../api/client';

interface PromptCardProps {
  promptName: string;
  runs: ExperimentRun[];
  onRunExperiments: (promptName: string) => void;
  onDeletePrompt: (promptName: string) => void;
  onEdit: (promptName: string) => void;
  onViewResults: (promptName: string, runId: string) => void;
  onRunsUpdated: () => void;
}

const STATUS_COLORS = {
  running: 'bg-gray-100 text-gray-800',
  experiment_completed: 'bg-green-100 text-green-800',
  analysis_completed: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
};

const STATUS_LABELS = {
  running: 'Running...',
  experiment_completed: 'Experiment Done',
  analysis_completed: 'AI Ranking Done',
  failed: 'Failed',
};

export default function PromptCard({
  promptName,
  runs,
  onRunExperiments,
  onDeletePrompt,
  onEdit,
  onViewResults,
  onRunsUpdated,
}: PromptCardProps) {
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);

  const handleDeleteRun = async (runId: string) => {
    if (!confirm('Are you sure you want to delete this run and all its experiments?')) {
      return;
    }

    setDeletingRunId(runId);
    try {
      await api.deleteRun(runId);
      onRunsUpdated();
    } catch (error) {
      console.error('Failed to delete run:', error);
      alert('Failed to delete run: ' + (error as Error).message);
    } finally {
      setDeletingRunId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatCost = (cost: number | null) => {
    if (cost === null || cost === undefined) return '-';
    return `$${cost.toFixed(3)}`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex-1">{promptName}</h3>
          <div className="flex gap-2 ml-4">
            <button
              onClick={() => onEdit(promptName)}
              className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Edit"
            >
              <Edit className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRunExperiments(promptName)}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
              title="Run Experiments"
            >
              <Play className="w-3.5 h-3.5" />
              Run
            </button>
            <button
              onClick={() => onDeletePrompt(promptName)}
              className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              title="Delete Prompt"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Runs List */}
      <div className="p-4">
        {runs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No runs yet</p>
            <p className="text-xs mt-1">Click "Run" to start experiments</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-500 mb-3">
              RUNS ({runs.length})
            </div>
            {runs.map((run) => (
              <div
                key={run.run_id}
                className="p-3 hover:bg-gray-50 rounded transition-colors border border-gray-100"
              >
                {/* Header Row: Timestamp, Status, Actions */}
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-gray-600">
                    {formatDate(run.started_at)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[run.status]
                      }`}
                    >
                      {STATUS_LABELS[run.status]}
                    </span>
                    <button
                      onClick={() => onViewResults(promptName, run.run_id)}
                      className="p-1 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="View Results"
                      disabled={run.status === 'running'}
                    >
                      <BarChart2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteRun(run.run_id)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                      title="Delete Run"
                      disabled={deletingRunId === run.run_id}
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Config Info Row */}
                {run.recommended_config && (
                  <div className="text-sm text-gray-900 mb-1 truncate">
                    {run.recommended_config}
                  </div>
                )}

                {/* Stats Row */}
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span>{run.num_configs} configs</span>
                  <span className="font-medium">{formatCost(run.total_cost)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
