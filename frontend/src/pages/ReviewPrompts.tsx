import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { ReviewPromptCard } from '../components/ReviewPromptCard';
import { ReviewPromptEditor } from '../components/ReviewPromptEditor';

export default function ReviewPrompts() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [showEditor, setShowEditor] = useState(false);
  const [editingPromptId, setEditingPromptId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Fetch all review prompts
  const { data: reviewPrompts, isLoading, error } = useQuery({
    queryKey: ['review-prompts'],
    queryFn: () => api.getReviewPrompts(true),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (promptId: string) => api.deleteReviewPrompt(promptId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-prompts'] });
      setShowDeleteConfirm(null);
    },
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: ({ promptId, newName }: { promptId: string; newName: string }) =>
      api.duplicateReviewPrompt(promptId, newName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-prompts'] });
    },
  });

  const handleEdit = (promptId: string) => {
    setEditingPromptId(promptId);
    setShowEditor(true);
  };

  const handleDuplicate = (promptId: string, name: string) => {
    const newName = prompt(`Enter name for duplicated prompt:`, `${name} (Copy)`);
    if (newName) {
      duplicateMutation.mutate({ promptId, newName });
    }
  };

  const handleDelete = (promptId: string) => {
    setShowDeleteConfirm(promptId);
  };

  const confirmDelete = () => {
    if (showDeleteConfirm) {
      deleteMutation.mutate(showDeleteConfirm);
    }
  };

  const handleCreateNew = () => {
    setEditingPromptId(null);
    setShowEditor(true);
  };

  const handleCloseEditor = () => {
    setShowEditor(false);
    setEditingPromptId(null);
  };

  // Filter prompts based on search
  const filteredPrompts = reviewPrompts?.filter(
    (prompt: any) =>
      prompt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prompt.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600" />
          <p className="mt-2 text-gray-600">Loading review prompts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Review Prompts</h3>
        <p className="text-red-600">
          {error instanceof Error ? error.message : 'Failed to load review prompts'}
        </p>
      </div>
    );
  }

  return (
    <div className="w-full px-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Review Prompt Library</h1>
            <p className="text-gray-600 mt-1">
              Manage templates for AI-powered configuration evaluation
            </p>
          </div>
          <button
            onClick={handleCreateNew}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-5 w-5" />
            New Review Prompt
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <span className="font-semibold">💡 Review prompts</span> define how GPT-5 evaluates and
          ranks your LLM configurations. Each prompt specifies evaluation criteria and output format.
        </p>
      </div>

      {/* Review Prompt Grid */}
      {filteredPrompts && filteredPrompts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPrompts.map((prompt: any) => (
            <ReviewPromptCard
              key={prompt.prompt_id}
              prompt={prompt}
              onEdit={() => handleEdit(prompt.prompt_id)}
              onDuplicate={() => handleDuplicate(prompt.prompt_id, prompt.name)}
              onDelete={() => handleDelete(prompt.prompt_id)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600 mb-4">
            {searchQuery ? 'No review prompts match your search' : 'No review prompts available'}
          </p>
          {!searchQuery && (
            <button
              onClick={handleCreateNew}
              className="text-blue-600 hover:underline font-medium"
            >
              Create your first review prompt
            </button>
          )}
        </div>
      )}

      {/* Editor Modal */}
      {showEditor && (
        <ReviewPromptEditor
          promptId={editingPromptId}
          onClose={handleCloseEditor}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['review-prompts'] });
            handleCloseEditor();
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Confirm Delete</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this review prompt? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
