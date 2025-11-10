import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Copy, Save, X, ClipboardCopy, Check, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { api } from '../api/client';

interface LLMConfig {
  name: string;
  model: string;
  max_output_tokens: number | null;
  verbosity: string | null;
  reasoning_effort: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  unacceptable_count: number;
  avg_duration_seconds: number | null;
  avg_cost_usd: number | null;
  avg_ai_score: number | null;
  ai_evaluation_count: number;
}

type SortMethod = 'model' | 'aiScore' | 'time' | 'cost' | 'unacceptable';
type SortDirection = 'asc' | 'desc';

export function Configs() {
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [copiedConfig, setCopiedConfig] = useState<string | null>(null);
  const [sortMethod, setSortMethod] = useState<SortMethod>('model');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  useEffect(() => {
    fetchConfigs();
  }, []);

  const sortConfigs = (data: LLMConfig[], method: SortMethod, direction: SortDirection): LLMConfig[] => {
    const sorted = [...data];
    const dirMultiplier = direction === 'asc' ? 1 : -1;

    switch (method) {
      case 'model': {
        // Sort by model, reasoning_effort, then verbosity
        const modelOrder = { 'gpt-5': 1, 'gpt-5-mini': 2, 'gpt-5-nano': 3 };
        const reasoningOrder = { 'high': 1, 'medium': 2, 'low': 3, 'minimal': 4, '': 5, null: 5 };
        const verbosityOrder = { 'high': 1, 'medium': 2, 'low': 3, '': 4, null: 4 };

        return sorted.sort((a, b) => {
          const modelA = modelOrder[a.model as keyof typeof modelOrder] || 999;
          const modelB = modelOrder[b.model as keyof typeof modelOrder] || 999;
          if (modelA !== modelB) return (modelA - modelB) * dirMultiplier;

          const reasoningA = reasoningOrder[a.reasoning_effort as keyof typeof reasoningOrder] || 999;
          const reasoningB = reasoningOrder[b.reasoning_effort as keyof typeof reasoningOrder] || 999;
          if (reasoningA !== reasoningB) return (reasoningA - reasoningB) * dirMultiplier;

          const verbosityA = verbosityOrder[a.verbosity as keyof typeof verbosityOrder] || 999;
          const verbosityB = verbosityOrder[b.verbosity as keyof typeof verbosityOrder] || 999;
          return (verbosityA - verbosityB) * dirMultiplier;
        });
      }

      case 'aiScore': {
        // Sort by AI score, nulls always last
        return sorted.sort((a, b) => {
          if (a.avg_ai_score === null && b.avg_ai_score === null) return 0;
          if (a.avg_ai_score === null) return 1;
          if (b.avg_ai_score === null) return -1;
          return (b.avg_ai_score - a.avg_ai_score) * dirMultiplier;
        });
      }

      case 'time': {
        // Sort by average time, nulls always last
        return sorted.sort((a, b) => {
          if (a.avg_duration_seconds === null && b.avg_duration_seconds === null) return 0;
          if (a.avg_duration_seconds === null) return 1;
          if (b.avg_duration_seconds === null) return -1;
          return (a.avg_duration_seconds - b.avg_duration_seconds) * dirMultiplier;
        });
      }

      case 'cost': {
        // Sort by average cost, nulls always last
        return sorted.sort((a, b) => {
          if (a.avg_cost_usd === null && b.avg_cost_usd === null) return 0;
          if (a.avg_cost_usd === null) return 1;
          if (b.avg_cost_usd === null) return -1;
          return (a.avg_cost_usd - b.avg_cost_usd) * dirMultiplier;
        });
      }

      case 'unacceptable': {
        // Sort by unacceptable count
        return sorted.sort((a, b) => (b.unacceptable_count - a.unacceptable_count) * dirMultiplier);
      }

      default:
        return sorted;
    }
  };

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const data = await api.listConfigs(true);
      const sorted = sortConfigs(data, sortMethod, sortDirection);
      setConfigs(sorted);
    } catch (error) {
      console.error('Failed to fetch configs:', error);
      alert('Failed to load configs');
    } finally {
      setLoading(false);
    }
  };

  const handleSortChange = (method: SortMethod) => {
    // If clicking the same column, toggle direction
    if (method === sortMethod) {
      const newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      setSortDirection(newDirection);
      const sorted = sortConfigs(configs, method, newDirection);
      setConfigs(sorted);
    } else {
      // New column - use default direction for that column
      const defaultDirection = method === 'aiScore' || method === 'unacceptable' ? 'desc' : 'asc';
      setSortMethod(method);
      setSortDirection(defaultDirection);
      const sorted = sortConfigs(configs, method, defaultDirection);
      setConfigs(sorted);
    }
  };

  const SortableHeader = ({ column, label }: { column: SortMethod; label: string }) => {
    const isActive = sortMethod === column;
    const showArrow = isActive;

    return (
      <th
        className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer select-none group"
        onClick={() => handleSortChange(column)}
      >
        <div className="flex items-center gap-1 hover:text-blue-600 transition-colors">
          <span>{label}</span>
          <span className={`transition-opacity ${showArrow ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'}`}>
            {isActive ? (
              sortDirection === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
            ) : (
              <ArrowUpDown size={14} />
            )}
          </span>
        </div>
      </th>
    );
  };

  const handleCreate = () => {
    setEditingConfig({
      name: '',
      model: 'gpt-5',
      max_output_tokens: 8000,
      verbosity: 'medium',
      reasoning_effort: 'medium',
      description: '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_active: true,
      unacceptable_count: 0,
      avg_duration_seconds: null,
      avg_cost_usd: null,
      avg_ai_score: null,
      ai_evaluation_count: 0,
    });
    setIsCreating(true);
    setShowEditor(true);
  };

  const handleEdit = (config: LLMConfig) => {
    setEditingConfig(config);
    setIsCreating(false);
    setShowEditor(true);
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete config "${name}"?`)) return;

    try {
      await api.deleteConfig(name);
      await fetchConfigs();
      alert('Config deleted successfully');
    } catch (error) {
      console.error('Failed to delete config:', error);
      alert('Failed to delete config');
    }
  };

  const handleClone = async (name: string) => {
    const newName = prompt(`Enter new name for cloned config:`, `${name}-copy`);
    if (!newName) return;

    try {
      await api.cloneConfig(name, newName);
      await fetchConfigs();
      alert('Config cloned successfully');
    } catch (error) {
      console.error('Failed to clone config:', error);
      alert('Failed to clone config');
    }
  };

  const generateLangfuseJson = (config: LLMConfig): string => {
    // Map model names to Langfuse tier names
    let modelTier: string;
    if (config.model === 'gpt-5') {
      modelTier = 'smart'; // or 'reasoning' - using 'smart' as default
    } else if (config.model === 'gpt-5-mini') {
      modelTier = 'fast';
    } else {
      // For unknown models (like gpt-5-nano), pass through unchanged
      modelTier = config.model;
    }

    // Build Langfuse config JSON, omitting null/undefined fields
    const langfuseConfig: Record<string, string | number> = {
      model: modelTier,
    };

    if (config.max_output_tokens != null) {
      langfuseConfig.max_output_tokens = config.max_output_tokens;
    }
    if (config.verbosity) {
      langfuseConfig.verbosity = config.verbosity;
    }
    if (config.reasoning_effort) {
      langfuseConfig.reasoning_effort = config.reasoning_effort;
    }

    // Format as pretty JSON
    return JSON.stringify(langfuseConfig, null, 2);
  };

  const handleCopyLangfuseConfig = async (config: LLMConfig) => {
    try {
      const jsonString = generateLangfuseJson(config);
      await navigator.clipboard.writeText(jsonString);

      // Show visual feedback
      setCopiedConfig(config.name);
      setTimeout(() => setCopiedConfig(null), 2000);
    } catch (error) {
      console.error('Failed to copy Langfuse config:', error);
      alert('Failed to copy config to clipboard. Please ensure you are using HTTPS or localhost.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading configs...</div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">LLM Configurations</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your LLM model configurations for benchmarking.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
              Sort by:
            </label>
            <select
              id="sort-select"
              value={sortMethod}
              onChange={(e) => handleSortChange(e.target.value as SortMethod)}
              className="rounded-md border-gray-300 py-2 pl-3 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="model">Model</option>
              <option value="aiScore">AI Score</option>
              <option value="time">Avg Time</option>
              <option value="cost">Avg Cost</option>
              <option value="unacceptable">Unacceptable</option>
            </select>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
          >
            <Plus size={16} />
            New Config
          </button>
        </div>
      </div>

      <div className="mt-8 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <table className="min-w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">
                    Name
                  </th>
                  <SortableHeader column="model" label="Model" />
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Reasoning
                  </th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Verbosity
                  </th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Max Tokens
                  </th>
                  <SortableHeader column="time" label="Avg Time" />
                  <SortableHeader column="cost" label="Avg Cost" />
                  <SortableHeader column="aiScore" label="AI Score" />
                  <SortableHeader column="unacceptable" label="Unacceptable" />
                  <th className="relative py-3.5 pl-3 pr-4 sm:pr-0">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {configs.map((config) => (
                  <tr key={config.name} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-0">
                      {config.name}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.model}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.reasoning_effort || '-'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.verbosity || '-'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.max_output_tokens?.toLocaleString() || '-'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.avg_duration_seconds != null ? `${config.avg_duration_seconds.toFixed(1)}s` : '-'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.avg_cost_usd != null ? `$${config.avg_cost_usd.toFixed(4)}` : '-'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.avg_ai_score != null ? (
                        <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                          {config.avg_ai_score.toFixed(1)}/10
                          {config.ai_evaluation_count > 0 && (
                            <span className="ml-1 text-blue-600">({config.ai_evaluation_count})</span>
                          )}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {config.unacceptable_count > 0 ? (
                        <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                          {config.unacceptable_count}
                        </span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleEdit(config)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => handleCopyLangfuseConfig(config)}
                          className={`p-2 rounded transition-colors ${
                            copiedConfig === config.name
                              ? 'text-green-600 bg-green-50'
                              : 'text-purple-600 hover:bg-purple-50'
                          }`}
                          title={generateLangfuseJson(config)}
                        >
                          {copiedConfig === config.name ? (
                            <Check size={16} />
                          ) : (
                            <ClipboardCopy size={16} />
                          )}
                        </button>
                        <button
                          onClick={() => handleClone(config.name)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded"
                          title="Clone"
                        >
                          <Copy size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(config.name)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Config Editor Modal */}
      {showEditor && editingConfig && (
        <ConfigEditorModal
          config={editingConfig}
          isCreating={isCreating}
          onClose={() => {
            setShowEditor(false);
            setEditingConfig(null);
            setIsCreating(false);
          }}
          onSave={async () => {
            await fetchConfigs();
            setShowEditor(false);
            setEditingConfig(null);
            setIsCreating(false);
          }}
        />
      )}
    </div>
  );
}

function ConfigEditorModal({
  config,
  isCreating,
  onClose,
  onSave,
}: {
  config: LLMConfig;
  isCreating: boolean;
  onClose: () => void;
  onSave: () => void;
}) {
  const [formData, setFormData] = useState(config);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (isCreating) {
        await api.createConfig({
          name: formData.name,
          model: formData.model,
          max_output_tokens: formData.max_output_tokens || undefined,
          verbosity: formData.verbosity || undefined,
          reasoning_effort: formData.reasoning_effort || undefined,
          description: formData.description || undefined,
        });
      } else {
        await api.updateConfig(config.name, {
          model: formData.model,
          max_output_tokens: formData.max_output_tokens || undefined,
          verbosity: formData.verbosity || undefined,
          reasoning_effort: formData.reasoning_effort || undefined,
          description: formData.description || undefined,
        });
      }
      onSave();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save config');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">
            {isCreating ? 'Create Config' : `Edit Config: ${config.name}`}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name {isCreating && <span className="text-red-500">*</span>}
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={!isCreating}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="gpt-5">gpt-5</option>
              <option value="gpt-5-mini">gpt-5-mini</option>
              <option value="gpt-5-nano">gpt-5-nano</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reasoning Effort
            </label>
            <select
              value={formData.reasoning_effort || ''}
              onChange={(e) =>
                setFormData({ ...formData, reasoning_effort: e.target.value || null })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">None</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="minimal">Minimal</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Verbosity
            </label>
            <select
              value={formData.verbosity || ''}
              onChange={(e) => setFormData({ ...formData, verbosity: e.target.value || null })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">None</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Output Tokens
            </label>
            <input
              type="number"
              value={formData.max_output_tokens || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  max_output_tokens: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              min="1"
              step="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value || null })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Save size={16} />
              {saving ? 'Saving...' : isCreating ? 'Create' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
