import { useState } from 'react';
import { Play, Trash2, Edit, BarChart2, XCircle, Sparkles, Loader2, FileText, X } from 'lucide-react';
import type { ExperimentRun, Experiment } from '../types/index';
import { api } from '../api/client';
import MultiRunDialog from './MultiRunDialog';

interface PromptCardProps {
  promptName: string;
  runs: ExperimentRun[];
  onRunExperiments: (promptName: string) => void;
  onDeletePrompt: (promptName: string) => void;
  onEdit: (promptName: string) => void;
  onViewResults: (promptName: string, runId: string) => void;
  onRunsUpdated: () => void;
  onStartAIEvaluation: (promptName: string, runId: string) => void;
  evaluatingRunId?: string | null;
  onStartMultiRunSession?: (sessionId: string, numRuns: number) => void;
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
  onStartAIEvaluation,
  evaluatingRunId,
  onStartMultiRunSession,
}: PromptCardProps) {
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showDataModal, setShowDataModal] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runExperiments, setRunExperiments] = useState<Experiment[]>([]);
  const [loadingData, setLoadingData] = useState(false);

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

  const handleViewData = async (runId: string) => {
    setSelectedRunId(runId);
    setShowDataModal(true);
    setLoadingData(true);

    try {
      const data = await api.getRun(runId);
      setRunExperiments(data.experiments);
    } catch (error) {
      console.error('Failed to fetch run data:', error);
      alert('Failed to load run data: ' + (error as Error).message);
      setShowDataModal(false);
    } finally {
      setLoadingData(false);
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

  const generateMarkdownData = (): string => {
    if (runExperiments.length === 0) {
      return 'No experiment data available.';
    }

    let markdown = `# Experiment Run Data\n\n`;
    markdown += `**Run ID:** ${selectedRunId}\n\n`;
    markdown += `**Total Experiments:** ${runExperiments.length}\n\n`;
    markdown += `---\n\n`;

    runExperiments.forEach((exp, index) => {
      markdown += `## Experiment ${index + 1}: ${exp.config_name}\n\n`;
      markdown += `- **Experiment ID:** ${exp.experiment_id}\n`;
      markdown += `- **Config Name:** ${exp.config_name}\n`;
      markdown += `- **Success:** ${exp.success ? 'Yes' : 'No'}\n`;
      markdown += `- **Acceptable:** ${exp.is_acceptable ? 'Yes' : 'No'}\n`;
      markdown += `- **Duration:** ${exp.duration_seconds.toFixed(2)}s\n`;
      markdown += `- **Cost:** $${exp.estimated_cost_usd.toFixed(4)}\n`;
      markdown += `- **Tokens:** ${exp.total_tokens} (prompt: ${exp.prompt_tokens}, completion: ${exp.completion_tokens})\n`;
      markdown += `- **Finish Reason:** ${exp.finish_reason || 'N/A'}\n`;
      markdown += `- **Start Time:** ${new Date(exp.start_time).toLocaleString()}\n`;
      markdown += `- **End Time:** ${new Date(exp.end_time).toLocaleString()}\n`;

      if (exp.error) {
        markdown += `- **Error:** ${exp.error}\n`;
      }

      markdown += `\n### Response\n\n`;
      markdown += `\`\`\`\n${exp.response || 'No response'}\n\`\`\`\n\n`;

      markdown += `### Configuration\n\n`;
      markdown += `\`\`\`json\n${JSON.stringify(exp.config_json, null, 2)}\n\`\`\`\n\n`;

      if (exp.metadata_json && Object.keys(exp.metadata_json).length > 0) {
        markdown += `### Metadata\n\n`;
        markdown += `\`\`\`json\n${JSON.stringify(exp.metadata_json, null, 2)}\n\`\`\`\n\n`;
      }

      markdown += `---\n\n`;
    });

    return markdown;
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
              onClick={() => setIsDialogOpen(true)}
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
                {/* Header Row: Timestamp & Status */}
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-gray-600">
                    {run.run_number ? `Run #${run.run_number} • ` : ''}{formatDate(run.started_at)}
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${
                      STATUS_COLORS[run.status]
                    }`}
                  >
                    {(run.status === 'running' || run.status === 'experiment_completed') && (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    )}
                    {STATUS_LABELS[run.status]}
                  </span>
                </div>

                {/* Config Info Row */}
                {run.recommended_config && (
                  <div className="text-sm text-gray-900 mb-1 truncate">
                    {run.recommended_config}
                  </div>
                )}

                {/* Stats Row */}
                <div className="flex items-center justify-between text-xs text-gray-600 mb-2">
                  <span>{run.num_configs} configs</span>
                  {run.avg_duration !== null && (
                    <span className="font-medium">⏱ {run.avg_duration.toFixed(1)}s avg</span>
                  )}
                  <span className="font-medium">{formatCost(run.total_cost)}</span>
                </div>

                {/* Actions Row */}
                <div className="flex items-center justify-between gap-2 pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-1.5">
                    {/* AI Evaluation Button - Only show for experiment_completed status */}
                    {run.status === 'experiment_completed' && (
                      <button
                        onClick={() => onStartAIEvaluation(promptName, run.run_id)}
                        disabled={evaluatingRunId === run.run_id}
                        className="px-2.5 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-1.5 shadow-sm"
                        title="Run AI Evaluation"
                      >
                        {evaluatingRunId === run.run_id ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Evaluating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-3.5 h-3.5" />
                            AI Evaluation
                          </>
                        )}
                      </button>
                    )}

                    {/* View Results Button */}
                    <button
                      onClick={() => onViewResults(promptName, run.run_id)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-40"
                      title="View Results"
                      disabled={run.status === 'running'}
                    >
                      <BarChart2 className="w-4 h-4" />
                    </button>

                    {/* View Data Button */}
                    <button
                      onClick={() => handleViewData(run.run_id)}
                      className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-40"
                      title="View Run Data"
                      disabled={run.status === 'running'}
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={() => handleDeleteRun(run.run_id)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                    title="Delete Run"
                    disabled={deletingRunId === run.run_id}
                  >
                    {deletingRunId === run.run_id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Multi-Run Dialog */}
      <MultiRunDialog
        promptName={promptName}
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onStartSession={(sessionId, numRuns) => {
          if (onStartMultiRunSession) {
            onStartMultiRunSession(sessionId, numRuns);
          }
        }}
      />

      {/* Data Modal */}
      {showDataModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Experiment Run Data
              </h2>
              <button
                onClick={() => {
                  setShowDataModal(false);
                  setSelectedRunId(null);
                  setRunExperiments([]);
                }}
                className="p-2 text-gray-500 hover:text-gray-700 rounded hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loadingData ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  <span className="ml-3 text-gray-600">Loading experiment data...</span>
                </div>
              ) : (
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto">
                    {generateMarkdownData()}
                  </pre>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center bg-gray-50">
              <span className="text-sm text-gray-600">
                {runExperiments.length > 0 && `${runExperiments.length} experiment(s)`}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const markdown = generateMarkdownData();
                    navigator.clipboard.writeText(markdown);
                    alert('Copied to clipboard!');
                  }}
                  disabled={loadingData}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Copy to Clipboard
                </button>
                <button
                  onClick={() => {
                    setShowDataModal(false);
                    setSelectedRunId(null);
                    setRunExperiments([]);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
