interface RankingCardProps {
  experiment: {
    experiment_id: string;
    config_name: string;
    response: string;
    duration_seconds: number;
    estimated_cost_usd: number;
    total_tokens: number;
  };
  rank: number;
  aiScore?: number;
  aiRank?: number;
  aiComment?: string;
  isDragging: boolean;
  dragHandleProps?: any;
}

const getRankBadge = (rank: number) => {
  const badges = {
    1: { emoji: '🥇', color: 'text-yellow-600', bg: 'bg-yellow-50' },
    2: { emoji: '🥈', color: 'text-gray-600', bg: 'bg-gray-50' },
    3: { emoji: '🥉', color: 'text-orange-600', bg: 'bg-orange-50' },
  };
  return badges[rank as keyof typeof badges] || { emoji: '', color: 'text-gray-500', bg: 'bg-white' };
};

export function RankingCard({
  experiment,
  rank,
  aiScore,
  aiRank,
  aiComment,
  isDragging,
  dragHandleProps,
}: RankingCardProps) {
  const badge = getRankBadge(rank);

  return (
    <div
      className={`
        w-full h-[900px]
        bg-white rounded-lg shadow-md border border-gray-200
        flex flex-col
        transition-all duration-300
        ${isDragging ? 'scale-105 shadow-2xl opacity-80 rotate-2' : 'hover:shadow-lg cursor-grab active:cursor-grabbing'}
      `}
      {...dragHandleProps}
    >
      {/* Header - Sticky */}
      <div
        className={`
          ${badge.bg} ${badge.color}
          p-4 rounded-t-lg border-b border-gray-200
          flex items-center justify-between
          sticky top-0 z-10
        `}
      >
        <div className="flex items-center gap-2">
          <span className="text-2xl">{badge.emoji}</span>
          <div>
            <div className="font-bold text-lg">RANK #{rank}</div>
            <div className="text-sm font-medium truncate max-w-[200px]">
              {experiment.config_name}
            </div>
          </div>
        </div>
        {aiScore !== undefined && (
          <div className="text-right">
            <div className="text-xs text-gray-600">AI Score</div>
            <div className="text-lg font-bold">{aiScore.toFixed(1)}/10</div>
            {aiRank !== undefined && aiRank !== rank && (
              <div className="text-xs text-orange-600">AI: #{aiRank}</div>
            )}
          </div>
        )}
      </div>

      {/* AI Comment Section */}
      {aiComment && (
        <div className="bg-blue-50 border-b border-blue-200 p-3">
          <div className="flex items-start gap-2">
            <span className="text-blue-600 text-sm">🤖</span>
            <div className="flex-1">
              <div className="text-xs font-semibold text-blue-800 mb-1">AI Evaluation</div>
              <div className="text-sm text-blue-900 italic leading-relaxed">
                "{aiComment}"
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Response (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-gray-800 leading-relaxed text-base">
            {experiment.response}
          </div>
        </div>
      </div>

      {/* Footer - Metrics */}
      <div className="p-3 bg-gray-50 rounded-b-lg border-t border-gray-200 flex justify-around text-xs">
        <div className="flex items-center gap-1">
          <span>⏱</span>
          <span className="font-medium">{experiment.duration_seconds.toFixed(1)}s</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💰</span>
          <span className="font-medium">${experiment.estimated_cost_usd.toFixed(4)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>📊</span>
          <span className="font-medium">{experiment.total_tokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
