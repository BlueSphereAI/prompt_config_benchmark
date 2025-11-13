import { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  SortableContext,
  horizontalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { RankingCard } from './RankingCard';

interface Experiment {
  experiment_id: string;
  config_name: string;
  response: string;
  duration_seconds: number;
  estimated_cost_usd: number;
  total_tokens: number;
  is_acceptable?: boolean;
}

interface AIEvaluation {
  experiment_id: string;
  ai_rank: number;
  overall_score: number;
  justification: string;
  criteria_scores?: Record<string, number>;
}

interface DragCarouselProps {
  experiments: Experiment[];
  aiEvaluations?: Map<string, AIEvaluation>;
  humanRankedIds: string[];
  onReorder: (newOrder: string[]) => void;
  onToggleAcceptability?: (experimentId: string, isAcceptable: boolean) => void;
}

function SortableCard({
  experiment,
  humanRank,
  aiEval,
  onToggleAcceptability,
}: {
  experiment: Experiment;
  humanRank: number;
  aiEval?: AIEvaluation;
  onToggleAcceptability?: (experimentId: string, isAcceptable: boolean) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: experiment.experiment_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <RankingCard
        experiment={experiment}
        humanRank={humanRank}
        aiScore={aiEval?.overall_score}
        aiRank={aiEval?.ai_rank}
        aiComment={aiEval?.justification}
        aiCriteriaScores={aiEval?.criteria_scores}
        isDragging={isDragging}
        dragHandleProps={listeners}
        onToggleAcceptability={onToggleAcceptability}
      />
    </div>
  );
}

export function DragCarousel({
  experiments,
  aiEvaluations,
  humanRankedIds,
  onReorder,
  onToggleAcceptability,
}: DragCarouselProps) {
  const [items, setItems] = useState(experiments);

  // Update items when experiments prop changes (e.g., after acceptability toggle)
  useEffect(() => {
    setItems(experiments);
  }, [experiments]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => item.experiment_id === active.id);
      const newIndex = items.findIndex((item) => item.experiment_id === over.id);

      const newItems = arrayMove(items, oldIndex, newIndex);
      setItems(newItems);
      onReorder(newItems.map((item) => item.experiment_id));
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <div className="relative">
        <SortableContext
          items={items.map((exp) => exp.experiment_id)}
          strategy={horizontalListSortingStrategy}
        >
          {/* Responsive grid: 1-5 cols based on screen size */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 3xl:grid-cols-5 gap-6">
            {items.map((exp) => {
              // Find human rank for this experiment
              const humanRank = humanRankedIds.indexOf(exp.experiment_id) + 1;
              return (
                <SortableCard
                  key={exp.experiment_id}
                  experiment={exp}
                  humanRank={humanRank}
                  aiEval={aiEvaluations?.get(exp.experiment_id)}
                  onToggleAcceptability={onToggleAcceptability}
                />
              );
            })}
          </div>
        </SortableContext>
      </div>
    </DndContext>
  );
}
