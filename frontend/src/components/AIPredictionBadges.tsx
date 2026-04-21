// Layer C — ML Prediction Badges shown on every task card
// Fetches delay, duration, and bottleneck predictions from ai-service

import { useEffect, useState } from 'react';
import { predictDelay, predictDuration, predictBottleneck } from '@/api/aiClient';
import { AlertTriangle, Clock, GitMerge, Loader2, Cpu } from 'lucide-react';

interface Props {
  task: any;
  compact?: boolean; // slim mode for kanban columns
}

interface Predictions {
  delay: any | null;
  duration: any | null;
  bottleneck: any | null;
}

const riskColor: Record<string, string> = {
  HIGH:   'bg-red-50 text-red-600 border-red-200',
  MEDIUM: 'bg-amber-50 text-amber-600 border-amber-200',
  LOW:    'bg-emerald-50 text-emerald-600 border-emerald-200',
};

export default function AIPredictionBadges({ task, compact = false }: Props) {
  const [preds, setPreds] = useState<Predictions>({ delay: null, duration: null, bottleneck: null });
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState(false);

  useEffect(() => {
    // Only fetch tasks that have ML metadata (generated via AI or with complexity_label)
    if (!task.complexity_label && !task.story_points) return;
    if (fetched) return;

    let cancelled = false;
    setLoading(true);

    Promise.all([
      predictDelay(task),
      predictDuration(task),
      predictBottleneck(task),
    ]).then(([delay, duration, bottleneck]) => {
      if (!cancelled) {
        setPreds({ delay, duration, bottleneck });
        setFetched(true);
        setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [task.id]);

  if (loading) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-gray-300 font-medium">
        <Loader2 className="w-2.5 h-2.5 animate-spin" />
        {!compact && 'AI loading…'}
      </span>
    );
  }

  if (!fetched) return null;

  return (
    <div className="flex flex-wrap gap-1 items-center mt-1.5">
      {/* AI label */}
      <span className="inline-flex items-center gap-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-500 border border-violet-200 bg-violet-50 px-1.5 py-0.5 rounded">
        <Cpu className="w-2.5 h-2.5" />
        AI
      </span>

      {/* Delay Badge */}
      {preds.delay && (
        <span
          title={`Delay probability: ${Math.round((preds.delay.probability || 0) * 100)}%`}
          className={`inline-flex items-center gap-0.5 text-[10px] font-semibold border px-1.5 py-0.5 rounded ${
            riskColor[preds.delay.risk_level] || riskColor.LOW
          }`}
        >
          <AlertTriangle className="w-2.5 h-2.5" />
          {compact
            ? `${Math.round((preds.delay.probability || 0) * 100)}%`
            : `Delay ${Math.round((preds.delay.probability || 0) * 100)}%`}
        </span>
      )}

      {/* Duration Badge */}
      {preds.duration && preds.duration.predicted_actual_hours != null && (
        <span
          title={`Predicted: ${preds.duration.predicted_actual_hours}h (estimated: ${preds.duration.original_estimate_hours}h)`}
          className={`inline-flex items-center gap-0.5 text-[10px] font-semibold border px-1.5 py-0.5 rounded ${
            preds.duration.delta_hours > 4
              ? 'bg-orange-50 text-orange-600 border-orange-200'
              : 'bg-blue-50 text-blue-600 border-blue-200'
          }`}
        >
          <Clock className="w-2.5 h-2.5" />
          {compact
            ? `${preds.duration.predicted_actual_hours}h`
            : `~${preds.duration.predicted_actual_hours}h actual`}
        </span>
      )}

      {/* Bottleneck Badge */}
      {preds.bottleneck?.is_bottleneck && (
        <span
          title={`Bottleneck risk: ${preds.bottleneck.risk_level}`}
          className="inline-flex items-center gap-0.5 text-[10px] font-semibold border px-1.5 py-0.5 rounded bg-red-50 text-red-600 border-red-200"
        >
          <GitMerge className="w-2.5 h-2.5" />
          {compact ? 'BN' : 'Bottleneck'}
        </span>
      )}
    </div>
  );
}
