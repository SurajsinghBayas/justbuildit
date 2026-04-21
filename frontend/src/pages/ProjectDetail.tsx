import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import apiClient from '@/api/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/Navbar';
import GitHubPanel from '@/components/GitHubPanel';
import { ShowMoreText } from '@/components/ui/ShowMoreText';
import {
  ArrowLeft, Briefcase, CheckSquare, Plus, Loader2, Sparkles,
  Clock, AlertTriangle, Trash2, GitBranch,
  CheckCircle2, Circle, AlertCircle, Zap
} from 'lucide-react';

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const STATUSES = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'];

const priorityConfig: Record<string, { color: string; IconComp: React.FC<{ className?: string }> }> = {
  LOW:      { color: 'bg-slate-100 text-slate-600 border-slate-200', IconComp: Circle },
  MEDIUM:   { color: 'bg-blue-50 text-blue-600 border-blue-200',     IconComp: AlertCircle },
  HIGH:     { color: 'bg-orange-50 text-orange-600 border-orange-200', IconComp: AlertTriangle },
  CRITICAL: { color: 'bg-red-50 text-red-600 border-red-200',        IconComp: Zap },
};

const statusConfig: Record<string, { color: string; IconComp: React.FC<{ className?: string }> }> = {
  TODO:        { color: 'bg-gray-100 text-gray-600',       IconComp: Circle },
  IN_PROGRESS: { color: 'bg-blue-100 text-blue-700',       IconComp: Clock },
  IN_REVIEW:   { color: 'bg-purple-100 text-purple-700',   IconComp: AlertCircle },
  DONE:        { color: 'bg-emerald-100 text-emerald-700', IconComp: CheckCircle2 },
};

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Active tab: 'board' | 'github'
  const [activeTab, setActiveTab] = useState<'board' | 'github'>('board');

  // Create task form
  const [createOpen, setCreateOpen] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskPriority, setTaskPriority] = useState('MEDIUM');
  const [taskStatus, setTaskStatus] = useState('TODO');
  const [taskEstimate, setTaskEstimate] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // AI generate
  const [aiOpen, setAiOpen] = useState(false);
  const [aiCount, setAiCount] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [aiPreviewTasks, setAiPreviewTasks] = useState<any[]>([]);
  const [selectedAiTasks, setSelectedAiTasks] = useState<Set<number>>(new Set());
  const [aiStep, setAiStep] = useState<'generate' | 'review'>('generate');
  const [isSavingAi, setIsSavingAi] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [pRes, tRes] = await Promise.all([
        apiClient.get(`/projects/${id}`),
        apiClient.get(`/tasks/?project_id=${id}`),
      ]);
      setProject(pRes.data);
      setTasks(tRes.data);
    } catch {
      navigate('/projects');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await apiClient.post('/tasks/', {
        title: taskTitle,
        description: taskDesc,
        priority: taskPriority,
        status: taskStatus,
        estimated_time: taskEstimate ? parseFloat(taskEstimate) : null,
        project_id: id,
      });
      setCreateOpen(false);
      setTaskTitle('');
      setTaskDesc('');
      setTaskPriority('MEDIUM');
      setTaskStatus('TODO');
      setTaskEstimate('');
      fetchAll();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create task');
    } finally {
      setIsCreating(false);
    }
  };

  const handleAiGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await apiClient.post('/tasks/ai-generate', {
        project_name: project?.name,
        project_description: project?.description,
        count: aiCount,
      });
      setAiPreviewTasks(res.data.tasks);
      setSelectedAiTasks(new Set(res.data.tasks.map((_: any, i: number) => i)));
      setAiStep('review');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'AI generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveAiTasks = async () => {
    setIsSavingAi(true);
    const toSave = aiPreviewTasks.filter((_, i) => selectedAiTasks.has(i));
    try {
      await Promise.all(
        toSave.map((t: any) =>
          apiClient.post('/tasks/', {
            title: t.title,
            description: t.description,
            priority: t.priority,
            status: 'TODO',
            estimated_time: t.estimated_time,
            project_id: id,
          })
        )
      );
      setAiOpen(false);
      setAiStep('generate');
      setAiPreviewTasks([]);
      fetchAll();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to save tasks');
    } finally {
      setIsSavingAi(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Delete this task?')) return;
    try {
      await apiClient.delete(`/tasks/${taskId}`);
      setTasks(tasks.filter((t) => t.id !== taskId));
    } catch {}
  };

  const handleUpdateStatus = async (taskId: string, newStatus: string) => {
    try {
      const res = await apiClient.patch(`/tasks/${taskId}/status`, { status: newStatus });
      setTasks(tasks.map((t) => (t.id === taskId ? res.data : t)));
    } catch {}
  };

  const toggleAiTask = (i: number) => {
    setSelectedAiTasks((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  const priorityWeight: Record<string, number> = {
    CRITICAL: 4,
    HIGH: 3,
    MEDIUM: 2,
    LOW: 1,
  };

  const grouped = STATUSES.reduce<Record<string, any[]>>((acc, s) => {
    acc[s] = tasks
      .filter((t) => t.status === s)
      .sort((a, b) => {
        const wA = priorityWeight[a.priority] || 0;
        const wB = priorityWeight[b.priority] || 0;
        return wB - wA;
      });
    return acc;
  }, {});

  const totalTasks = tasks.length;
  const doneTasks = tasks.filter((t) => t.status === 'DONE').length;
  const progress = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0;

  const TAB_CLASSES = (tab: string) =>
    `px-4 py-2 text-sm font-semibold border-b-2 transition-colors cursor-pointer ${
      activeTab === tab
        ? 'border-gray-900 text-gray-900'
        : 'border-transparent text-gray-400 hover:text-gray-700'
    }`;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Navbar />

      {/* Breadcrumb + Action bar */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-2.5 flex items-center justify-between">
          {/* Back link */}
          <Link
            to="/projects"
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Projects
          </Link>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {/* AI Generate Dialog */}
            <Dialog
              open={aiOpen}
              onOpenChange={(o) => {
                setAiOpen(o);
                if (!o) {
                  setAiStep('generate');
                  setAiPreviewTasks([]);
                }
              }}
            >
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  className="border-purple-200 text-purple-700 hover:bg-purple-50 text-sm h-9 gap-2"
                >
                  <Sparkles className="w-4 h-4" /> AI Generate Tasks
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[560px] bg-white">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600" /> AI Task Generator
                  </DialogTitle>
                </DialogHeader>

                {aiStep === 'generate' ? (
                  <div className="space-y-5 mt-4">
                    <div className="bg-purple-50 border border-purple-100 rounded-lg p-4">
                      <p className="text-sm text-purple-800 font-medium">
                        Generating tasks for:{' '}
                        <span className="font-bold">{project?.name}</span>
                      </p>
                      {project?.description && (
                        <p className="text-xs text-purple-600 mt-1">{project.description}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Number of tasks to generate</Label>
                      <div className="flex items-center gap-3">
                        {[3, 5, 7, 10].map((n) => (
                          <button
                            key={n}
                            type="button"
                            onClick={() => setAiCount(n)}
                            className={`w-12 h-10 rounded-lg border text-sm font-semibold transition-all ${
                              aiCount === n
                                ? 'bg-gray-900 text-white border-gray-900'
                                : 'bg-white text-gray-700 border-gray-200 hover:border-gray-400'
                            }`}
                          >
                            {n}
                          </button>
                        ))}
                      </div>
                    </div>
                    <Button
                      onClick={handleAiGenerate}
                      disabled={isGenerating}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white gap-2"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Analyzing project...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" /> Generate {aiCount} Tasks
                        </>
                      )}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4 mt-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-700">
                        {selectedAiTasks.size} of {aiPreviewTasks.length} tasks selected
                      </p>
                      <button
                        onClick={() => setAiStep('generate')}
                        className="text-xs text-gray-500 hover:text-gray-900 underline"
                      >
                        Regenerate
                      </button>
                    </div>
                    <div className="space-y-2 max-h-80 overflow-y-auto">
                      {aiPreviewTasks.map((t: any, i: number) => {
                        const pc = priorityConfig[t.priority] || priorityConfig.MEDIUM;
                        const selected = selectedAiTasks.has(i);
                        return (
                          <div
                            key={i}
                            onClick={() => toggleAiTask(i)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${
                              selected
                                ? 'border-gray-900 bg-gray-50'
                                : 'border-gray-200 bg-white opacity-60'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-gray-900 truncate">
                                  {t.title}
                                </p>
                                {t.description && (
                                  <ShowMoreText text={t.description} lines={2} className="mt-0.5" />
                                )}
                              </div>
                              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                <span
                                  className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border flex items-center gap-1 ${pc.color}`}
                                >
                                  <pc.IconComp className="w-3 h-3" />
                                  {t.priority}
                                </span>
                                {t.estimated_time && (
                                  <span className="text-[10px] text-gray-400">
                                    {t.estimated_time}h
                                  </span>
                                )}
                              </div>
                            </div>
                            <div
                              className={`mt-2 w-4 h-4 rounded border-2 flex items-center justify-center ml-auto ${
                                selected
                                  ? 'bg-gray-900 border-gray-900'
                                  : 'border-gray-300'
                              }`}
                            >
                              {selected && <CheckCircle2 className="w-3 h-3 text-white" />}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <Button
                      onClick={handleSaveAiTasks}
                      disabled={isSavingAi || selectedAiTasks.size === 0}
                      className="w-full bg-gray-900 text-white gap-2"
                    >
                      {isSavingAi ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Saving...
                        </>
                      ) : (
                        `Add ${selectedAiTasks.size} Tasks to Project`
                      )}
                    </Button>
                  </div>
                )}
              </DialogContent>
            </Dialog>

            {/* Add Task Dialog */}
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gray-900 text-white hover:bg-gray-800 text-sm h-9 gap-2">
                  <Plus className="w-4 h-4" /> Add Task
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[460px] bg-white">
                <DialogHeader>
                  <DialogTitle>Create Task</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreateTask} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Task Title *</Label>
                    <Input
                      value={taskTitle}
                      onChange={(e) => setTaskTitle(e.target.value)}
                      required
                      placeholder="e.g. Implement user authentication"
                      className="sleek-input"
                      autoFocus
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <textarea
                      value={taskDesc}
                      onChange={(e) => setTaskDesc(e.target.value)}
                      className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-gray-900 min-h-[80px] resize-none"
                      placeholder="Describe what needs to be done..."
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <select
                        value={taskPriority}
                        onChange={(e) => setTaskPriority(e.target.value)}
                        className="w-full h-10 rounded-md border border-gray-200 px-3 text-sm bg-white focus:ring-2 focus:ring-gray-900 outline-none"
                      >
                        {PRIORITIES.map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <select
                        value={taskStatus}
                        onChange={(e) => setTaskStatus(e.target.value)}
                        className="w-full h-10 rounded-md border border-gray-200 px-3 text-sm bg-white focus:ring-2 focus:ring-gray-900 outline-none"
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Estimated Hours</Label>
                    <Input
                      type="number"
                      min="0.5"
                      step="0.5"
                      value={taskEstimate}
                      onChange={(e) => setTaskEstimate(e.target.value)}
                      placeholder="e.g. 4"
                      className="sleek-input"
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isCreating}
                    className="w-full bg-gray-900 text-white"
                  >
                    {isCreating && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    {isCreating ? 'Creating...' : 'Create Task'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Project info header */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gray-900 flex items-center justify-center flex-shrink-0">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">{project?.name}</h1>
              {project?.description ? (
                <ShowMoreText text={project.description} lines={2} className="mt-1" />
              ) : (
                <p className="text-sm text-gray-500 mt-1">No description provided</p>
              )}
            </div>
          </div>

          {/* Progress bar */}
          {totalTasks > 0 && (
            <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-6">
              <div className="flex-1">
                <div className="flex justify-between mb-1.5">
                  <span className="text-xs font-medium text-gray-600">Progress</span>
                  <span className="text-xs font-bold text-gray-900">{progress}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gray-900 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
              <div className="flex gap-6 text-center flex-shrink-0">
                {STATUSES.map((s) => (
                  <div key={s}>
                    <p className="text-lg font-bold text-gray-900">{grouped[s].length}</p>
                    <p className="text-[10px] uppercase font-semibold text-gray-400">
                      {s.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-0 border-b border-gray-200 -mx-6 px-6">
          <button className={TAB_CLASSES('board')} onClick={() => setActiveTab('board')}>
            Tasks
          </button>
          <button className={TAB_CLASSES('github')} onClick={() => setActiveTab('github')}>
            <span className="flex items-center gap-1.5">
              <GitBranch className="w-3.5 h-3.5" /> GitHub
            </span>
          </button>
        </div>

        {/* GitHub panel */}
        {activeTab === 'github' && id && (
          <GitHubPanel projectId={id} />
        )}

        {/* Task board */}
        {activeTab === 'board' && (tasks.length === 0 ? (
          <div className="py-20 text-center border border-dashed border-gray-200 rounded-xl">
            <CheckSquare className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-gray-900 mb-1">No tasks yet</h3>
            <p className="text-sm text-gray-500 mb-4">
              Add tasks manually or let AI generate them for you.
            </p>
            <div className="flex items-center gap-3 justify-center">
              <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-1.5">
                <Plus className="w-4 h-4" /> Add Task
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setAiOpen(true)}
                className="gap-1.5 border-purple-200 text-purple-700 hover:bg-purple-50"
              >
                <Sparkles className="w-4 h-4" /> AI Generate
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
            {STATUSES.map((s) => {
              const sc = statusConfig[s];
              const columnTasks = grouped[s];
              return (
                <div key={s} className="space-y-2 min-w-[280px] max-w-[350px] flex-1 shrink-0">
                  {/* Column header */}
                  <div
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${sc.color}`}
                  >
                    <sc.IconComp className="w-3 h-3" />
                    {s.replace(/_/g, ' ')}
                    <span className="ml-1 opacity-60">{columnTasks.length}</span>
                  </div>

                  {/* Task cards */}
                  <div className="space-y-2">
                    {columnTasks.map((task: any) => {
                      const pc = priorityConfig[task.priority] || priorityConfig.MEDIUM;
                      return (
                        <Card key={task.id} className="sleek-card group">
                          <CardContent className="p-3">
                            <div className="flex items-start justify-between gap-2">
                              <p className="text-sm font-semibold text-gray-900 leading-snug flex-1 flex items-center gap-1.5">
                                {task.github_issue_number && (
                                  <span className="text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-sm shrink-0">
                                    #{task.github_issue_number}
                                  </span>
                                )}
                                {task.title}
                              </p>
                              <button
                                onClick={() => handleDeleteTask(task.id)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-500 flex-shrink-0"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>

                            {task.description && (
                              <ShowMoreText text={task.description} lines={2} className="mt-1" />
                            )}

                            <div className="flex flex-wrap items-center gap-1 mt-2">
                              <span
                                className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border flex items-center gap-0.5 ${pc.color}`}
                              >
                                <pc.IconComp className="w-3 h-3" />
                                {task.priority}
                              </span>
                              {task.estimated_time && (
                                <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                                  <Clock className="w-2.5 h-2.5" />
                                  {task.estimated_time}h
                                </span>
                              )}
                            </div>

                            {/* Status quick-change */}
                            <select
                              value={task.status}
                              onChange={(e) => handleUpdateStatus(task.id, e.target.value)}
                              className="mt-2 w-full text-[11px] font-medium bg-gray-50 border border-gray-100 rounded px-1.5 py-0.5 text-gray-600 cursor-pointer focus:outline-none"
                            >
                              {STATUSES.map((st) => (
                                <option key={st} value={st}>{st.replace(/_/g, ' ')}</option>
                              ))}
                            </select>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </main>
    </div>
  );
}
