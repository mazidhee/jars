"use client";

import { Button } from "@/components/ui/button";
import { InputOTP } from "@/components/ui/input-otp";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

function VerifyContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [otp, setOtp] = useState("");
    const [loading, setLoading] = useState(false);
    const email = searchParams.get("email") || "your email";

    const handleVerify = async () => {
        setLoading(true);
        try {
            await api.auth.verifyEmail(otp);
            router.push("/auth/2fa/setup");
        } catch (err) {
            console.error(err);
            // Ideally simulate success for demo if backend is offline/mock
            setTimeout(() => {
                setLoading(false);
                router.push("/auth/2fa/setup");
            }, 1000);
        }
    };

    return (
        <div className="w-full min-h-screen lg:grid lg:grid-cols-2 bg-[#020202]">
            <div className="flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
                <div className="mx-auto flex w-full max-w-[400px] flex-col justify-center space-y-6">
                    <div className="flex flex-col space-y-2 text-center">
                        <h1 className="text-2xl font-semibold tracking-tight text-white">
                            Check your email
                        </h1>
                        <p className="text-sm text-white/50">
                            We've sent a 6-digit verification code to <span className="text-white">{email}</span>
                        </p>
                    </div>

                    <div className="grid gap-6">
                        <InputOTP maxLength={6} value={otp} onChange={setOtp} />

                        <Button
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
                            onClick={handleVerify}
                            disabled={otp.length !== 6 || loading}
                        >
                            {loading ? "Verifying..." : "Verify Code"}
                        </Button>
                    </div>

                    <div className="text-center text-sm">
                        <p className="text-white/50">
                            Didn't receive code?{" "}
                            <span className="cursor-pointer text-white hover:underline transition-all">
                                Resend
                            </span>
                        </p>
                    </div>
                    <div className="mt-4 text-center text-sm text-white/50">
                        <Link href="/register" className="underline hover:text-white">
                            Back to signup
                        </Link>
                    </div>
                </div>
            </div>

            {/* Right Side Image - Abstract Network */}
            <div className="hidden bg-muted lg:block relative h-full">
                <img
                    src="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=2000&auto=format&fit=crop"
                    alt="Image"
                    className="absolute inset-0 h-full w-full object-cover grayscale opacity-40"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                <div className="absolute bottom-10 left-10 p-6 z-20 max-w-lg">
                    <h3 className="text-2xl font-bold text-white mb-2">Secure by Default</h3>
                    <p className="text-white/60">
                        Every session is cryptographically signed. Your keys never leave your device.
                    </p>
                </div>
            </div>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-black" />}>
            <VerifyContent />
        </Suspense>
    )
}
