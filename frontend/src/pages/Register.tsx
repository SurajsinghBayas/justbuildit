import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Register() {
  const navigate = useNavigate();

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md shadow-lg border-0 bg-white">
        <CardHeader className="space-y-2 text-center pb-8 border-b-8 border-secondary rounded-t-xl">
          <CardTitle className="text-3xl font-extrabold tracking-tight">Create an account</CardTitle>
          <CardDescription className="text-gray-500 font-medium">Join justbuildit. today</CardDescription>
        </CardHeader>
        <CardContent className="pt-8 space-y-6">
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="font-bold">Full Name</Label>
              <Input id="name" type="text" placeholder="John Doe" required className="bg-gray-50 border-gray-200" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="font-bold">Email address</Label>
              <Input id="email" type="email" placeholder="name@company.com" required className="bg-gray-50 border-gray-200" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="font-bold">Password</Label>
              <Input id="password" type="password" required className="bg-gray-50 border-gray-200" />
            </div>
            <Button type="submit" className="w-full bg-gray-900 text-white shadow-none mt-2 text-lg py-6 rounded-xl hover:bg-gray-800">
              Sign up
            </Button>
          </form>
          <div className="text-center text-sm font-medium text-gray-500 pt-4">
            Already have an account? <Link to="/login" className="text-primary-foreground underline underline-offset-4 hover:text-black">Log in</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
