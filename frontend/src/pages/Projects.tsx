import { useEffect, useState } from 'react';
import apiClient from '@/api/client';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';
import { Briefcase, Plus, Loader2, ArrowLeft } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [open, setOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  async function fetchProjects() {
    setLoading(true);
    try {
      const res = await apiClient.get('/projects/');
      setProjects(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await apiClient.post('/projects/', { name: newProjectName, description: newProjectDesc });
      setOpen(false);
      setNewProjectName('');
      setNewProjectDesc('');
      fetchProjects();
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      <header className="bg-white px-6 py-4 flex items-center justify-between border-b border-gray-200">
         <Link to="/dashboard" className="font-bold text-sm flex items-center gap-2 text-gray-600 hover:text-gray-900">
           <ArrowLeft className="w-4 h-4" /> Back to Dashboard
         </Link>
      </header>

      <main className="p-8 max-w-6xl mx-auto w-full space-y-8 flex-1">
        <div className="flex justify-between items-end border-b border-gray-200 pb-4">
           <div>
             <h1 className="text-3xl font-bold tracking-tight text-gray-900">Projects</h1>
             <p className="text-sm text-gray-500 mt-1 font-medium">Manage and view all your active initiatives.</p>
           </div>
           
           <Dialog open={open} onOpenChange={setOpen}>
             <DialogTrigger asChild>
               <Button className="bg-gray-900 text-white hover:bg-gray-800 text-sm h-9">
                 <Plus className="w-4 h-4 mr-2" /> New Project
               </Button>
             </DialogTrigger>
             <DialogContent className="sm:max-w-[425px] bg-white">
               <DialogHeader>
                 <DialogTitle>Create Project</DialogTitle>
               </DialogHeader>
               <form onSubmit={handleCreateProject} className="space-y-4 mt-4">
                 <div className="space-y-2">
                   <Label htmlFor="name">Project Name</Label>
                   <Input id="name" value={newProjectName} onChange={e => setNewProjectName(e.target.value)} required className="sleek-input" placeholder="e.g. Website Redesign" />
                 </div>
                 <div className="space-y-2">
                   <Label htmlFor="desc">Description</Label>
                   <Input id="desc" value={newProjectDesc} onChange={e => setNewProjectDesc(e.target.value)} className="sleek-input" placeholder="Optional brief overview" />
                 </div>
                 <div className="pt-4 flex justify-end">
                   <Button type="submit" disabled={isCreating} className="bg-gray-900 text-white w-full">
                     {isCreating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : 'Create'}
                   </Button>
                 </div>
               </form>
             </DialogContent>
           </Dialog>

        </div>

        {loading ? (
          <div className="flex justify-center p-20">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-4">
            {projects.length > 0 ? projects.map((p: any) => (
              <Card key={p.id} className="sleek-card cursor-pointer"> 
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded border border-gray-200 bg-gray-50 flex items-center justify-center">
                      <Briefcase className="w-4 h-4 text-gray-500" />
                    </div>
                    <h3 className="font-semibold text-gray-900 truncate">{p.name}</h3>
                  </div>
                  <p className="text-sm font-medium text-gray-500 line-clamp-2">
                    {p.description || "No description provided."}
                  </p>
                  <div className="flex items-center gap-2 mt-4 text-xs font-medium text-gray-500">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" /> Active
                  </div>
                </CardContent>
              </Card>
            )) : (
              <div className="col-span-3 py-16 text-center border border-dashed border-gray-200 rounded-lg">
                <Briefcase className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-gray-900 mb-1">No projects yet</h3>
                <p className="text-sm text-gray-500">Click early button above to start your first project.</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
