"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { toast } from "sonner";

export function SignupForm() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    async function onSubmit(event: React.SyntheticEvent) {
        event.preventDefault();
        setIsLoading(true);

        const target = event.target as typeof event.target & {
            email: { value: string };
            password: { value: string };
            "first-name": { value: string };
            "last-name": { value: string };
            country: { value: string };
        };

        const data = {
            email: target.email.value,
            password: target.password.value,
            first_name: target["first-name"].value,
            last_name: target["last-name"].value,
            country: target.country.value,
        };

        try {
            await api.auth.register(data);
            router.push(`/register?loading=true&email=${encodeURIComponent(data.email)}`);
        } catch (err: any) {
            console.error(err);
            // Ideally use a toast component here, defaulting to alert for now if toast not set up
            alert(err.message || "Failed to register");
            setIsLoading(false);
        }
    }

    return (
        <div className="w-full lg:grid lg:min-h-[600px] lg:grid-cols-2 xl:min-h-[800px]">
            <div className="flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
                <div className="mx-auto grid w-full max-w-[400px] gap-6">
                    <div className="grid gap-2 text-center">
                        <h1 className="text-3xl font-bold tracking-tight text-white">Create an account</h1>
                        <p className="text-balance text-white/50">
                            Enter your details below to create your JARS account
                        </p>
                    </div>
                    <form onSubmit={onSubmit} className="grid gap-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="first-name" className="text-white">First name</Label>
                                <Input id="first-name" placeholder="Max" required className="bg-[#1a1a1a] border-white/10 text-white placeholder:text-white/20 focus:border-emerald-500/50" />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="last-name" className="text-white">Last name</Label>
                                <Input id="last-name" placeholder="Robinson" required className="bg-[#1a1a1a] border-white/10 text-white placeholder:text-white/20 focus:border-emerald-500/50" />
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="email" className="text-white">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@example.com"
                                required
                                className="bg-[#1a1a1a] border-white/10 text-white placeholder:text-white/20 focus:border-emerald-500/50"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="country" className="text-white">Country</Label>
                            <Input
                                id="country"
                                placeholder="Nigeria"
                                required
                                className="bg-[#1a1a1a] border-white/10 text-white placeholder:text-white/20 focus:border-emerald-500/50"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="password" className="text-white">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                required
                                className="bg-[#1a1a1a] border-white/10 text-white placeholder:text-white/20 focus:border-emerald-500/50"
                            />
                        </div>
                        <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold" disabled={isLoading}>
                            {isLoading ? "Creating account..." : "Create account"}
                        </Button>
                        <Button variant="outline" className="w-full border-white/10 hover:bg-white/5 hover:text-white bg-transparent text-white/70">
                            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                                <path
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    fill="#4285F4"
                                />
                                <path
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    fill="#34A853"
                                />
                                <path
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    fill="#FBBC05"
                                />
                                <path
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    fill="#EA4335"
                                />
                            </svg>
                            Sign up with Google
                        </Button>
                    </form>
                </div>
            </div>

            {/* Right Side Image / Testimonial */}
            <div className="hidden bg-muted lg:block relative h-full">
                <img
                    src="https://images.unsplash.com/photo-1642104704074-907c0698cbd9?q=80&w=2832&auto=format&fit=crop"
                    alt="Image"
                    className="absolute inset-0 h-full w-full object-cover grayscale opacity-30"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                <div className="absolute bottom-10 left-10 p-6 z-20 max-w-lg">
                    <blockquote className="space-y-2">
                        <p className="text-lg text-white font-medium">
                            &ldquo;The speed of execution is terrifying. In a good way. It feels like I upgraded my entire trading infrastructure overnight.&rdquo;
                        </p>
                        <footer className="text-sm text-white/50">Soona Amadi, Quant @ Lagos Hedge</footer>
                    </blockquote>
                </div>
            </div>
        </div>
    );
}
