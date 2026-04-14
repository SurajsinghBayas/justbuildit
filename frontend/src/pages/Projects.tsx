import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';

export default function Projects() {
  const dummyProjects = [
    { id: 1, name: "Website Redesign", status: "In Progress", color: "border-primary" },
    { id: 2, name: "Mobile App Launch", status: "Planning", color: "border-secondary" },
    { id: 3, name: "Marketing Campaign Q3", status: "Completed", color: "border-accent" },
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
             <h1 className="text-4xl font-extrabold tracking-tight">Projects</h1>
             <p className="text-gray-500 mt-2">Manage and view all your active initiatives.</p>
           </div>
           <Button className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold rounded-xl px-6">
             New Project
           </Button>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dummyProjects.map((p) => (
            <Card key={p.id} className={`border-l-8 ${p.color} border-y-0 border-r-0 shadow-sm hover:shadow-md transition-shadow bg-white rounded-xl`}> 
              <CardHeader pb-2>
                <CardTitle>{p.name}</CardTitle>
                <CardDescription className="font-medium text-gray-500 uppercase tracking-wider text-xs mt-1">
                  {p.status}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4 flex justify-end">
                <Button variant="outline" size="sm" className="font-bold text-gray-600 rounded-lg">View Details</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
