import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, X, Save, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import PromptCard from '../components/PromptCard';
import type { ExperimentRun } from '../types/index';

interface Prompt {
  name: string;
  messages: any[];
}

interface PromptWithRuns {
  name: string;
  runs: ExperimentRun[];
}

export function Prompts() {
  const navigate = useNavigate();
  const [promptsWithRuns, setPromptsWithRuns] = useState<PromptWithRuns[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [viewMode, setViewMode] = useState<'preview' | 'edit'>('preview');

  useEffect(() => {
    fetchPromptsWithRuns();
  }, []);

  const fetchPromptsWithRuns = async () => {
    try {
      // Get list of all prompts
      const promptsList = await api.getPromptsList();

      // Fetch runs for each prompt
      const promptsData = await Promise.all(
        promptsList.map(async (promptName: string) => {
          try {
            const runs = await api.getRunsForPrompt(promptName);
            return { name: promptName, runs };
          } catch (error) {
            console.error(`Failed to fetch runs for ${promptName}:`, error);
            return { name: promptName, runs: [] };
          }
        })
      );

      setPromptsWithRuns(promptsData);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete prompt "${name}" and all its experiments?`)) return;

    try {
      await fetch(`http://localhost:8000/api/prompts/delete/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      await fetchPromptsWithRuns();
    } catch (error) {
      console.error('Failed to delete prompt:', error);
      alert('Failed to delete prompt');
    }
  };

  const handleRunExperiments = async (name: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/experiments/run-all-configs?prompt_name=${encodeURIComponent(name)}`,
        { method: 'POST' }
      );

      const data = await response.json();
      console.log('Started run:', data);

      // Refresh to show the new run
      await fetchPromptsWithRuns();

      // Poll for completion every 5 seconds
      const pollInterval = setInterval(async () => {
        await fetchPromptsWithRuns();
      }, 5000);

      // Stop polling after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 300000);
    } catch (error) {
      console.error('Failed to run configs:', error);
      alert('Failed to start experiments');
    }
  };

  const handleViewJSON = async (name: string) => {
    try {
      const promptData = await api.getPromptDetail(name);
      setEditingPrompt(promptData);
      setViewMode('preview');
      setIsCreatingNew(false);
      setShowEditor(true);
    } catch (error) {
      console.error('Failed to load prompt:', error);
      alert('Failed to load prompt');
    }
  };

  const handleEdit = async (name: string) => {
    try {
      const promptData = await api.getPromptDetail(name);
      setEditingPrompt(promptData);
      setViewMode('edit');
      setIsCreatingNew(false);
      setShowEditor(true);
    } catch (error) {
      console.error('Failed to load prompt:', error);
      alert('Failed to load prompt');
    }
  };

  const handleViewResults = (promptName: string, runId: string) => {
    navigate(`/compare/${promptName}?run_id=${runId}`);
  };

  const handleCreateNew = () => {
    setEditingPrompt({
      name: '',
      messages: [{ role: 'user', content: '' }],
    });
    setViewMode('edit');
    setIsCreatingNew(true);
    setShowEditor(true);
  };

  const handleSavePrompt = async () => {
    if (!editingPrompt) return;

    try {
      await api.savePrompt(editingPrompt.name, editingPrompt.messages);
      setShowEditor(false);
      setEditingPrompt(null);
      await fetchPromptsWithRuns();
    } catch (error) {
      console.error('Failed to save prompt:', error);
      alert('Failed to save prompt');
    }
  };

  const updatePromptName = (name: string) => {
    if (editingPrompt) {
      setEditingPrompt({ ...editingPrompt, name });
    }
  };

  const updateMessage = (index: number, field: 'role' | 'content', value: string) => {
    if (editingPrompt) {
      const newMessages = [...editingPrompt.messages];
      newMessages[index] = { ...newMessages[index], [field]: value };
      setEditingPrompt({ ...editingPrompt, messages: newMessages });
    }
  };

  const addMessage = () => {
    if (editingPrompt) {
      setEditingPrompt({
        ...editingPrompt,
        messages: [...editingPrompt.messages, { role: 'user', content: '' }],
      });
    }
  };

  const removeMessage = (index: number) => {
    if (editingPrompt) {
      const newMessages = editingPrompt.messages.filter((_, i) => i !== index);
      setEditingPrompt({ ...editingPrompt, messages: newMessages });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading prompts...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Prompt Library</h1>
        <button
          onClick={handleCreateNew}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Prompt
        </button>
      </div>

      {/* Prompts Grid */}
      {promptsWithRuns.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No prompts yet</h3>
          <p className="text-gray-500 mb-4">Create your first prompt to get started</p>
          <button
            onClick={handleCreateNew}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Prompt
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {promptsWithRuns.map((prompt) => (
            <PromptCard
              key={prompt.name}
              promptName={prompt.name}
              runs={prompt.runs}
              onRunExperiments={handleRunExperiments}
              onDeletePrompt={handleDelete}
              onViewJSON={handleViewJSON}
              onEdit={handleEdit}
              onViewResults={handleViewResults}
              onRunsUpdated={fetchPromptsWithRuns}
            />
          ))}
        </div>
      )}

      {/* Editor Modal */}
      {showEditor && editingPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">
                {isCreatingNew ? 'New Prompt' : viewMode === 'edit' ? 'Edit Prompt' : 'View Prompt'}
              </h2>
              <div className="flex gap-2">
                {viewMode === 'preview' && !isCreatingNew && (
                  <button
                    onClick={() => setViewMode('edit')}
                    className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                )}
                {viewMode === 'edit' && (
                  <button
                    onClick={handleSavePrompt}
                    className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center gap-1"
                  >
                    <Save className="w-4 h-4" />
                    Save
                  </button>
                )}
                <button
                  onClick={() => {
                    setShowEditor(false);
                    setEditingPrompt(null);
                  }}
                  className="p-1.5 text-gray-500 hover:text-gray-700 rounded hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {viewMode === 'edit' ? (
                <div className="space-y-4">
                  {/* Prompt Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prompt Name
                    </label>
                    <input
                      type="text"
                      value={editingPrompt.name}
                      onChange={(e) => updatePromptName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="my-prompt-name"
                    />
                  </div>

                  {/* Messages */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Messages
                      </label>
                      <button
                        onClick={addMessage}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        + Add Message
                      </button>
                    </div>

                    <div className="space-y-3">
                      {editingPrompt.messages.map((message, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex gap-2 mb-2">
                            <select
                              value={message.role}
                              onChange={(e) => updateMessage(index, 'role', e.target.value)}
                              className="px-3 py-1.5 border border-gray-300 rounded bg-white text-sm"
                            >
                              <option value="system">system</option>
                              <option value="user">user</option>
                              <option value="assistant">assistant</option>
                            </select>
                            {editingPrompt.messages.length > 1 && (
                              <button
                                onClick={() => removeMessage(index)}
                                className="ml-auto p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                          <textarea
                            value={message.content}
                            onChange={(e) => updateMessage(index, 'content', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                            rows={4}
                            placeholder="Message content..."
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                // Preview Mode
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Prompt Name</h3>
                    <p className="text-gray-900 font-mono">{editingPrompt.name}</p>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Messages</h3>
                    <div className="space-y-3">
                      {editingPrompt.messages.map((message, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-3">
                          <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                            {message.role}
                          </div>
                          <div className="text-sm text-gray-900 whitespace-pre-wrap font-mono">
                            {message.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
