"use client";

import { MultiStepLoader } from "@/components/ui/multi-step-loader";
import { CopyButton } from "@/components/ui/copy-button";
import { Button } from "@/components/ui/button";
import { CheckCircle, Terminal } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";

const loadingStates = [
    { text: "Verifying session integrity..." },
    { text: "Provisioning JARS Identity (DID)..." },
    { text: "Linking to global execution fabric..." },
    { text: "Establishing secure Sentinel stream..." },
    { text: "All set." },
];

function CompleteContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const loadingParam = searchParams.get("loading");
    const [loading, setLoading] = useState(false);
    const [finished, setFinished] = useState(false);

    useEffect(() => {
        if (loadingParam === 'true') {
            setLoading(true);
            const timer = setTimeout(() => {
                setLoading(false);
                setFinished(true);
            }, 6000); // 1.2s per step roughly
            return () => clearTimeout(timer);
        } else {
            setFinished(true);
        }
    }, [loadingParam]);

    return (
        <div className="min-h-screen bg-[#020202] text-white flex items-center justify-center relative">
            <MultiStepLoader loadingStates={loadingStates} loading={loading} duration={1200} loop={false} />

            {finished && (
                <div className="w-full max-w-md p-4 animate-in fade-in zoom-in duration-500">
                    <div className="text-center space-y-8">
                        <div className="flex justify-center">
                            <div className="h-24 w-24 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 shadow-[0_0_40px_-10px_rgba(16,185,129,0.3)]">
                                <CheckCircle className="h-12 w-12 text-emerald-500" />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h1 className="text-3xl font-bold text-white">All set!</h1>
                            <p className="text-white/50">Your JARS account is fully provisioned.</p>
                        </div>

                        <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 text-left space-y-4 shadow-2xl">
                            <div className="flex items-center gap-3 text-white/80">
                                <Terminal className="h-5 w-5 text-emerald-500" />
                                <span className="font-medium">Connect via CLI</span>
                            </div>
                            <p className="text-sm text-white/50 leading-relaxed">
                                You can now access your high-frequency terminal. Copy the command below to log in.
                            </p>

                            <div className="flex items-center justify-between gap-4 p-3 rounded-lg bg-black border border-white/10 group cursor-pointer hover:border-emerald-500/50 transition-colors">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <span className="text-emerald-500 font-mono select-none">$</span>
                                    <span className="font-mono text-white text-sm truncate">jars auth login</span>
                                </div>
                                <CopyButton text="jars auth login" />
                            </div>
                        </div>

                        <Button
                            onClick={() => router.push("/")}
                            variant="ghost"
                            className="text-white/40 hover:text-white"
                        >
                            Return to Dashboard
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function CompletePage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-black" />}>
            <CompleteContent />
        </Suspense>
    )
}
