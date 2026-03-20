"use client";

import { Tabs } from "./ui/tabs";
import { FeatureTerminal } from "./feature-terminal";

const SPLASH_ART = `
      ██╗ █████╗ ██████╗ ███████╗
      ██║██╔══██╗██╔══██╗██╔════╝
      ██║███████║██████╔╝███████╗
 ██   ██║██╔══██║██╔══██╗╚════██║
 ╚█████╔╝██║  ██║██║  ██║███████║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   v3.0.1`;

export function TabsDemo() {
    const tabs = [
        {
            title: "Infrastructure",
            value: "infrastructure",
            content: (
                <div className="w-full overflow-hidden relative h-full rounded-2xl p-4 md:p-10 font-bold text-white bg-gradient-to-br from-gray-900 to-black border border-white/10 shadow-2xl">
                    <p className="text-xl md:text-3xl font-bold text-white mb-6">Global Sentinel Control</p>
                    <div className="h-[500px] md:h-[600px] shadow-inner bg-black/50 rounded-xl overflow-hidden">
                        <FeatureTerminal
                            title="jars-cli — sentinel"
                            steps={[
                                { type: "output", content: SPLASH_ART, style: "text-emerald-500 font-bold mb-4 leading-tight text-[10px] md:text-xs whitespace-pre" },
                                { type: "command", content: "jars infra up --region lagos --tier institution", delay: 800 },
                                { type: "output", content: ">> INITIALIZING SENTINEL DEPLOYMENT SEQUENCE...", style: "text-blue-400 font-bold", delay: 300 },
                                { type: "output", content: "[1/4] Provisioning isolation container (c7g.2xlarge)...", style: "text-white/60", delay: 400 },
                                { type: "output", content: "[2/4] Optimizing kernel for low-latency packet switching...", style: "text-white/60", delay: 500 },
                                { type: "output", content: "      > sysctl -w net.ipv4.tcp_low_latency=1", style: "text-gray-500 text-xs", delay: 100 },
                                { type: "output", content: "[3/4] Establishing encrypted tunnel to Binance (Tokyo)...", style: "text-white/60", delay: 600 },
                                { type: "output", content: "      > Ping: 12.4ms [EXCELLENT]", style: "text-emerald-400", delay: 200 },
                                { type: "output", content: "[4/4] Syncing Atomic Ledger state...", style: "text-white/60", delay: 400 },
                                { type: "output", content: "✓ SENTINEL NODE ONLINE (ID: lagos-Alpha-9)", style: "text-emerald-500 font-bold text-lg mt-2", delay: 200 },
                                { type: "command", content: "jars status --performance", delay: 1500 },
                                { type: "output", content: "Uptime: 00:00:12 | Memory: 4% | CPU: 1%", style: "text-white/80", delay: 200 },
                                { type: "output", content: "Active Signals: 0 | Executed Today: 0", style: "text-white/80", delay: 200 },
                                { type: "output", content: "Network Jitter: 0.4ms", style: "text-emerald-400", delay: 200 },
                            ]}
                        />
                    </div>
                </div>
            ),
        },
        {
            title: "Copy Trading",
            value: "trading",
            content: (
                <div className="w-full overflow-hidden relative h-full rounded-2xl p-4 md:p-10 font-bold text-white bg-gradient-to-br from-gray-900 to-black border border-white/10 shadow-2xl">
                    <p className="text-xl md:text-3xl font-bold text-white mb-6">High-Frequency Execution</p>
                    <div className="h-[500px] md:h-[600px] shadow-inner bg-black/50 rounded-xl overflow-hidden">
                        <FeatureTerminal
                            title="jars-cli — execution"
                            steps={[
                                { type: "output", content: SPLASH_ART, style: "text-emerald-500 font-bold mb-4 leading-tight text-[10px] md:text-xs whitespace-pre" },
                                { type: "command", content: "subs follow --alias 'Quantum_X' --allocation 5000", delay: 800 },
                                { type: "output", content: ">> ATTACHING TO MASTER TRADER: Quantum_X", style: "text-blue-400 font-bold", delay: 300 },
                                { type: "output", content: "   Strategy: Mean Reversion [Risk: HIGH]", style: "text-yellow-500", delay: 200 },
                                { type: "output", content: "   Syncing portfolio snapshot...", style: "text-white/60", delay: 400 },
                                { type: "output", content: "✓ SYNC COMPLETE. MONITORING SIGNAL STREAM...", style: "text-emerald-500 animate-pulse", delay: 500 },
                                { type: "output", content: "...", style: "text-white/30", delay: 1000 },
                                { type: "output", content: "[SIGNAL DETECTED]  LONG BTC/USDT @ MARKET", style: "text-emerald-400 font-bold bg-emerald-950/30 p-1", delay: 100 },
                                { type: "output", content: "   Size: 0.15 BTC ($9,342.50)", style: "text-white", delay: 100 },
                                { type: "output", content: "   Risk Check: PASSED (Leverage < 3x)", style: "text-blue-300", delay: 100 },
                                { type: "output", content: ">> EXECUTING ORDER...", style: "text-yellow-400", delay: 50 },
                                { type: "output", content: "✓ FILL CONFIRMED: 62,145.50 (Slippage: 0.01%)", style: "text-emerald-500 font-bold", delay: 200 },
                                { type: "output", content: "   Latency: 45ms (Broker) + 12ms (Network)", style: "text-white/40", delay: 200 },
                                { type: "command", content: "pnl --live", delay: 2000 },
                                { type: "output", content: "Current Position: +$42.50 (0.45%) ▲", style: "text-emerald-400 text-lg", delay: 300 },
                            ]}
                        />
                    </div>
                </div>
            ),
        },
        {
            title: "Wallet",
            value: "wallet",
            content: (
                <div className="w-full overflow-hidden relative h-full rounded-2xl p-4 md:p-10 font-bold text-white bg-gradient-to-br from-gray-900 to-black border border-white/10 shadow-2xl">
                    <p className="text-xl md:text-3xl font-bold text-white mb-6">Instant Liquidity Access</p>
                    <div className="h-[500px] md:h-[600px] shadow-inner bg-black/50 rounded-xl overflow-hidden">
                        <FeatureTerminal
                            title="jars-cli — wallet"
                            steps={[
                                { type: "output", content: SPLASH_ART, style: "text-emerald-500 font-bold mb-4 leading-tight text-[10px] md:text-xs whitespace-pre" },
                                { type: "command", content: "wallet balance", delay: 800 },
                                { type: "output", content: "Total Equity:   $  4,250.00", style: "text-white", delay: 200 },
                                { type: "output", content: "Available:      $    150.00", style: "text-white/60", delay: 100 },
                                { type: "output", content: "In Positions:   $  4,100.00", style: "text-white/60", delay: 100 },
                                { type: "command", content: "wallet deposit 50000 --currency NGN --method bank_transfer", delay: 1500 },
                                { type: "output", content: ">> INITIATING SECURE GATEWAY (Paystack)...", style: "text-blue-400", delay: 300 },
                                { type: "output", content: "Generating one-time virtual account...", style: "text-white/60", delay: 400 },
                                { type: "output", content: "----------------------------------------", style: "text-white/30", delay: 100 },
                                { type: "output", content: "BANK:          Titan Trust Bank", style: "text-yellow-400 font-bold", delay: 100 },
                                { type: "output", content: "ACCOUNT:       9954 221 009", style: "text-yellow-400 font-bold", delay: 100 },
                                { type: "output", content: "REFERENCE:     JARS-DEP-88X", style: "text-white/60", delay: 100 },
                                { type: "output", content: "----------------------------------------", style: "text-white/30", delay: 100 },
                                { type: "output", content: "Waiting for transfer...", style: "text-white/40 animate-pulse", delay: 1500 },
                                { type: "output", content: "✓ PAYMENT RECEIVED: +₦50,000.00", style: "text-emerald-500 font-bold text-lg", delay: 200 },
                                { type: "output", content: "   New Balance: $4,285.00 (Converted)", style: "text-emerald-400", delay: 200 },
                            ]}
                        />
                    </div>
                </div>
            ),
        },
        {
            title: "Security",
            value: "security",
            content: (
                <div className="w-full overflow-hidden relative h-full rounded-2xl p-4 md:p-10 font-bold text-white bg-gradient-to-br from-gray-900 to-black border border-white/10 shadow-2xl">
                    <p className="text-xl md:text-3xl font-bold text-white mb-6">Zero-Trust Key Management</p>
                    <div className="h-[500px] md:h-[600px] shadow-inner bg-black/50 rounded-xl overflow-hidden">
                        <FeatureTerminal
                            title="jars-cli — vault"
                            steps={[
                                { type: "output", content: SPLASH_ART, style: "text-emerald-500 font-bold mb-4 leading-tight text-[10px] md:text-xs whitespace-pre" },
                                { type: "command", content: "keys audit --full", delay: 800 },
                                { type: "output", content: "Scanning local keystore...", style: "text-white/60", delay: 300 },
                                { type: "output", content: "[OK] Vault Encryption: AES-256-GCM", style: "text-emerald-500", delay: 100 },
                                { type: "output", content: "[OK] Key Permissions: READ/TRADE (No Withdraw)", style: "text-emerald-500", delay: 100 },
                                { type: "command", content: "keys add binance --label 'SafeFund'", delay: 1500 },
                                { type: "output", content: "Enter API Key: ************************", style: "text-white", delay: 300 },
                                { type: "output", content: "Enter Secret:  ************************", style: "text-white", delay: 300 },
                                { type: "output", content: ">> VALIDATING CREDENTIALS...", style: "text-blue-400", delay: 500 },
                                { type: "output", content: "   Connecting to Binance API... OK", style: "text-white/60", delay: 200 },
                                { type: "output", content: "   Verifying permissions... OK", style: "text-white/60", delay: 200 },
                                { type: "output", content: ">> ENCRYPTING...", style: "text-yellow-400", delay: 400 },
                                { type: "output", content: "✓ KEYSTORE UPDATED. ID: 8f92-a1b2", style: "text-emerald-500 font-bold", delay: 200 },
                                { type: "output", content: "   Your keys are encrypted locally. We never see them.", style: "text-white/40 italic", delay: 200 },
                            ]}
                        />
                    </div>
                </div>
            ),
        },
    ];

    return (
        <section className="py-24 bg-black relative">
            <div className="max-w-4xl mx-auto px-6 text-center mb-20">
                <h2 className="text-4xl md:text-6xl font-semibold tracking-tight text-white mb-6">
                    Complete control from <span className="text-emerald-500">one terminal</span>.
                </h2>
                <p className="text-lg text-white/40 max-w-2xl mx-auto leading-relaxed">
                    Manage infrastructure, copy-trading, and payments without leaving your keyboard.
                    The JARS CLI provides a unified interface for your entire operation.
                </p>
            </div>

            <div className="h-[45rem] md:h-[55rem] [perspective:1000px] relative b flex flex-col max-w-5xl mx-auto w-full items-start justify-start px-4">
                <Tabs tabs={tabs} />
            </div>
        </section>
    );
}
