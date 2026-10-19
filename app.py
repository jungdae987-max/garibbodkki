import sys
import json
import random
import os
import webbrowser
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>스마트 자리 뽑기 (Smart Seat Picker)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons CDN -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- html2canvas for exporting layout as PNG image -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <!-- Canvas Confetti for completion effect -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
        }

        /* 3D Card Flip Animation Styles */
        .perspective-1000 {
            perspective: 1000px;
        }
        .transform-style-3d {
            transform-style: preserve-3d;
        }
        .backface-hidden {
            backface-visibility: hidden;
            -webkit-backface-visibility: hidden;
        }
        .rotate-y-180 {
            transform: rotateY(180deg);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.6);
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }

        /* Print Media Styles */
        @media print {
            body {
                background-color: white !important;
                color: black !important;
            }
            header, section:first-child, .no-print {
                display: none !important;
            }
            #seating-board-wrapper {
                background: white !important;
                border: none !important;
                box-shadow: none !important;
                color: black !important;
            }
            .card-back-print {
                background: #f8fafc !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
            }
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between selection:bg-indigo-500 selection:text-white">

    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl shadow-lg shadow-indigo-500/30">
                    <i data-lucide="layout-grid" class="w-6 h-6 text-white"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg sm:text-xl bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">스마트 자리 뽑기</h1>
                    <p class="text-xs text-slate-400 hidden sm:block">공정하고 편리한 Flask 기반 인터랙티브 좌석 배치 시스템</p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button id="btn-reset-all" class="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 border border-slate-700/50">
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i> 전체 초기화
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content Area -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex-grow grid grid-cols-1 lg:grid-cols-12 gap-6">

        <!-- Left Sidebar: Configuration Panel -->
        <section class="lg:col-span-4 space-y-5">
            
            <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-4">
                
                <!-- Step 1: Participants List -->
                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label class="text-sm font-semibold text-slate-200 flex items-center gap-2">
                            <span class="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs flex items-center justify-center font-bold">1</span>
                            참여자 명단
                        </label>
                        <span id="participant-count" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-indigo-400 font-medium">0명</span>
                    </div>
                    <textarea id="input-participants" rows="4" 
                        class="w-full bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-y"
                        placeholder="이름을 콤마(,) 또는 줄바꿈으로 구분해 입력하세요.&#10;예: 김철수, 이영희, 박민수, 정수진"></textarea>
                </div>

                <hr class="border-slate-800">

                <!-- Step 2: Grid Layout Settings -->
                <div>
                    <label class="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
                        <span class="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs flex items-center justify-center font-bold">2</span>
                        배치 및 그리드 규격
                    </label>

                    <div class="grid grid-cols-2 gap-3 mb-3">
                        <div>
                            <label class="text-xs text-slate-400 mb-1 block">행 수 (Row)</label>
                            <input type="number" id="input-rows" min="1" max="15" value="4" 
                                class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="text-xs text-slate-400 mb-1 block">열 수 (Col)</label>
                            <input type="number" id="input-cols" min="1" max="15" value="6" 
                                class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500">
                        </div>
                    </div>

                    <div class="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-400">
                        <span>총 좌석 용량:</span>
                        <span id="total-capacity-badge" class="font-bold text-slate-200">24석</span>
                    </div>
                </div>

                <hr class="border-slate-800">

                <!-- Step 3: Constraints -->
                <div>
                    <label class="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
                        <span class="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs flex items-center justify-center font-bold">3</span>
                        특별 조건 (고정 & 격리)
                    </label>

                    <div class="space-y-3">
                        <!-- Fixed Seat Rule -->
                        <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80 space-y-2">
                            <span class="text-xs font-medium text-indigo-300 flex items-center gap-1">
                                <i data-lucide="pin" class="w-3.5 h-3.5"></i> 특정 자리 고정
                            </span>
                            <div class="flex gap-2">
                                <select id="select-fixed-person" class="bg-slate-900 border border-slate-700 text-xs rounded-lg p-2 text-slate-200 flex-grow focus:outline-none focus:border-indigo-500">
                                    <option value="">인원 선택</option>
                                </select>
                                <select id="select-fixed-seat" class="bg-slate-900 border border-slate-700 text-xs rounded-lg p-2 text-slate-200 flex-grow focus:outline-none focus:border-indigo-500">
                                    <option value="">좌석 선택</option>
                                </select>
                                <button id="btn-add-fixed" class="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors">
                                    추가
                                </button>
                            </div>
                        </div>

                        <!-- Isolation Rule -->
                        <div class="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80 space-y-2">
                            <span class="text-xs font-medium text-rose-400 flex items-center gap-1">
                                <i data-lucide="user-x" class="w-3.5 h-3.5"></i> 서로 이웃 금지 (격리)
                            </span>
                            <div class="flex gap-2">
                                <select id="select-iso-p1" class="bg-slate-900 border border-slate-700 text-xs rounded-lg p-2 text-slate-200 w-1/2 focus:outline-none focus:border-indigo-500">
                                    <option value="">A 인원</option>
                                </select>
                                <select id="select-iso-p2" class="bg-slate-900 border border-slate-700 text-xs rounded-lg p-2 text-slate-200 w-1/2 focus:outline-none focus:border-indigo-500">
                                    <option value="">B 인원</option>
                                </select>
                                <button id="btn-add-iso" class="px-3 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold transition-colors">
                                    추가
                                </button>
                            </div>
                        </div>

                        <!-- Active Rules List -->
                        <div id="rules-container" class="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                        </div>
                    </div>
                </div>

                <!-- Draw Button -->
                <button id="btn-draw" class="w-full py-3.5 px-4 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold text-base rounded-xl shadow-lg shadow-indigo-500/25 active:scale-[0.99] transition-all flex items-center justify-center gap-2">
                    <i data-lucide="sparkles" class="w-5 h-5"></i>
                    <span>자리 무작위 추첨 시작</span>
                </button>
            </div>
        </section>

        <!-- Right Section: Seat Board & Output -->
        <section class="lg:col-span-8 flex flex-col space-y-4">
            
            <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-xl no-print">
                <div class="flex items-center gap-3">
                    <div class="flex items-center gap-2 text-xs text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                        <i data-lucide="presentation" class="w-4 h-4 text-indigo-400"></i>
                        <span>교탁/교단 위치: <strong>상단 Central</strong></span>
                    </div>
                </div>

                <!-- Action Controls -->
                <div class="flex items-center gap-2">
                    <button id="btn-reveal-all" disabled class="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-200 rounded-lg transition-colors flex items-center gap-1.5 border border-slate-700">
                        <i data-lucide="eye" class="w-3.5 h-3.5"></i> 전체 공개
                    </button>
                    <div class="h-4 w-px bg-slate-800"></div>
                    <button id="btn-export-text" disabled class="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-200 rounded-lg transition-colors flex items-center gap-1.5 border border-slate-700">
                        <i data-lucide="copy" class="w-3.5 h-3.5"></i> 텍스트 복사
                    </button>
                    <button id="btn-export-img" disabled class="px-3 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-1.5 shadow-md">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i> 이미지 저장
                    </button>
                    <button id="btn-print" disabled class="px-3 py-1.5 text-xs font-medium bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-1.5 shadow-md">
                        <i data-lucide="printer" class="w-3.5 h-3.5"></i> 인쇄
                    </button>
                </div>
            </div>

            <!-- The Main Seat Grid Viewboard -->
            <div id="seating-board-wrapper" class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl flex-grow flex flex-col justify-between overflow-x-auto relative">
                
                <!-- Blackboard Marker -->
                <div class="w-full max-w-xs mx-auto mb-6 py-2 px-6 bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800 border border-slate-600 rounded-lg text-center text-xs font-bold tracking-widest text-slate-300 shadow-inner flex items-center justify-center gap-2">
                    <i data-lucide="monitor" class="w-4 h-4 text-indigo-400"></i>
                    칠판 / 교탁 (FRONT)
                </div>

                <!-- Seat Grid Container -->
                <div id="seat-grid" class="grid gap-3 sm:gap-4 my-auto mx-auto w-full justify-center transition-all duration-300">
                    <div class="col-span-full py-16 text-center text-slate-500 space-y-2">
                        <i data-lucide="layout" class="w-12 h-12 mx-auto stroke-1 text-slate-600"></i>
                        <p class="text-sm">참여자 명단을 입력하고 [자리 무작위 추첨 시작] 버튼을 누르세요.</p>
                    </div>
                </div>

                <!-- Grid Footer -->
                <div class="mt-6 text-center text-xs text-slate-500 no-print">
                    * 카드를 클릭하면 해당 자리만 하나씩 개별 공개할 수 있습니다.
                </div>
            </div>

        </section>
    </main>

    <footer class="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500 no-print">
        <p>© 2026 Interactive Smart Seat Manager. Powered by Flask & Vanilla JS.</p>
    </footer>

    <div id="toast-container" class="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none"></div>

    <script>
        const state = {
            participants: [],
            rows: 4,
            cols: 6,
            fixedRules: [],
            isolationRules: [],
            assignedSeats: [],
            isDrawing: false
        };

        const elInputs = {
            participants: document.getElementById('input-participants'),
            rows: document.getElementById('input-rows'),
            cols: document.getElementById('input-cols'),
            participantCount: document.getElementById('participant-count'),
            capacityBadge: document.getElementById('total-capacity-badge'),
            
            selectFixedPerson: document.getElementById('select-fixed-person'),
            selectFixedSeat: document.getElementById('select-fixed-seat'),
            btnAddFixed: document.getElementById('btn-add-fixed'),

            selectIsoP1: document.getElementById('select-iso-p1'),
            selectIsoP2: document.getElementById('select-iso-p2'),
            btnAddIso: document.getElementById('btn-add-iso'),

            rulesContainer: document.getElementById('rules-container'),
            seatGrid: document.getElementById('seat-grid'),
            seatingBoardWrapper: document.getElementById('seating-board-wrapper'),

            btnDraw: document.getElementById('btn-draw'),
            btnRevealAll: document.getElementById('btn-reveal-all'),
            btnExportText: document.getElementById('btn-export-text'),
            btnExportImg: document.getElementById('btn-export-img'),
            btnPrint: document.getElementById('btn-print'),
            btnResetAll: document.getElementById('btn-reset-all')
        };

        window.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            setupEventListeners();
            parseParticipants();
            updateSeatDropdowns();
            renderGridPlaceholder();
        });

        function setupEventListeners() {
            elInputs.participants.addEventListener('input', () => {
                parseParticipants();
                updateRuleDropdowns();
            });

            elInputs.rows.addEventListener('change', handleGridDimensionChange);
            elInputs.cols.addEventListener('change', handleGridDimensionChange);

            elInputs.btnAddFixed.addEventListener('click', addFixedRule);
            elInputs.btnAddIso.addEventListener('click', addIsolationRule);

            elInputs.btnDraw.addEventListener('click', startSeatDrawing);
            elInputs.btnRevealAll.addEventListener('click', revealAllCards);
            elInputs.btnExportText.addEventListener('click', exportAsText);
            elInputs.btnExportImg.addEventListener('click', exportAsImage);
            elInputs.btnPrint.addEventListener('click', () => window.print());
            elInputs.btnResetAll.addEventListener('click', resetAll);
        }

        function parseParticipants() {
            const rawText = elInputs.participants.value;
            state.participants = rawText
                .split(/[\\n,]/)
                .map(s => s.trim())
                .filter(s => s.length > 0);
            
            elInputs.participantCount.textContent = `${state.participants.length}명`;
            updateCapacityCheck();
        }

        function handleGridDimensionChange() {
            let r = parseInt(elInputs.rows.value) || 1;
            let c = parseInt(elInputs.cols.value) || 1;
            
            r = Math.max(1, Math.min(15, r));
            c = Math.max(1, Math.min(15, c));

            state.rows = r;
            state.cols = c;
            elInputs.rows.value = r;
            elInputs.cols.value = c;

            updateCapacityCheck();
            updateSeatDropdowns();
            
            state.fixedRules = state.fixedRules.filter(rule => rule.row <= r && rule.col <= c);
            renderRulesTags();
        }

        function updateCapacityCheck() {
            const capacity = state.rows * state.cols;
            elInputs.capacityBadge.textContent = `${capacity}석`;
            
            if (state.participants.length > capacity) {
                elInputs.capacityBadge.className = "font-bold text-rose-400";
            } else {
                elInputs.capacityBadge.className = "font-bold text-slate-200";
            }
        }

        function updateRuleDropdowns() {
            const currentP = state.participants;
            const prevFixedP = elInputs.selectFixedPerson.value;
            
            elInputs.selectFixedPerson.innerHTML = '<option value="">인원 선택</option>' + 
                currentP.map(p => `<option value="${p}">${p}</option>`).join('');
            elInputs.selectFixedPerson.value = prevFixedP;

            const prevIso1 = elInputs.selectIsoP1.value;
            const prevIso2 = elInputs.selectIsoP2.value;

            const pOptions = '<option value="">인원 선택</option>' + currentP.map(p => `<option value="${p}">${p}</option>`).join('');
            elInputs.selectIsoP1.innerHTML = pOptions;
            elInputs.selectIsoP2.innerHTML = pOptions;

            elInputs.selectIsoP1.value = prevIso1;
            elInputs.selectIsoP2.value = prevIso2;
        }

        function updateSeatDropdowns() {
            const prevSeat = elInputs.selectFixedSeat.value;
            let options = '<option value="">좌석 선택</option>';

            for (let r = 1; r <= state.rows; r++) {
                for (let c = 1; c <= state.cols; c++) {
                    options += `<option value="${r}-${c}">${r}행 ${c}열</option>`;
                }
            }
            elInputs.selectFixedSeat.innerHTML = options;
            elInputs.selectFixedSeat.value = prevSeat;
        }

        function addFixedRule() {
            const person = elInputs.selectFixedPerson.value;
            const seatVal = elInputs.selectFixedSeat.value;

            if (!person || !seatVal) {
                showToast("고정할 인원과 좌석을 모두 선택해 주세요.", "error");
                return;
            }

            const [r, c] = seatVal.split('-').map(Number);

            if (state.fixedRules.some(rule => rule.person === person)) {
                showToast(`${person}님은 이미 특정 자리에 고정되어 있습니다.`, "error");
                return;
            }
            if (state.fixedRules.some(rule => rule.row === r && rule.col === c)) {
                showToast(`${r}행 ${c}열 자리는 이미 다른 참가자가 고정되어 있습니다.`, "error");
                return;
            }

            state.fixedRules.push({ person, row: r, col: c });
            renderRulesTags();
            showToast(`${person}님을 ${r}행 ${c}열에 고정했습니다.`);
        }

        function addIsolationRule() {
            const p1 = elInputs.selectIsoP1.value;
            const p2 = elInputs.selectIsoP2.value;

            if (!p1 || !p2) {
                showToast("격리할 두 인원을 선택해 주세요.", "error");
                return;
            }
            if (p1 === p2) {
                showToast("서로 다른 두 명을 선택해야 합니다.", "error");
                return;
            }

            const exists = state.isolationRules.some(([a, b]) => 
                (a === p1 && b === p2) || (a === p2 && b === p1)
            );

            if (exists) {
                showToast("이미 설정된 격리 조건입니다.", "error");
                return;
            }

            state.isolationRules.push([p1, p2]);
            renderRulesTags();
            showToast(`${p1}님과 ${p2}님은 인접하지 않도록 설정되었습니다.`);
        }

        function removeFixedRule(index) {
            state.fixedRules.splice(index, 1);
            renderRulesTags();
        }

        function removeIsoRule(index) {
            state.isolationRules.splice(index, 1);
            renderRulesTags();
        }

        function renderRulesTags() {
            let html = '';

            state.fixedRules.forEach((rule, idx) => {
                html += `
                    <div class="flex items-center justify-between px-2.5 py-1 bg-indigo-950/60 border border-indigo-800/80 rounded-lg text-xs text-indigo-300">
                        <span>📌 <strong>${rule.person}</strong> ➔ ${rule.row}행 ${rule.col}열</span>
                        <button onclick="removeFixedRule(${idx})" class="text-indigo-400 hover:text-indigo-100 ml-2">
                            <i data-lucide="x" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                `;
            });

            state.isolationRules.forEach(([a, b], idx) => {
                html += `
                    <div class="flex items-center justify-between px-2.5 py-1 bg-rose-950/60 border border-rose-800/80 rounded-lg text-xs text-rose-300">
                        <span>🚫 <strong>${a}</strong> ↔ <strong>${b}</strong> 격리</span>
                        <button onclick="removeIsoRule(${idx})" class="text-rose-400 hover:text-rose-100 ml-2">
                            <i data-lucide="x" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                `;
            });

            elInputs.rulesContainer.innerHTML = html;
            lucide.createIcons();
        }

        async function startSeatDrawing() {
            if (state.participants.length === 0) {
                showToast("참여자 명단을 입력해 주세요.", "error");
                return;
            }

            try {
                const response = await fetch('/api/draw', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        participants: state.participants,
                        rows: state.rows,
                        cols: state.cols,
                        fixedRules: state.fixedRules,
                        isolationRules: state.isolationRules
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    showToast(data.error || "추첨 작업 중 오류가 발생했습니다.", "error");
                    return;
                }

                state.assignedSeats = data.result;
                state.isDrawing = true;

                elInputs.btnRevealAll.disabled = false;
                elInputs.btnExportText.disabled = false;
                elInputs.btnExportImg.disabled = false;
                elInputs.btnPrint.disabled = false;

                elInputs.seatGrid.style.gridTemplateColumns = `repeat(${state.cols}, minmax(0, 1fr))`;
                elInputs.seatGrid.innerHTML = '';

                state.assignedSeats.forEach((seat) => {
                    const cardEl = createSeatCardElement(seat);
                    elInputs.seatGrid.appendChild(cardEl);
                });

                lucide.createIcons();
                showToast("추첨이 완료되었습니다! 카드를 클릭해 자리를 확인하세요. 🎉");

            } catch (err) {
                console.error(err);
                showToast("서버와 통신하는 중 문제가 발생했습니다.", "error");
            }
        }

        function createSeatCardElement(seat) {
            const wrapper = document.createElement('div');
            wrapper.className = "perspective-1000 w-full aspect-[4/3] min-w-[70px] sm:min-w-[90px]";

            const inner = document.createElement('div');
            inner.id = `card-inner-${seat.row}-${seat.col}`;
            inner.className = `w-full h-full relative transform-style-3d transition-transform duration-700 cursor-pointer rounded-xl border ${
                seat.isRevealed ? 'rotate-y-180' : ''
            }`;

            const front = document.createElement('div');
            front.className = `absolute inset-0 backface-hidden bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 rounded-xl flex flex-col items-center justify-center p-1 text-center shadow-lg hover:border-indigo-500/80 hover:shadow-indigo-500/20 transition-all`;
            front.innerHTML = `
                <span class="text-[10px] sm:text-xs font-semibold text-slate-400 mb-0.5">${seat.row}-${seat.col}</span>
                <i data-lucide="help-circle" class="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400/80 animate-pulse"></i>
            `;

            const back = document.createElement('div');
            const hasPerson = seat.person !== null;
            const bgGradient = seat.isFixed 
                ? 'from-indigo-900/90 to-purple-900/90 border-indigo-500' 
                : hasPerson 
                    ? 'from-slate-800 to-slate-850 border-slate-600' 
                    : 'from-slate-950 to-slate-900 border-slate-800/50 opacity-40';

            back.className = `absolute inset-0 backface-hidden rotate-y-180 bg-gradient-to-br ${bgGradient} card-back-print border rounded-xl flex flex-col items-center justify-center p-1 text-center shadow-md`;
            
            back.innerHTML = `
                <span class="text-[9px] sm:text-[11px] text-slate-400 font-medium">${seat.row}행 ${seat.col}열</span>
                <span class="text-xs sm:text-base font-bold text-slate-100 truncate w-full px-1 my-0.5">${seat.person || '빈 자리'}</span>
                ${seat.isFixed ? '<span class="text-[8px] bg-indigo-500/30 text-indigo-300 px-1.5 py-0.2 rounded">고정</span>' : ''}
            `;

            inner.appendChild(front);
            inner.appendChild(back);
            wrapper.appendChild(inner);

            wrapper.addEventListener('click', () => toggleCardReveal(seat.row, seat.col));

            return wrapper;
        }

        function toggleCardReveal(r, c) {
            const seat = state.assignedSeats.find(s => s.row === r && s.col === c);
            if (!seat) return;

            seat.isRevealed = !seat.isRevealed;
            const inner = document.getElementById(`card-inner-${r}-${c}`);
            if (inner) {
                inner.classList.toggle('rotate-y-180', seat.isRevealed);
            }

            if (state.assignedSeats.every(s => s.isRevealed)) {
                triggerConfetti();
            }
        }

        function revealAllCards() {
            let delay = 0;
            state.assignedSeats.forEach((seat) => {
                if (!seat.isRevealed) {
                    setTimeout(() => {
                        toggleCardReveal(seat.row, seat.col);
                    }, delay);
                    delay += 40;
                }
            });
        }

        function exportAsText() {
            if (state.assignedSeats.length === 0) return;

            let resultText = `=== [스마트 자리 배치 결과] ===\\n`;
            resultText += `규격: ${state.rows}행 ${state.cols}열 (총 ${state.participants.length}명)\\n\\n`;

            for (let r = 1; r <= state.rows; r++) {
                let rowStr = `[${r}행] `;
                for (let c = 1; c <= state.cols; c++) {
                    const seat = state.assignedSeats.find(s => s.row === r && s.col === c);
                    const name = seat && seat.person ? seat.person : '빈자리';
                    rowStr += `${c}열: ${name}\\t`;
                }
                resultText += rowStr + '\\n';
            }

            const dummy = document.createElement("textarea");
            document.body.appendChild(dummy);
            dummy.value = resultText;
            dummy.select();
            document.execCommand("copy");
            document.body.removeChild(dummy);

            showToast("자리 배치 결과가 클립보드에 복사되었습니다!");
        }

        function exportAsImage() {
            const target = elInputs.seatingBoardWrapper;
            showToast("이미지를 생성 중입니다...", "info");

            html2canvas(target, {
                backgroundColor: '#0f172a',
                scale: 2
            }).then(canvas => {
                const link = document.createElement('a');
                link.download = `자리배치결과_${new Date().toISOString().slice(0,10)}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
                showToast("이미지 다운로드가 시작되었습니다!");
            }).catch(err => {
                showToast("이미지 저장 중 오류가 발생했습니다.", "error");
                console.error(err);
            });
        }

        function renderGridPlaceholder() {
            elInputs.seatGrid.style.gridTemplateColumns = `repeat(${state.cols}, minmax(0, 1fr))`;
            elInputs.seatGrid.innerHTML = `
                <div class="col-span-full py-16 text-center text-slate-500 space-y-2">
                    <i data-lucide="layout" class="w-12 h-12 mx-auto stroke-1 text-slate-600"></i>
                    <p class="text-sm">참여자 명단을 입력하고 [자리 무작위 추첨 시작] 버튼을 누르세요.</p>
                </div>
            `;
            lucide.createIcons();
        }

        function resetAll() {
            state.participants = [];
            state.fixedRules = [];
            state.isolationRules = [];
            state.assignedSeats = [];
            state.isDrawing = false;

            elInputs.participants.value = '';
            elInputs.rows.value = 4;
            elInputs.cols.value = 6;

            handleGridDimensionChange();
            parseParticipants();
            renderRulesTags();
            renderGridPlaceholder();

            elInputs.btnRevealAll.disabled = true;
            elInputs.btnExportText.disabled = true;
            elInputs.btnExportImg.disabled = true;
            elInputs.btnPrint.disabled = true;

            showToast("모든 설정이 초기화되었습니다.");
        }

        function triggerConfetti() {
            if (typeof confetti === 'function') {
                confetti({
                    particleCount: 80,
                    spread: 70,
                    origin: { y: 0.6 }
                });
            }
        }

        function showToast(message, type = "success") {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            
            const bgColor = type === "error" 
                ? "bg-rose-900/90 border-rose-700 text-rose-100" 
                : type === "info"
                    ? "bg-sky-900/90 border-sky-700 text-sky-100"
                    : "bg-slate-800/90 border-indigo-500/80 text-slate-100";

            toast.className = `px-4 py-3 rounded-xl border shadow-2xl backdrop-blur-md text-xs sm:text-sm font-medium flex items-center gap-2 transform transition-all duration-300 translate-y-2 opacity-0 pointer-events-auto ${bgColor}`;
            
            const iconName = type === "error" ? "alert-circle" : type === "info" ? "info" : "check-circle-2";
            toast.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4"></i> <span>${message}</span>`;

            container.appendChild(toast);
            lucide.createIcons();

            requestAnimationFrame(() => {
                toast.classList.remove('translate-y-2', 'opacity-0');
            });

            setTimeout(() => {
                toast.classList.add('opacity-0', 'translate-y-2');
                setTimeout(() => {
                    if (toast.parentNode) toast.parentNode.removeChild(toast);
                }, 300);
            }, 3000);
        }
    </script>
</body>
</html>
"""

def is_adjacent(r1, c1, r2, c2):
    """Checks if two seats (r1, c1) and (r2, c2) are orthogonally or diagonally adjacent."""
    dr = abs(r1 - r2)
    dc = abs(c1 - c2)
    return dr <= 1 and dc <= 1 and not (dr == 0 and dc == 0)

@app.route('/')
def index():
    """Renders the single-page application UI."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/draw', methods=['POST'])
def draw_seats():
    """API endpoint to calculate fair random seat allocation matching constraints."""
    data = request.get_json() or {}
    
    participants = data.get('participants', [])
    rows = int(data.get('rows', 4))
    cols = int(data.get('cols', 6))
    fixed_rules = data.get('fixedRules', [])
    isolation_rules = data.get('isolationRules', [])

    capacity = rows * cols
    if len(participants) > capacity:
        return jsonify({'error': f'참여 인원({len(participants)}명)이 전체 좌석 용량({capacity}석)보다 많습니다.'}), 400

    max_attempts = 1000
    for attempt in range(max_attempts):
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        unassigned_people = list(participants)
        free_seats = [{'r': r, 'c': c} for r in range(1, rows + 1) for c in range(1, cols + 1)]

        # 1. Place fixed rules
        fixed_valid = True
        for rule in fixed_rules:
            person = rule.get('person')
            r = rule.get('row')
            c = rule.get('col')

            if person not in unassigned_people:
                continue

            grid[r - 1][c - 1] = person
            unassigned_people.remove(person)
            free_seats = [s for s in free_seats if not (s['r'] == r and s['c'] == c)]

        if not fixed_valid:
            continue

        # 2. Random Shuffle (Fisher-Yates via Python random.shuffle)
        random.shuffle(unassigned_people)
        random.shuffle(free_seats)

        for i, person in enumerate(unassigned_people):
            seat = free_seats[i]
            grid[seat['r'] - 1][seat['c'] - 1] = person

        # 3. Validate isolation constraints
        valid_isolation = True
        for p1, p2 in isolation_rules:
            pos1, pos2 = None, None
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    if grid[r - 1][c - 1] == p1:
                        pos1 = (r, c)
                    if grid[r - 1][c - 1] == p2:
                        pos2 = (r, c)

            if pos1 and pos2 and is_adjacent(pos1[0], pos1[1], pos2[0], pos2[1]):
                valid_isolation = False
                break

        if valid_isolation:
            result = []
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    person = grid[r - 1][c - 1]
                    is_fixed = any(rule.get('row') == r and rule.get('col') == c for rule in fixed_rules)
                    result.append({
                        'id': f'seat-{r}-{c}',
                        'row': r,
                        'col': c,
                        'person': person,
                        'isRevealed': False,
                        'isFixed': is_fixed
                    })
            return jsonify({'result': result})

    return jsonify({'error': '격리 조건이 너무 까다로워 조건을 만족하는 배치를 찾지 못했습니다.'}), 400

if __name__ == '__main__':
    port = 5000
    url = f"http://127.0.0.1:{port}"
    
    print("=" * 60)
    print(f"🚀 스마트 자리 뽑기 Flask 서버가 실행되었습니다: {url}")
    print("=" * 60)

    # Open browser automatically if running interactively
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        webbrowser.open(url)

    app.run(host='0.0.0.0', port=port, debug=True)
