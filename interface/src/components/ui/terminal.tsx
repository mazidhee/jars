"use client";

import { cn } from "@/lib/utils";
import { motion, MotionProps } from "framer-motion";
import { useEffect, useRef, useState } from "react";

interface TerminalProps {
    children: React.ReactNode;
    className?: string;
}

export const Terminal = ({ children, className }: TerminalProps) => {
    return (
        <div
            className={cn(
                "z-0 h-full w-full rounded-xl border border-white/10 bg-[#0a0a0a]",
                className,
            )}
        >
            <div className="flex flex-col gap-y-2 border-b border-white/5 bg-white/5 p-4">
                <div className="flex flex-row gap-x-2">
                    <div className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                    <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                </div>
            </div>
            <pre className="p-4 overflow-y-auto whitespace-pre-wrap font-mono text-sm leading-relaxed text-white/70 scrollbar-hide">
                {children}
            </pre>
        </div>
    );
};

interface AnimatedSpanProps extends MotionProps {
    children: React.ReactNode;
    delay?: number;
    className?: string;
}

export const AnimatedSpan = ({
    children,
    delay = 0,
    className,
    ...props
}: AnimatedSpanProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: delay / 1000, ease: "easeOut" }}
            className={cn("grid gap-y-1", className)}
            {...props}
        >
            {children}
        </motion.div>
    );
};

interface TypingAnimationProps extends MotionProps {
    children: string;
    className?: string;
    duration?: number;
    delay?: number;
    as?: React.ElementType;
}

export const TypingAnimation = ({
    children,
    className,
    duration = 60,
    delay = 0,
    as: Component = "span",
    ...props
}: TypingAnimationProps) => {
    const [displayedText, setDisplayedText] = useState<string>("");
    const [started, setStarted] = useState(false);
    const elementRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        const startTimeout = setTimeout(() => {
            setStarted(true);
        }, delay);
        return () => clearTimeout(startTimeout);
    }, [delay]);

    useEffect(() => {
        if (!started) return;

        let i = 0;
        const typingEffect = setInterval(() => {
            if (i < children.length) {
                setDisplayedText(children.substring(0, i + 1));
                i++;
            } else {
                clearInterval(typingEffect);
            }
        }, duration);

        return () => {
            clearInterval(typingEffect);
        };
    }, [children, duration, started]);

    return (
        <Component
            ref={elementRef}
            className={cn("text-emerald-400 font-bold", className)}
            {...props}
        >
            {displayedText}
        </Component>
    );
};
