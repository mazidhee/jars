"use client";

import React, { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface InputOTPProps {
    maxLength?: number;
    value?: string;
    onChange?: (value: string) => void;
    className?: string;
}

export function InputOTP({ maxLength = 6, value = "", onChange, className }: InputOTPProps) {
    const [otp, setOtp] = useState<string[]>(new Array(maxLength).fill(""));
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    useEffect(() => {
        if (value) {
            const split = value.split("").slice(0, maxLength);
            const newOtp = [...split, ...new Array(maxLength - split.length).fill("")];
            setOtp(newOtp);
        }
    }, [value, maxLength]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
        const val = e.target.value;
        const newOtp = [...otp];

        // Handle pasted content
        if (val.length > 1) {
            const pasted = val.slice(0, maxLength).split("");
            for (let i = 0; i < maxLength; i++) {
                if (pasted[i]) newOtp[i] = pasted[i];
            }
            setOtp(newOtp);
            onChange?.(newOtp.join(""));
            // Focus last filled
            const lastFilled = Math.min(pasted.length, maxLength - 1);
            inputRefs.current[lastFilled]?.focus();
            return;
        }

        newOtp[index] = val;
        setOtp(newOtp);
        onChange?.(newOtp.join(""));

        // Auto-advance
        if (val && index < maxLength - 1) {
            inputRefs.current[index + 1]?.focus();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
        if (e.key === "Backspace" && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    return (
        <div className={cn("flex gap-2 items-center justify-center", className)}>
            {otp.map((digit, index) => (
                <div key={index} className="relative group">
                    {/* Visual Box */}
                    <input
                        ref={(el) => { inputRefs.current[index] = el }}
                        type="text"
                        maxLength={6} // Allow paste but handle in onChange
                        value={digit}
                        onChange={(e) => handleChange(e, index)}
                        onKeyDown={(e) => handleKeyDown(e, index)}
                        className={cn(
                            "w-10 h-12 md:w-12 md:h-14 text-center text-xl md:text-2xl font-bold rounded-md bg-[#1a1a1a] border border-white/10 text-white focus:outline-none focus:border-emerald-500 transition-colors caret-emerald-500",
                        )}
                    />
                    {index === 2 && maxLength === 6 && (
                        <div className="absolute -right-2 top-1/2 -translate-y-1/2 w-2 h-0.5 bg-white/10" />
                    )}
                </div>
            ))}
        </div>
    );
}

export const InputOTPGroup = ({ children, className }: { children: React.ReactNode, className?: string }) => {
    return <div className={cn("flex items-center gap-2", className)}>{children}</div>
}

export const InputOTPSlot = ({ index, ...props }: any) => {
    // Adapter for Shadcn slot pattern if needed, but our custom component is self-contained
    return null;
}
