"use client";

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export type TerminalStep = {
    type: "command" | "output";
    content: string;
    delay?: number;
    style?: string;
};

export const FeatureTerminal = ({ title, steps }: { title: string; steps: TerminalStep[] }) => {
    const [displayedContent, setDisplayedContent] = useState<(TerminalStep & { id?: number })[]>([]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [isTyping, setIsTyping] = useState(false);
    const terminalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        let isMounted = true;

        const processStep = async () => {
            if (currentStepIndex >= steps.length) {
                // Loop
                setTimeout(() => {
                    if (isMounted) {
                        setDisplayedContent([]);
                        setCurrentStepIndex(0);
                    }
                }, 5000);
                return;
            }

            const currentStep = steps[currentStepIndex];

            if (currentStep.type === "command") {
                setIsTyping(true);
                const chars = currentStep.content.split("");
                let currentText = "";
                const lineId = Date.now();

                // Start new command line
                setDisplayedContent(prev => [...prev, { ...currentStep, content: "", id: lineId }]);

                for (let i = 0; i < chars.length; i++) {
                    if (!isMounted) return;
                    await new Promise(r => setTimeout(r, 30)); // Fast typing
                    currentText += chars[i];

                    setDisplayedContent((prev) =>
                        prev.map(item => item.id === lineId ? { ...item, content: currentText } : item)
                    );
                }

                if (isMounted) {
                    setIsTyping(false);
                    setTimeout(() => setCurrentStepIndex(p => p + 1), currentStep.delay || 400);
                }
            } else {
                // Output
                setDisplayedContent(prev => {
                    const last = prev[prev.length - 1];
                    // Prevent strict mode double-mount duplication
                    if (last && last.content === currentStep.content && last.type === currentStep.type) {
                        return prev;
                    }
                    return [...prev, currentStep];
                });

                if (isMounted) {
                    setTimeout(() => setCurrentStepIndex(p => p + 1), currentStep.delay || 200);
                }
            }
        };

        processStep();

        return () => { isMounted = false; };
    }, [currentStepIndex, steps]);

    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [displayedContent]);

    return (
        <div className="relative w-full h-full bg-[#0a0a0a] rounded-xl overflow-hidden border border-white/10 shadow-2xl font-mono text-sm leading-relaxed">
            {/* Minimal Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#111] border-b border-white/5">
                <div className="flex space-x-1.5">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
                    <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                    <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
                </div>
                <div className="text-white/40 text-xs tracking-wide font-medium">{title}</div>
                <div className="w-10" /> {/* Spacer */}
            </div>

            {/* Terminal Body */}
            <div ref={terminalRef} className="p-6 h-[calc(100%-40px)] overflow-y-auto scrollbar-hide space-y-2">
                {displayedContent.map((step, index) => (
                    <div key={index} className={cn("break-words", step.style)}>
                        {step.type === "command" ? (
                            <div className="flex items-start gap-3 mt-4 mb-2 group">
                                <span className="text-emerald-500 font-bold select-none shrink-0">➜</span>
                                <span className="text-white font-bold">
                                    {step.content}
                                    {isTyping && index === displayedContent.length - 1 && (
                                        <span className="inline-block w-2.5 h-5 bg-emerald-500 ml-1 animate-pulse align-middle" />
                                    )}
                                </span>
                            </div>
                        ) : (
                            <div className="text-gray-300 pl-6 whitespace-pre-wrap font-medium">
                                {step.content}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
