import { useEffect, useState } from 'react';
import apiClient from '@/api/client';
import { Card, CardContent } from '@/components/ui/card';
import {
  Loader2, Star, GitFork, Eye, AlertCircle, Code2, GitBranch,
  GitPullRequest, Box, Users, ExternalLink, RefreshCw,
  Tag, Lock, GitCommit, Package, Calendar
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// ─── Types ────────────────────────────────────────────────────────────────────
interface Analytics {
  overview: RepoOverview;
  commit_timeline: { date: string; count: number }[];
  commit_by_weekday: { day: string; count: number }[];
  total_commits_90d: number;
  pull_requests: { open: number; closed: number; merged: number; recent: PRItem[] };
  issues: { open: number; closed: number; top_labels: [string, number][] };
  contributors: ContributorItem[];
  languages: LangItem[];
  branches: BranchItem[];
  releases: ReleaseItem[];
}
interface RepoOverview {
  full_name: string; description: string; stars: number; forks: number;
  watchers: number; open_issues: number; size_kb: number; primary_language: string;
  default_branch: string; html_url: string; created_at: string; updated_at: string;
  license?: string; visibility: string; topics: string[];
}
interface PRItem { number: number; title: string; state: string; author: string; created_at: string; }
interface ContributorItem { login: string; avatar_url: string; contributions: number; profile_url: string; }
interface LangItem { name: string; bytes: number; percentage: number; color: string; }
interface BranchItem { name: string; protected: boolean; sha: string; }
interface ReleaseItem { tag: string; name: string; prerelease: boolean; published_at: string; url: string; }

// ─── Helpers ──────────────────────────────────────────────────────────────────
function timeAgo(d: string) {
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function fmtNum(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

// ─── Commit spark-chart (mini bars) ──────────────────────────────────────────
function SparkBars({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  // Show only last 60 entries (avoid overflow at smaller widths)
  const visible = data.slice(-60);
  return (
    <div className="flex items-end gap-px h-12" title="Commits per day">
      {visible.map((d, i) => (
        <div
          key={i}
          className="flex-1 rounded-sm transition-all"
          style={{
            height: `${Math.max((d.count / max) * 100, d.count > 0 ? 8 : 3)}%`,
            backgroundColor: d.count === 0 ? '#f3f4f6' : `rgba(17,24,39,${0.3 + (d.count / max) * 0.7})`,
          }}
          title={`${d.date}: ${d.count} commit${d.count !== 1 ? 's' : ''}`}
        />
      ))}
    </div>
  );
}

// ─── Horizontal bar ───────────────────────────────────────────────────────────
function HBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
}

// ─── Donut segment (SVG) ──────────────────────────────────────────────────────
function DonutChart({ segments }: { segments: { value: number; color: string; label: string }[] }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  let cumulativePct = 0;
  const r = 40, cx = 50, cy = 50, stroke = 14;
  const circumference = 2 * Math.PI * r;

  return (
    <svg viewBox="0 0 100 100" className="w-24 h-24">
      {segments.map((seg, i) => {
        const pct = seg.value / total;
        const offset = circumference * (1 - cumulativePct);
        cumulativePct += pct;
        return (
          <circle
            key={i}
            r={r} cx={cx} cy={cy}
            fill="none"
            stroke={seg.color}
            strokeWidth={stroke}
            strokeDasharray={`${pct * circumference} ${circumference}`}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ transition: 'all 0.5s ease' }}
          >
            <title>{seg.label}: {seg.value}</title>
          </circle>
        );
      })}
      <text x="50" y="54" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#111827">
        {total}
      </text>
    </svg>
  );
}

// ─── Weekday bar chart ────────────────────────────────────────────────────────
function WeekdayBars({ data }: { data: { day: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  return (
    <div className="flex items-end justify-between gap-1.5 h-16 px-1">
      {data.map((d, i) => (
        <div key={i} className="flex flex-col items-center gap-1 flex-1">
          <div
            className="w-full rounded-t-sm bg-gray-900 opacity-80 transition-all duration-500"
            style={{ height: `${Math.max((d.count / max) * 52, d.count > 0 ? 6 : 2)}px` }}
            title={`${d.day}: ${d.count} commits`}
          />
          <span className="text-[9px] font-semibold text-gray-400">{d.day}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function GitHubAnalytics({ projectId }: { projectId: string }) {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const fetch = async (silent = false) => {
    silent ? setRefreshing(true) : setLoading(true);
    setError('');
    try {
      const res = await apiClient.get(`/github/analytics/${projectId}`);
      setData(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetch(); }, [projectId]);

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
    </div>
  );

  if (error) return (
    <div className="py-12 text-center text-red-500 text-sm">
      <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
      {error}
    </div>
  );

  if (!data) return null;

  const { overview: ov, pull_requests: prs, issues, contributors, languages, branches, releases } = data;

  return (
    <div className="space-y-5">

      {/* ── Header strip ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-gray-900">{ov.full_name}</h2>
            <a href={ov.html_url} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-900">
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
              {ov.visibility}
            </span>
            {ov.license && (
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">
                {ov.license}
              </span>
            )}
          </div>
          {ov.description && <p className="text-xs text-gray-400 mt-0.5">{ov.description}</p>}
        </div>
        <Button
          variant="outline" size="sm"
          onClick={() => fetch(true)}
          disabled={refreshing}
          className="h-8 w-8 p-0 border-gray-200"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* ── Stat cards row ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: <Star className="w-4 h-4 text-amber-500" />,     label: 'Stars',        value: fmtNum(ov.stars) },
          { icon: <GitFork className="w-4 h-4 text-blue-500" />,   label: 'Forks',        value: fmtNum(ov.forks) },
          { icon: <Eye className="w-4 h-4 text-purple-500" />,     label: 'Watchers',     value: fmtNum(ov.watchers) },
          { icon: <GitCommit className="w-4 h-4 text-gray-600" />, label: 'Commits (90d)', value: fmtNum(data.total_commits_90d) },
        ].map(s => (
          <Card key={s.label} className="sleek-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">{s.icon}<span className="text-xs font-medium text-gray-500">{s.label}</span></div>
              <p className="text-2xl font-bold text-gray-900">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Topics */}
      {ov.topics?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {ov.topics.map(t => (
            <span key={t} className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* ── Commit activity ───────────────────────────────────────────────── */}
      <Card className="sleek-card">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-gray-500" /> Commit Activity
              <span className="text-xs font-normal text-gray-400">last 90 days</span>
            </h3>
            <span className="text-xs font-bold text-gray-900 bg-gray-100 px-2 py-0.5 rounded-full">
              {data.total_commits_90d} commits
            </span>
          </div>
          <SparkBars data={data.commit_timeline} />
          <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-50">
            <div>
              <p className="text-[10px] font-bold uppercase text-gray-400 mb-2">By Day of Week</p>
              <WeekdayBars data={data.commit_by_weekday} />
            </div>
            <div className="space-y-1.5">
              <p className="text-[10px] font-bold uppercase text-gray-400">Peak Days</p>
              {[...data.commit_by_weekday]
                .sort((a, b) => b.count - a.count)
                .slice(0, 3)
                .map((d, i) => (
                  <div key={d.day} className="flex items-center justify-between">
                    <span className="text-xs text-gray-600 font-medium">{d.day}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-gray-900 rounded-full"
                          style={{ width: `${(d.count / Math.max(...data.commit_by_weekday.map(x => x.count), 1)) * 100}%` }} />
                      </div>
                      <span className="text-xs font-bold text-gray-700">{d.count}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── PRs + Issues row ──────────────────────────────────────────────── */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Pull Requests */}
        <Card className="sleek-card">
          <CardContent className="p-4 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <GitPullRequest className="w-4 h-4 text-purple-500" /> Pull Requests
            </h3>
            <div className="flex items-center gap-4">
              <DonutChart segments={[
                { value: prs.open,   color: '#22c55e', label: 'Open' },
                { value: prs.merged, color: '#8b5cf6', label: 'Merged' },
                { value: prs.closed, color: '#9ca3af', label: 'Closed' },
              ]} />
              <div className="space-y-2 flex-1">
                {[
                  { label: 'Open',   value: prs.open,   color: '#22c55e' },
                  { label: 'Merged', value: prs.merged, color: '#8b5cf6' },
                  { label: 'Closed', value: prs.closed, color: '#9ca3af' },
                ].map(s => (
                  <div key={s.label} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                    <span className="text-xs text-gray-500 flex-1">{s.label}</span>
                    <span className="text-xs font-bold text-gray-900">{s.value}</span>
                  </div>
                ))}
              </div>
            </div>
            {prs.recent?.length > 0 && (
              <div className="space-y-1.5 border-t border-gray-50 pt-3">
                <p className="text-[10px] font-bold uppercase text-gray-400 mb-2">Recent</p>
                {prs.recent.slice(0, 4).map(pr => (
                  <div key={pr.number} className="flex items-start gap-2">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 mt-0.5 ${
                      pr.state === 'open' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>{pr.state}</span>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-gray-800 truncate">#{pr.number} {pr.title}</p>
                      <p className="text-[10px] text-gray-400">{pr.author} · {pr.created_at ? timeAgo(pr.created_at) : ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Issues */}
        <Card className="sleek-card">
          <CardContent className="p-4 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Box className="w-4 h-4 text-orange-500" /> Issues
            </h3>
            <div className="flex items-center gap-4">
              <DonutChart segments={[
                { value: issues.open,   color: '#f97316', label: 'Open' },
                { value: issues.closed, color: '#9ca3af', label: 'Closed' },
              ]} />
              <div className="space-y-2 flex-1">
                {[
                  { label: 'Open',   value: issues.open,   color: '#f97316' },
                  { label: 'Closed', value: issues.closed, color: '#9ca3af' },
                ].map(s => (
                  <div key={s.label} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                    <span className="text-xs text-gray-500 flex-1">{s.label}</span>
                    <span className="text-xs font-bold text-gray-900">{s.value}</span>
                  </div>
                ))}
              </div>
            </div>
            {issues.top_labels?.length > 0 && (
              <div className="border-t border-gray-50 pt-3">
                <p className="text-[10px] font-bold uppercase text-gray-400 mb-2">Top Labels</p>
                <div className="flex flex-wrap gap-1.5">
                  {issues.top_labels.map(([name, count]) => (
                    <span key={name} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                      {name} <span className="font-bold">{count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Languages ─────────────────────────────────────────────────────── */}
      {languages.length > 0 && (
        <Card className="sleek-card">
          <CardContent className="p-4 space-y-3">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-blue-500" /> Languages
            </h3>
            {/* Stacked bar */}
            <div className="flex h-3 rounded-full overflow-hidden gap-px">
              {languages.map(l => (
                <div
                  key={l.name}
                  style={{ width: `${l.percentage}%`, backgroundColor: l.color }}
                  title={`${l.name}: ${l.percentage}%`}
                  className="transition-all duration-500"
                />
              ))}
            </div>
            {/* Legend */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              {languages.map(l => (
                <div key={l.name} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: l.color }} />
                  <span className="text-xs font-medium text-gray-700 flex-1">{l.name}</span>
                  <span className="text-xs font-bold text-gray-500">{l.percentage}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Contributors ──────────────────────────────────────────────────── */}
      {contributors.length > 0 && (
        <Card className="sleek-card">
          <CardContent className="p-4 space-y-3">
            <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-500" /> Top Contributors
            </h3>
            <div className="space-y-2">
              {contributors.map((c, i) => {
                const maxContrib = contributors[0]?.contributions || 1;
                return (
                  <div key={c.login} className="flex items-center gap-3">
                    <span className="text-xs font-bold text-gray-400 w-4 text-right">{i + 1}</span>
                    <img
                      src={c.avatar_url}
                      alt={c.login}
                      className="w-7 h-7 rounded-full flex-shrink-0 bg-gray-100"
                      onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                    <a
                      href={c.profile_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-semibold text-gray-800 hover:underline w-28 truncate flex-shrink-0"
                    >
                      {c.login}
                    </a>
                    <div className="flex-1">
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gray-800 rounded-full transition-all duration-700"
                          style={{ width: `${(c.contributions / maxContrib) * 100}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-xs font-bold text-gray-600 flex-shrink-0 w-10 text-right">
                      {fmtNum(c.contributions)}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Branches + Releases row ───────────────────────────────────────── */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Branches */}
        {branches.length > 0 && (
          <Card className="sleek-card">
            <CardContent className="p-4 space-y-2">
              <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-blue-500" /> Branches
                <span className="text-xs font-normal text-gray-400">{branches.length}</span>
              </h3>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {branches.map(b => (
                  <div key={b.name} className="flex items-center gap-2 py-1 border-b border-gray-50 last:border-0">
                    <GitBranch className="w-3.5 h-3.5 text-gray-300 flex-shrink-0" />
                    <span className="text-xs font-semibold text-gray-800 flex-1 truncate">{b.name}</span>
                    {b.protected && (
                      <span className="flex items-center gap-0.5 text-[10px] text-amber-600 font-semibold">
                        <Lock className="w-2.5 h-2.5" /> protected
                      </span>
                    )}
                    {b.name === ov.default_branch && (
                      <span className="text-[10px] font-semibold text-emerald-600">default</span>
                    )}
                    <code className="text-[10px] text-gray-400 font-mono">{b.sha}</code>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Releases */}
        {releases.length > 0 && (
          <Card className="sleek-card">
            <CardContent className="p-4 space-y-2">
              <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                <Package className="w-4 h-4 text-indigo-500" /> Releases
              </h3>
              <div className="space-y-2">
                {releases.map(r => (
                  <a
                    key={r.tag}
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 py-1.5 border-b border-gray-50 last:border-0 hover:bg-gray-50 rounded-md px-1 transition-colors group"
                  >
                    <Tag className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <span className="text-xs font-bold text-gray-800 group-hover:underline">{r.tag}</span>
                    {r.prerelease && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-600">pre</span>
                    )}
                    <span className="flex-1 text-xs text-gray-500 truncate">{r.name !== r.tag ? r.name : ''}</span>
                    <span className="text-[10px] text-gray-400 flex items-center gap-0.5 flex-shrink-0">
                      <Calendar className="w-2.5 h-2.5" />
                      {r.published_at ? fmtDate(r.published_at) : ''}
                    </span>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* ── Repo meta footer ──────────────────────────────────────────────── */}
      <div className="text-center text-[11px] text-gray-300 pb-2">
        Created {fmtDate(ov.created_at)} · Last updated {timeAgo(ov.updated_at)} · {Math.round(ov.size_kb / 1024 * 10) / 10} MB
      </div>
    </div>
  );
}
