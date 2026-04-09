from flask import Flask, request, render_template_string, jsonify
import sys
import os
import json

# Add the coding-agent/agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'coding-agent', 'agent'))

from agent import run_agent

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Coding Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    animation: {
                        'fade-in':    'fadeIn 0.8s ease-out forwards',
                        'slide-up':   'slideUp 0.7s ease-out forwards',
                        'float':      'float 6s ease-in-out infinite',
                        'float-slow': 'float 9s ease-in-out 1s infinite',
                        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite alternate',
                    },
                    keyframes: {
                        fadeIn:    { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
                        slideUp:   { '0%': { opacity: '0', transform: 'translateY(40px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
                        float:     { '0%,100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-22px)' } },
                        pulseGlow: { '0%': { 'box-shadow': '0 0 20px rgba(99,102,241,0.4)' }, '100%': { 'box-shadow': '0 0 55px rgba(139,92,246,0.75)' } },
                    }
                }
            }
        }
    </script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .gradient-text {
            background: linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #f0abfc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .btn-gradient {
            background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .btn-gradient:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(99,102,241,0.5);
        }
        .card-hover {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card-hover:hover {
            transform: translateY(-8px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
        }
        .output-content {
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 420px;
            overflow-y: auto;
            line-height: 1.65;
        }
        /* staggered animation delays */
        .d100 { animation-delay: 0.1s; opacity: 0; }
        .d200 { animation-delay: 0.2s; opacity: 0; }
        .d300 { animation-delay: 0.3s; opacity: 0; }
        .d400 { animation-delay: 0.4s; opacity: 0; }
        .d500 { animation-delay: 0.5s; opacity: 0; }
    </style>
</head>

<body class="bg-gray-950 antialiased">

    <!-- ═══════════════════════════════════════════ HERO ═══ -->
    <section class="relative overflow-hidden min-h-screen flex items-center"
             style="background: linear-gradient(135deg,#0f0c29 0%,#302b63 52%,#1a1a2e 100%);">

        <!-- Animated blobs -->
        <div class="absolute top-16 left-8 w-80 h-80 rounded-full bg-purple-700 opacity-20 blur-3xl animate-float"></div>
        <div class="absolute top-32 right-12 w-96 h-96 rounded-full bg-indigo-700 opacity-20 blur-3xl animate-float-slow"></div>
        <div class="absolute bottom-16 left-1/2 w-72 h-72 rounded-full bg-fuchsia-700 opacity-10 blur-3xl animate-float"></div>

        <!-- Subtle grid -->
        <div class="absolute inset-0 opacity-[0.04]"
             style="background-image:linear-gradient(rgba(255,255,255,0.15) 1px,transparent 1px),
                    linear-gradient(90deg,rgba(255,255,255,0.15) 1px,transparent 1px);
                    background-size:60px 60px;"></div>

        <div class="relative z-10 w-full max-w-7xl mx-auto px-6 py-28 text-center">

            <!-- Pill badge -->
            <div class="inline-flex items-center gap-2 bg-white/10 backdrop-blur border border-white/20
                        rounded-full px-5 py-2 mb-10 animate-fade-in">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span class="text-emerald-300 text-sm font-medium">Powered by GPT-4 &middot; Now with multi-file support</span>
            </div>

            <!-- Headline -->
            <h1 class="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-[1.05] mb-6
                       animate-slide-up d100">
                Code Smarter,<br>
                <span class="gradient-text">Ship Faster</span>
            </h1>

            <!-- Sub-headline -->
            <p class="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed mb-12
                      animate-slide-up d200">
                Your AI coding partner that generates, explains, and refactors code in seconds&hairsp;&mdash;&hairsp;so
                you can focus on what actually matters.
            </p>

            <!-- CTAs -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center mb-20 animate-slide-up d300">
                <a href="#agent"
                   class="btn-gradient text-white font-bold px-10 py-4 rounded-2xl text-lg
                          inline-flex items-center gap-3 shadow-xl cursor-pointer"
                   onclick="document.getElementById('agent').scrollIntoView({behavior:'smooth'}); setTimeout(unlockAgent,600); return false;">
                    <i class="fas fa-rocket"></i> Try it for $5
                </a>
                <a href="#pricing"
                   class="bg-white/10 backdrop-blur border border-white/20 text-white font-bold
                          px-10 py-4 rounded-2xl text-lg inline-flex items-center gap-3
                          hover:bg-white/20 transition-all duration-300">
                    <i class="fas fa-tag"></i> View Pricing
                </a>
            </div>

            <!-- Stats row -->
            <div class="grid grid-cols-3 max-w-lg mx-auto gap-6 animate-slide-up d400">
                <div>
                    <div class="text-3xl md:text-4xl font-black text-white">10K+</div>
                    <div class="text-gray-400 text-sm mt-1">Developers</div>
                </div>
                <div class="border-x border-white/10">
                    <div class="text-3xl md:text-4xl font-black text-white">500K+</div>
                    <div class="text-gray-400 text-sm mt-1">Lines Generated</div>
                </div>
                <div>
                    <div class="text-3xl md:text-4xl font-black text-white">99.9%</div>
                    <div class="text-gray-400 text-sm mt-1">Uptime</div>
                </div>
            </div>
        </div>

        <!-- Scroll caret -->
        <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
            <a href="#features" class="text-white/40 hover:text-white/80 transition-colors">
                <i class="fas fa-chevron-down text-2xl"></i>
            </a>
        </div>
    </section>

    <!-- ═══════════════════════════════════════ FEATURES ═══ -->
    <section id="features" class="bg-gray-900 border-y border-gray-800 py-16">
        <div class="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-10 text-center">

            <div class="group animate-fade-in d100">
                <div class="w-14 h-14 mx-auto mb-5 rounded-2xl bg-indigo-600/20 flex items-center justify-center
                            group-hover:bg-indigo-600/40 transition-colors duration-300">
                    <i class="fas fa-bolt text-indigo-400 text-xl"></i>
                </div>
                <h3 class="text-white font-bold text-lg mb-2">Instant Generation</h3>
                <p class="text-gray-400 text-sm leading-relaxed">Get production-ready code in seconds, not hours.</p>
            </div>

            <div class="group animate-fade-in d200">
                <div class="w-14 h-14 mx-auto mb-5 rounded-2xl bg-purple-600/20 flex items-center justify-center
                            group-hover:bg-purple-600/40 transition-colors duration-300">
                    <i class="fas fa-brain text-purple-400 text-xl"></i>
                </div>
                <h3 class="text-white font-bold text-lg mb-2">Smart Refactoring</h3>
                <p class="text-gray-400 text-sm leading-relaxed">Automatically improves code quality and performance.</p>
            </div>

            <div class="group animate-fade-in d300">
                <div class="w-14 h-14 mx-auto mb-5 rounded-2xl bg-fuchsia-600/20 flex items-center justify-center
                            group-hover:bg-fuchsia-600/40 transition-colors duration-300">
                    <i class="fas fa-book-open text-fuchsia-400 text-xl"></i>
                </div>
                <h3 class="text-white font-bold text-lg mb-2">Clear Explanations</h3>
                <p class="text-gray-400 text-sm leading-relaxed">Understand any codebase with human-friendly breakdowns.</p>
            </div>

        </div>
    </section>

    <!-- ═══════════════════════════════════════%= AGENT =%%══ -->
    <section id="agent" class="py-24 px-6" style="background:linear-gradient(160deg,#f8faff 0%,#eef2ff 100%);">
        <div class="max-w-5xl mx-auto">

            <div class="text-center mb-12">
                <h2 class="text-4xl md:text-5xl font-black text-gray-900 mb-3">
                    Your AI <span class="gradient-text">Coding Agent</span>
                </h2>
                <p class="text-gray-500 text-lg">Choose a task and let AI do the heavy lifting</p>
            </div>

            <!-- Agent card (locked until payment) -->
            <div class="relative bg-white rounded-3xl shadow-2xl overflow-hidden">

                <!-- ── Paywall overlay ── -->
                <div id="paywallOverlay"
                     class="absolute inset-0 z-20 flex flex-col items-center justify-center gap-6
                            rounded-3xl backdrop-blur-sm"
                     style="background:rgba(15,12,41,0.75);">
                    <div class="flex flex-col items-center gap-4 text-center px-8">
                        <div class="w-20 h-20 rounded-full bg-indigo-600/20 flex items-center justify-center
                                    border-2 border-indigo-500/40">
                            <i class="fas fa-lock text-indigo-300 text-3xl"></i>
                        </div>
                        <h3 class="text-white text-2xl font-black">Unlock the Agent</h3>
                        <p class="text-gray-300 text-sm max-w-xs">
                            Complete your $5 payment to access the full AI Coding Agent.
                        </p>
                        <button onclick="unlockAgent()"
                                class="btn-gradient text-white font-bold px-10 py-4 rounded-2xl text-lg
                                       inline-flex items-center gap-3 shadow-xl mt-2">
                            <i class="fas fa-credit-card"></i> Pay $5 &amp; Unlock
                        </button>
                        <p class="text-gray-500 text-xs">Secure checkout &middot; Instant access &middot; Cancel anytime</p>
                    </div>
                </div>

                <!-- Title bar -->
                <div class="bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-5 flex items-center gap-4">
                    <div class="flex gap-1.5">
                        <div class="w-3 h-3 rounded-full bg-red-400"></div>
                        <div class="w-3 h-3 rounded-full bg-yellow-400"></div>
                        <div class="w-3 h-3 rounded-full bg-emerald-400"></div>
                    </div>
                    <div class="flex items-center gap-2 text-white font-bold">
                        <i class="fas fa-robot"></i> AI Coding Agent
                    </div>
                    <div class="ml-auto flex items-center gap-2 bg-white/20 rounded-full px-3 py-1">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span class="text-white/90 text-xs font-medium">Online</span>
                    </div>
                </div>

                <div class="p-8">

                    <!-- Task switcher -->
                    <div class="flex flex-wrap gap-3 mb-8">
                        <button type="button" data-task="generate"
                                class="btn-task flex items-center gap-2 px-5 py-3 rounded-xl font-semibold
                                       border-2 border-indigo-600 bg-indigo-600 text-white
                                       transition-all duration-300 hover:shadow-lg">
                            <i class="fas fa-plus-circle"></i> Generate Code
                        </button>
                        <button type="button" data-task="explain"
                                class="btn-task flex items-center gap-2 px-5 py-3 rounded-xl font-semibold
                                       border-2 border-gray-200 bg-white text-indigo-600
                                       transition-all duration-300 hover:border-indigo-400 hover:bg-indigo-50">
                            <i class="fas fa-file-alt"></i> Explain Code
                        </button>
                        <button type="button" data-task="refactor"
                                class="btn-task flex items-center gap-2 px-5 py-3 rounded-xl font-semibold
                                       border-2 border-gray-200 bg-white text-indigo-600
                                       transition-all duration-300 hover:border-indigo-400 hover:bg-indigo-50">
                            <i class="fas fa-magic"></i> Refactor Code
                        </button>
                    </div>

                    <!-- Input -->
                    <div class="mb-6">
                        <label for="taskInput" id="inputLabel"
                               class="block text-sm font-semibold text-gray-700 mb-2">
                            Enter your coding requirement:
                        </label>
                        <textarea id="taskInput"
                                  class="w-full border-2 border-gray-200 rounded-xl p-4 font-mono text-sm
                                         focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200
                                         transition-all duration-300 resize-y min-h-[150px]"
                                  placeholder="Describe what you need..."></textarea>
                    </div>

                    <button id="submitBtn"
                            class="btn-gradient text-white font-bold py-3 px-8 rounded-xl
                                   inline-flex items-center gap-3 shadow-lg">
                        <i class="fas fa-paper-plane"></i> Process Request
                    </button>

                    <!-- Output -->
                    <div id="outputContainer"
                         class="hidden mt-8 p-5 bg-gray-50 rounded-2xl border-l-4 border-indigo-500 animate-fade-in">
                        <h5 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                            <i class="fas fa-check-circle text-emerald-500"></i> Result
                        </h5>
                        <div id="outputContent"
                             class="output-content bg-white p-4 rounded-xl border border-gray-200
                                    text-sm text-gray-700"></div>
                    </div>

                </div>
            </div>
        </div>
    </section>

    <!-- ════════════════════════════════════════ PRICING ═══ -->
    <section id="pricing" class="bg-gray-950 py-24 px-6">
        <div class="max-w-6xl mx-auto">

            <div class="text-center mb-16">
                <div class="inline-flex items-center gap-2 border border-indigo-500/30 bg-indigo-600/15
                            rounded-full px-5 py-2 mb-6">
                    <i class="fas fa-tag text-indigo-400 text-sm"></i>
                    <span class="text-indigo-300 text-sm font-medium">Simple, transparent pricing</span>
                </div>
                <h2 class="text-4xl md:text-5xl font-black text-white mb-4">
                    Choose Your <span class="gradient-text">Plan</span>
                </h2>
                <p class="text-gray-400 text-lg max-w-xl mx-auto">
                    Start free and scale as you grow. No hidden fees, cancel anytime.
                </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">

                <!-- ── Starter ── -->
                <div class="bg-gray-900 border border-gray-800 rounded-3xl p-8 card-hover animate-fade-in d100">
                    <div class="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center mb-5">
                        <i class="fas fa-seedling text-emerald-400 text-lg"></i>
                    </div>
                    <h3 class="text-white text-xl font-bold mb-1">Starter</h3>
                    <p class="text-gray-400 text-sm mb-6">Perfect for hobbyists &amp; learners</p>
                    <div class="mb-8">
                        <span class="text-5xl font-black text-white">$5</span>
                        <span class="text-gray-400 ml-1 text-sm">/month</span>
                    </div>
                    <ul class="space-y-3 mb-8 text-sm">
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-emerald-400 w-4"></i> 50 requests / month</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-emerald-400 w-4"></i> Code generation</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-emerald-400 w-4"></i> Basic explanations</li>
                        <li class="flex items-center gap-3 text-gray-500"><i class="fas fa-times text-gray-600 w-4"></i> Refactoring</li>
                        <li class="flex items-center gap-3 text-gray-500"><i class="fas fa-times text-gray-600 w-4"></i> Priority support</li>
                    </ul>
                    <button class="w-full py-3 rounded-xl border-2 border-gray-700 text-gray-300 font-semibold
                                   hover:border-indigo-500 hover:text-white transition-all duration-300">
                        Get Started Free
                    </button>
                </div>

                <!-- ── Pro (popular) ── -->
                <div class="animate-slide-up d200 relative">
                    <!-- gradient border wrapper -->
                    <div class="rounded-3xl p-[2px] card-hover animate-pulse-glow"
                         style="background:linear-gradient(135deg,#6366f1,#7c3aed,#a855f7);">
                        <div class="bg-gray-950 rounded-3xl p-8 relative">
                            <span class="absolute -top-4 left-1/2 -translate-x-1/2
                                         bg-gradient-to-r from-indigo-500 to-purple-500 text-white
                                         text-xs font-bold px-4 py-1.5 rounded-full shadow-lg animate-bounce
                                         whitespace-nowrap">
                                &#11088; MOST POPULAR
                            </span>
                            <div class="w-12 h-12 bg-indigo-600/30 rounded-2xl flex items-center justify-center mb-5 mt-3">
                                <i class="fas fa-rocket text-indigo-400 text-lg"></i>
                            </div>
                            <h3 class="text-white text-xl font-bold mb-1">Pro</h3>
                            <p class="text-gray-400 text-sm mb-6">For professional developers</p>
                            <div class="mb-8">
                                <span class="text-5xl font-black text-white">$19</span>
                                <span class="text-gray-400 ml-1 text-sm">/month</span>
                            </div>
                            <ul class="space-y-3 mb-8 text-sm">
                                <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-indigo-400 w-4"></i> Unlimited requests</li>
                                <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-indigo-400 w-4"></i> Code generation</li>
                                <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-indigo-400 w-4"></i> Advanced explanations</li>
                                <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-indigo-400 w-4"></i> Smart refactoring</li>
                                <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-indigo-400 w-4"></i> Priority support</li>
                            </ul>
                            <button class="w-full py-3 rounded-xl btn-gradient text-white font-bold shadow-xl
                                           shadow-indigo-900/50">
                                Start Pro Trial
                            </button>
                        </div>
                    </div>
                </div>

                <!-- ── Enterprise ── -->
                <div class="bg-gray-900 border border-gray-800 rounded-3xl p-8 card-hover animate-fade-in d300">
                    <div class="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center mb-5">
                        <i class="fas fa-building text-sky-400 text-lg"></i>
                    </div>
                    <h3 class="text-white text-xl font-bold mb-1">Enterprise</h3>
                    <p class="text-gray-400 text-sm mb-6">For teams &amp; organisations</p>
                    <div class="mb-8">
                        <span class="text-5xl font-black text-white">$79</span>
                        <span class="text-gray-400 ml-1 text-sm">/month</span>
                    </div>
                    <ul class="space-y-3 mb-8 text-sm">
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-sky-400 w-4"></i> Everything in Pro</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-sky-400 w-4"></i> Team workspace (20 seats)</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-sky-400 w-4"></i> Custom model fine-tuning</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-sky-400 w-4"></i> SSO &amp; audit logs</li>
                        <li class="flex items-center gap-3 text-gray-300"><i class="fas fa-check text-sky-400 w-4"></i> Dedicated account manager</li>
                    </ul>
                    <button class="w-full py-3 rounded-xl border-2 border-gray-700 text-gray-300 font-semibold
                                   hover:border-sky-500 hover:text-white transition-all duration-300">
                        Contact Sales
                    </button>
                </div>

            </div>

            <p class="text-center text-gray-500 text-sm mt-10">
                <i class="fas fa-shield-alt text-emerald-400 mr-2"></i>
                14-day free trial on all paid plans &middot; No credit card required &middot; Cancel anytime
            </p>
        </div>
    </section>

    <!-- ═════════════════════════════════════════ FOOTER ═══ -->
    <footer class="bg-gray-950 border-t border-gray-800 py-10 px-6">
        <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3 text-white font-bold text-lg">
                <i class="fas fa-robot text-indigo-400"></i> AI Coding Agent
            </div>
            <p class="text-gray-500 text-sm">&copy; 2026 AI Coding Agent. All rights reserved.</p>
            <div class="flex gap-5 text-gray-500 text-sm">
                <a href="#" class="hover:text-white transition-colors">Privacy</a>
                <a href="#" class="hover:text-white transition-colors">Terms</a>
                <a href="#" class="hover:text-white transition-colors">Contact</a>
            </div>
        </div>
    </footer>

    <script>
        const taskLabels = {
            generate: 'Enter your coding requirement:',
            explain:  'Paste the code you want to explain:',
            refactor: 'Paste the code you want to refactor:'
        };
        const taskHints = {
            generate: 'e.g., Create a function that calculates fibonacci numbers...',
            explain:  'e.g., Paste your Python code here...',
            refactor: 'e.g., Paste your code to optimize it...'
        };
        let currentTask = 'generate';

        document.querySelectorAll('.btn-task').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.btn-task').forEach(b => {
                    b.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-600');
                    b.classList.add('bg-white', 'text-indigo-600', 'border-gray-200');
                });
                this.classList.remove('bg-white', 'text-indigo-600', 'border-gray-200');
                this.classList.add('bg-indigo-600', 'text-white', 'border-indigo-600');
                currentTask = this.dataset.task;
                document.getElementById('inputLabel').textContent = taskLabels[currentTask];
                const ta = document.getElementById('taskInput');
                ta.placeholder = taskHints[currentTask];
                ta.value = '';
                document.getElementById('outputContainer').classList.add('hidden');
            });
        });

        document.getElementById('submitBtn').addEventListener('click', async function () {
            const input = document.getElementById('taskInput').value.trim();
            if (!input) { alert('Please enter your request.'); return; }

            const btn = this;
            btn.disabled = true;
            btn.innerHTML = '<span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>Processing...';

            try {
                const res  = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input, task_type: currentTask })
                });
                const data = await res.json();
                const out  = document.getElementById('outputContent');

                if (data.success) {
                    out.textContent = data.output;
                    out.className = 'output-content bg-white p-4 rounded-xl border border-gray-200 text-sm text-gray-700';
                } else {
                    out.innerHTML = `<span class="text-red-600"><i class="fas fa-exclamation-circle mr-2"></i>Error: ${data.error}</span>`;
                    out.className = 'output-content bg-red-50 p-4 rounded-xl border border-red-200 text-sm';
                }
                document.getElementById('outputContainer').classList.remove('hidden');
            } catch (err) {
                const out = document.getElementById('outputContent');
                out.innerHTML = `<span class="text-red-600"><i class="fas fa-exclamation-circle mr-2"></i>Error: ${err.message}</span>`;
                out.className = 'output-content bg-red-50 p-4 rounded-xl border border-red-200 text-sm';
                document.getElementById('outputContainer').classList.remove('hidden');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-paper-plane"></i> Process Request';
            }
        });

        document.getElementById('taskInput').addEventListener('keypress', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                document.getElementById('submitBtn').click();
            }
        });

        function unlockAgent() {
            const overlay = document.getElementById('paywallOverlay');
            if (!overlay) return;
            overlay.style.transition = 'opacity 0.5s ease';
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 500);
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        user_input = data.get('input', '').strip()
        task_type = data.get('task_type', 'generate')

        if not user_input:
            return jsonify({
                'success': False,
                'error': 'Input cannot be empty'
            }), 400

        # Run the agent
        output = run_agent(user_input, task_type)
        
        return jsonify({
            'success': True,
            'output': output
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    print("Starting AI Coding Agent on http://localhost:8080/")
    app.run(debug=True, host='0.0.0.0', port=8080)
