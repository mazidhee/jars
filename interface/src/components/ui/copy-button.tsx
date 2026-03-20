"use client";

import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
    text: string;
    className?: string;
}

export function CopyButton({ text, className }: CopyButtonProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async (e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent parent clicks
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    return (
        <Button
            variant="ghost"
            size="icon"
            className={cn(
                "h-8 w-8 transition-all duration-200",
                copied
                    ? "text-emerald-500 hover:text-emerald-500 bg-emerald-500/10"
                    : "text-white/40 hover:text-white hover:bg-white/10",
                className
            )}
            onClick={handleCopy}
        >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
        </Button>
    );
}
