
"use client";

import { SignupForm } from "@/components/blocks/signup-form";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, Suspense } from "react";

function RegisterContent() {
    return (
        <div className="min-h-screen bg-[#020202] text-white">
            <div className="flex min-h-screen flex-col items-center justify-center p-0">
                <SignupForm />
            </div>
        </div>
    );
}

export default function RegisterPage() {
    return (
        <RegisterContent />
    )
}
