"use client";

import React, { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";

// Types for our terminal steps
type TerminalStep = {
    type: "command" | "output" | "splash" | "input_prompt";
    content?: string;
    delay?: number; // Time to wait before showing this step
    typingSpeed?: number; // For commands
    style?: string; // Color/style class
};

const SPLASH_ART = `
      ██╗ █████╗ ██████╗ ███████╗
      ██║██╔══██╗██╔══██╗██╔════╝
      ██║███████║██████╔╝███████╗
 ██   ██║██╔══██║██╔══██╗╚════██║
 ╚█████╔╝██║  ██║██║  ██║███████║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
`;

const INITIAL_STEPS: TerminalStep[] = [
    // 1. Splash Screen
    { type: "splash", content: SPLASH_ART, delay: 200 },
    { type: "output", content: "JARS Sentinel v3.0.1", style: "text-emerald-500 font-bold mb-4", delay: 200 },
    { type: "output", content: "Initializing secure execution environment...", style: "text-white/40 mb-6", delay: 300 },

    // 2. Login Flow
    { type: "input_prompt", content: "Authentication Required", delay: 500 },
    { type: "command", content: "auth login", delay: 800 },
    { type: "output", content: "• Signing in as demo@jars.fi...", style: "text-white/60", delay: 400 },
    { type: "output", content: "✓ Session Authenticated [2FA Verified]", style: "text-emerald-400 font-bold", delay: 600 },

    // 3. Action
    { type: "command", content: "subs follow --alias 'Quantum_X' --alloc 5000", delay: 1000 },

    // 4. Thread
    { type: "output", content: "[SYS] Initializing copy protocol for 'Quantum_X'...", style: "text-blue-400", delay: 200 },
    { type: "output", content: "[NET] Establishing persistent WebSocket -> wss://api.jars.fi/v2/stream", style: "text-white/50", delay: 100 },
    { type: "output", content: "[NET] Connection established. Latency: 14ms", style: "text-white/50", delay: 150 },
    { type: "output", content: "[RISK] Verifying margin requirements for $5,000.00 allocation...", style: "text-white/50", delay: 200 },
    { type: "output", content: "[RISK] Check passed. Leverage cap: 5x.", style: "text-emerald-500/80", delay: 100 },

    { type: "output", content: "[SYNC] Fetching master open positions...", style: "text-white/50", delay: 400 },
    { type: "output", content: "Detected 2 active positions:", style: "text-white underline mt-2", delay: 100 },
    {
        type: "output",
        content: "  • LONG BTC/USDT @ 64,210.50 (Size: 0.42 BTC)",
        style: "text-emerald-400 ml-4",
        delay: 200
    },
    {
        type: "output",
        content: "  • SHORT ETH/USDT @ 3,450.20 (Size: 5.10 ETH)",
        style: "text-red-400 ml-4 mb-2",
        delay: 200
    },

    { type: "output", content: "[EXEC] Calculating entry parity...", style: "text-white/50", delay: 300 },

    { type: "output", content: "[ORDER] SUBMIT MARKET BUY BTC/USDT...", style: "text-white", delay: 100 },
    { type: "output", content: ">>> FILL: 0.02 BTC @ 64,212.00 (Diff: +1.50)", style: "text-emerald-500 font-bold", delay: 200 },

    { type: "output", content: "[INFO] Synchronization Complete.", style: "text-blue-400 mt-2", delay: 500 },
    { type: "output", content: "Sentinel Active. Listening for real-time signals...", style: "text-emerald-400 animate-pulse", delay: 1000 },

    // 5. Live "Heartbeat" logs
    { type: "output", content: "[Ping] 14ms...", style: "text-white/20 text-xs", delay: 2000 },
    { type: "output", content: "[Ping] 15ms...", style: "text-white/20 text-xs", delay: 2000 },
    { type: "output", content: "[Ping] 13ms...", style: "text-white/20 text-xs", delay: 2000 },
];

export function TerminalDemo() {
    const [displayedContent, setDisplayedContent] = useState<(TerminalStep & { id?: number })[]>([]);
    const [stepIndex, setStepIndex] = useState(0);
    const [isTyping, setIsTyping] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        let isMounted = true;

        const processStep = async () => {
            if (stepIndex >= INITIAL_STEPS.length) return;

            const step = INITIAL_STEPS[stepIndex];

            // Initial delay
            if (isMounted) {
                await new Promise(r => setTimeout(r, step.delay || 0));
            }
            if (!isMounted) return;

            if (step.type === "command") {
                setIsTyping(true);
                const chars = step.content?.split("") || [];
                let currentText = "";
                const lineId = Date.now();

                // Start new command line
                setDisplayedContent(prev => [...prev, { ...step, content: "", id: lineId }]);

                for (let i = 0; i < chars.length; i++) {
                    if (!isMounted) return;
                    await new Promise(r => setTimeout(r, step.typingSpeed || 40));
                    currentText += chars[i];

                    setDisplayedContent(prev =>
                        prev.map(item => item.id === lineId ? { ...item, content: currentText } : item)
                    );
                }

                if (isMounted) {
                    setIsTyping(false);
                    setStepIndex(prev => prev + 1);
                }
            }
            else {
                setDisplayedContent(prev => {
                    const last = prev[prev.length - 1];
                    if (last && last.content === step.content && last.type === step.type) {
                        return prev;
                    }
                    return [...prev, step];
                });
                if (isMounted) setStepIndex(prev => prev + 1);
            }
        };

        processStep();

        return () => { isMounted = false; };
    }, [stepIndex]);

    // Auto-scroll
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [displayedContent]);

    return (
        <div className="w-full max-w-5xl mx-auto rounded-xl border border-white/10 bg-[#0a0a0a] shadow-2xl overflow-hidden font-mono text-sm md:text-base leading-relaxed">
            {/* Minimal Header - Claude Style */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#111] border-b border-white/5">
                <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                    <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                    <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                </div>
                <div className="text-white/40 text-xs tracking-wide font-medium">jars-cli — sentinel</div>
                <div className="w-10" />
            </div>

            {/* Terminal Viewport */}
            <div
                ref={containerRef}
                className="h-[500px] md:h-[600px] overflow-y-auto p-6 space-y-2 scrollbar-hide"
            >
                {displayedContent.map((line, i) => (
                    <div key={i} className={cn("break-words", line.style)}>
                        {line.type === "splash" && (
                            <pre className="text-emerald-500 font-bold leading-none text-[8px] md:text-sm whitespace-pre-wrap select-none text-center mb-6">
                                {line.content}
                            </pre>
                        )}

                        {line.type === "command" && (
                            <div className="flex items-start gap-3 mt-4 mb-2">
                                <span className="text-emerald-500 font-bold select-none shrink-0">➜</span>
                                <span className="text-white font-bold">
                                    {line.content}
                                    {isTyping && i === displayedContent.length - 1 && (
                                        <span className="inline-block w-2.5 h-5 bg-emerald-500 ml-1 animate-pulse align-middle" />
                                    )}
                                </span>
                            </div>
                        )}

                        {line.type === "output" && (
                            <div className={cn("text-gray-300 pl-6 font-medium whitespace-pre-wrap", line.style)}>{line.content}</div>
                        )}

                        {line.type === "input_prompt" && (
                            <div className="mt-8 mb-4 text-white font-bold pl-6 border-l-2 border-emerald-500 pl-4">{line.content}</div>
                        )}
                    </div>
                ))}

                {/* Idle Cursor */}
                {!isTyping && stepIndex >= INITIAL_STEPS.length && (
                    <div className="flex items-start gap-3 mt-4 pl-6">
                        <span className="text-emerald-500 font-bold select-none shrink-0">➜</span>
                        <span className="inline-block w-2.5 h-5 bg-emerald-500 animate-pulse" />
                    </div>
                )}

                <div ref={containerRef} />
            </div>
        </div>
    );
}
