import { useEffect, useState } from 'react';
import apiClient from '@/api/client';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';
import { Building, Plus, Loader2, ArrowLeft, Users } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function Organizations() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [open, setOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  async function fetchOrgs() {
    setLoading(true);
    try {
      const res = await apiClient.get('/organizations/');
      setOrgs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchOrgs();
  }, []);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await apiClient.post('/organizations/', { name: newOrgName });
      setOpen(false);
      setNewOrgName('');
      fetchOrgs();
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

      <main className="p-8 max-w-5xl mx-auto w-full space-y-8 flex-1">
        <div className="flex justify-between items-end border-b border-gray-200 pb-4">
           <div>
             <h1 className="text-3xl font-bold tracking-tight text-gray-900">Organizations</h1>
             <p className="text-sm text-gray-500 mt-1 font-medium">Workspaces and team directories.</p>
           </div>
           
           <Dialog open={open} onOpenChange={setOpen}>
             <DialogTrigger asChild>
               <Button className="bg-gray-900 text-white hover:bg-gray-800 text-sm h-9">
                 <Plus className="w-4 h-4 mr-2" /> New Organization
               </Button>
             </DialogTrigger>
             <DialogContent className="sm:max-w-[350px] bg-white">
               <DialogHeader>
                 <DialogTitle>Create Organization</DialogTitle>
               </DialogHeader>
               <form onSubmit={handleCreateOrg} className="space-y-4 mt-4">
                 <div className="space-y-2">
                   <Label htmlFor="name">Organization Name</Label>
                   <Input id="name" value={newOrgName} onChange={e => setNewOrgName(e.target.value)} required className="sleek-input" placeholder="e.g. Acme Corp" />
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
          <div className="grid md:grid-cols-2 gap-4">
            {orgs.length > 0 ? orgs.map((org: any) => (
              <Card key={org.id} className="sleek-card cursor-pointer">
                <CardContent className="p-5 flex justify-between items-center">
                   <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded border border-gray-200 bg-gray-50 flex items-center justify-center">
                        <Building className="w-5 h-5 text-gray-500" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 text-lg">{org.name}</h3>
                        <p className="text-xs font-medium flex items-center gap-1 mt-1 text-gray-500">
                          <Users className="w-3 h-3" /> Company Workspace
                        </p>
                      </div>
                   </div>
                   <Button variant="outline" size="sm" className="font-semibold border-gray-200 text-gray-700">Manage</Button>
                </CardContent>
              </Card>
            )) : (
              <div className="col-span-2 py-16 text-center border border-dashed border-gray-200 rounded-lg">
                <Building className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-gray-900 mb-1">No organizations found</h3>
                <p className="text-sm text-gray-500">Create a new organization to start collaborating.</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
