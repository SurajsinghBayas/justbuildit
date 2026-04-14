import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md shadow-lg border-0 bg-white">
        <CardHeader className="space-y-2 text-center pb-8 border-b-8 border-primary rounded-t-xl">
          <CardTitle className="text-3xl font-extrabold tracking-tight">Welcome back</CardTitle>
          <CardDescription className="text-gray-500 font-medium">Log in to your account</CardDescription>
        </CardHeader>
        <CardContent className="pt-8 space-y-6">
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="font-bold">Email address</Label>
              <Input id="email" type="email" placeholder="name@company.com" required className="bg-gray-50 border-gray-200" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="font-bold">Password</Label>
              <Input id="password" type="password" required className="bg-gray-50 border-gray-200" />
            </div>
            <Button type="submit" className="w-full bg-gray-900 text-white shadow-none mt-2 text-lg py-6 rounded-xl hover:bg-gray-800">
              Log in
            </Button>
          </form>
          <div className="text-center text-sm font-medium text-gray-500 pt-4">
            Don't have an account? <Link to="/register" className="text-primary-foreground underline underline-offset-4 hover:text-black">Sign up</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
