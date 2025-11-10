import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Edit2, Copy, Trash2, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { api } from '../api/client';

interface ReviewPromptCardProps {
  prompt: {
    prompt_id: string;
    name: string;
    description?: string;
    criteria: string[];
    default_model: string;
    created_at: string;
  };
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export function ReviewPromptCard({ prompt, onEdit, onDuplicate, onDelete }: ReviewPromptCardProps) {
  const [showActions, setShowActions] = useState(false);

  // Fetch stats for this prompt
  const { data: stats } = useQuery({
    queryKey: ['review-prompt-stats', prompt.prompt_id],
    queryFn: () => api.getReviewPromptStats(prompt.prompt_id),
    staleTime: 60000, // 1 minute
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow relative"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{prompt.name}</h3>
          {prompt.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{prompt.description}</p>
          )}
        </div>
        {showActions && (
          <div className="flex gap-1 ml-2">
            <button
              onClick={onEdit}
              className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
              title="Edit"
            >
              <Edit2 className="h-4 w-4" />
            </button>
            <button
              onClick={onDuplicate}
              className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded"
              title="Duplicate"
            >
              <Copy className="h-4 w-4" />
            </button>
            <button
              onClick={onDelete}
              className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
              title="Delete"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <span className="text-gray-700">
            {prompt.criteria.length} criteria
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Model:</span>
          <span className="text-gray-900 font-medium">{prompt.default_model}</span>
        </div>
      </div>

      {/* Criteria Tags */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {prompt.criteria.slice(0, 4).map((criterion, idx) => (
          <span
            key={idx}
            className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full"
          >
            {criterion}
          </span>
        ))}
        {prompt.criteria.length > 4 && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
            +{prompt.criteria.length - 4} more
          </span>
        )}
      </div>

      {/* Stats */}
      {stats && (
        <div className="border-t border-gray-200 pt-3 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5" />
              Used
            </span>
            <span className="font-medium text-gray-900">
              {stats.usage_count} time{stats.usage_count !== 1 ? 's' : ''}
            </span>
          </div>
          {stats.last_used && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                Last used
              </span>
              <span className="text-gray-900">{formatDate(stats.last_used)}</span>
            </div>
          )}
          {stats.average_score !== null && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Avg Score</span>
              <span className="font-medium text-gray-900">
                {stats.average_score.toFixed(1)}/10
              </span>
            </div>
          )}
        </div>
      )}

      {!stats?.usage_count && (
        <div className="border-t border-gray-200 pt-3">
          <p className="text-sm text-gray-500 italic">Never used</p>
        </div>
      )}
    </div>
  );
}
