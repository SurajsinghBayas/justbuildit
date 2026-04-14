import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';

export default function Organizations() {
  const dummyOrgs = [
    { id: 1, name: "Acme Corp", members: 45 },
    { id: 2, name: "Stark Industries", members: 2 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 p-4 sticky top-0 z-10 shadow-sm flex items-center justify-between">
         <Link to="/dashboard" className="font-bold text-xl tracking-tighter hover:opacity-80">justbuildit.</Link>
         <nav className="flex gap-4">
            <Link to="/dashboard"><Button variant="ghost">Dashboard</Button></Link>
         </nav>
      </header>

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8 flex-1">
        <div className="flex justify-between items-end border-b border-gray-200 pb-4">
           <div>
             <h1 className="text-4xl font-extrabold tracking-tight">Organizations</h1>
             <p className="text-gray-500 mt-2">Workspaces and team directories.</p>
           </div>
           <Button className="bg-gray-900 text-white shadow-none hover:bg-gray-800 font-bold rounded-xl px-6">
             New Organization
           </Button>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {dummyOrgs.map((org) => (
             <Card key={org.id} className="border-t-4 border-t-accent border-x-0 border-b-0 shadow-sm bg-white rounded-lg">
                <CardHeader>
                   <CardTitle className="text-2xl">{org.name}</CardTitle>
                   <CardDescription>Members: {org.members}</CardDescription>
                </CardHeader>
                <CardContent className="pt-2">
                   <Button variant="outline" className="w-full font-bold">Manage</Button>
                </CardContent>
             </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
