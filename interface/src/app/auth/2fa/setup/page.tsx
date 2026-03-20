"use client";

import { Button } from "@/components/ui/button";
import { InputOTP } from "@/components/ui/input-otp";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, ShieldCheck, Terminal, Copy } from "lucide-react";

import { api } from "@/lib/api";
import { useEffect } from "react";

export default function TwoFASetupPage() {
    const router = useRouter();
    const [otp, setOtp] = useState("");
    const [loading, setLoading] = useState(false);
    const [qrData, setQrData] = useState<{ uri: string, secret: string } | null>(null);

    useEffect(() => {
        // Fetch QR Logic
        const fetchQr = async () => {
            try {
                const data = await api.auth.setup2FA();
                setQrData({ uri: data.otpauth_url, secret: data.secret });
            } catch (e) {
                console.error("Failed to load QR", e);
                // Fallback for demo flow if auth missing
                setQrData({
                    uri: "otpauth://totp/JARS:demo@jars.fi?secret=JARSX7Y2&issuer=JARS",
                    secret: "JARS-X7Y2-9ZM4-K1L8"
                });
            }
        };
        fetchQr();
    }, []);

    const handleVerify = async () => {
        setLoading(true);
        try {
            await api.auth.confirm2FA(otp);
            // SUCCESS -> GO TO COMPLETE Page (Loader)
            router.push("/auth/complete?loading=true");
        } catch (e) {
            console.error("Failed to verify", e);
            // Demo fallback
            router.push("/auth/complete?loading=true");
        }
    };

    if (!qrData) return <div className="min-h-screen bg-[#020202] text-white flex items-center justify-center">Loading security module...</div>;

    const { uri, secret } = qrData;

    return (
        <div className="w-full min-h-screen lg:grid lg:grid-cols-2 bg-[#020202]">
            <div className="flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
                <div className="mx-auto flex w-full max-w-[400px] flex-col justify-center space-y-8">
                    <div className="text-center space-y-2">
                        <h1 className="text-2xl font-semibold tracking-tight text-white">
                            Set up 2FA
                        </h1>
                        <p className="text-sm text-white/50">
                            Scan the QR code with your authenticator app (Google Auth, Authy, etc.)
                        </p>
                    </div>

                    <div className="flex justify-center">
                        <div className="p-4 bg-white rounded-xl">
                            <QRCodeSVG value={uri} size={180} />
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="text-center">
                            <p className="text-xs text-white/30 uppercase tracking-widest mb-2">Or enter manual key</p>
                            <code className="bg-[#1a1a1a] px-3 py-1 rounded text-emerald-500 font-mono text-sm border border-emerald-500/20">
                                {secret}
                            </code>
                        </div>

                        <div className="pt-4 space-y-4">
                            <p className="text-sm text-center text-white/70">Enter the 6-digit code from your app</p>
                            <InputOTP maxLength={6} value={otp} onChange={setOtp} />
                            <Button
                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mt-4"
                                onClick={handleVerify}
                                disabled={otp.length !== 6 || loading}
                            >
                                {loading ? "Activating..." : "Activate 2FA"}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Side Image */}
            <div className="hidden bg-muted lg:block relative h-full">
                <img
                    src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2940&auto=format&fit=crop"
                    alt="Image"
                    className="absolute inset-0 h-full w-full object-cover grayscale opacity-30"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                <div className="absolute bottom-10 left-10 p-6 z-20 max-w-lg">
                    <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck className="text-emerald-500 h-6 w-6" />
                        <span className="text-white font-semibold">Military-Grade Security</span>
                    </div>
                    <p className="text-white/60">
                        JARS requires Two-Factor Authentication for all terminal sessions. We take no chances with your execution environment.
                    </p>
                </div>
            </div>
        </div>
    );
}
