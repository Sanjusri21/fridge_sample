/**
 * ALINA Smart Fridge OS - Advanced AI Character & Frontend Controller
 * Complete 3-Column Cyber Appliance Interface with Animated Background & Character Rig
 */

const API_BASE = "/api";

// ================= GLOBAL STATE =================
let allFoods = [];
let pendingConsumptionFoodId = null;
let pendingConsumedWeight = null;
let currentAlinaState = "idle";
let stateResetTimeout = null;
let lastDoorStatus = "closed";

// Emojis for food catalog
const FOOD_ICONS = {
  chicken: "🍗",
  milk: "🥛",
  eggs: "🥚",
  egg: "🥚",
  cheese: "🧀",
  apple: "🍎",
  apples: "🍎",
  bread: "🍞",
  rice: "🍚",
  fish: "🐟",
  vegetables: "🥦",
  vegetable: "🥦",
  curd: "🥣",
  yogurt: "🍦",
  meat: "🥩",
  fruit: "🍓",
  butter: "🧈",
  carrot: "🥕",
  tomato: "🍅"
};

// SVG Mouth Path Morphs for emotional expressions
const MOUTH_PATHS = {
  idle: "M 86 126 Q 100 134 114 126",
  listening: "M 90 128 Q 100 128 110 128",
  thinking: "M 88 128 Q 94 132 112 127",
  happy: "M 82 124 Q 100 144 118 124",
  excited: "M 80 122 Q 100 148 120 122",
  concerned: "M 86 132 Q 100 124 114 132",
  warning: "M 85 130 L 115 130",
  angry: "M 85 135 Q 100 124 115 135",
  sad: "M 86 136 Q 100 122 114 136",
  celebration: "M 78 120 Q 100 152 122 120",
  error: "M 86 130 Q 93 135 100 130 T 114 130",
};

// Character Voice Thoughts / Ribbons by state
const STATE_THOUGHTS = {
  idle: "Hi! I'm ALINA. Your smart fridge friend.",
  listening: "I am listening attentively. Speak or type your request...",
  thinking: "Analyzing ingredients and evaluating freshness matrices...",
  happy: "Wonderful! Everything in your fridge is running smoothly.",
  excited: "New food safely logged into your smart fridge!",
  concerned: "Heads up! We have groceries nearing their expiry date.",
  warning: "Critical shelf-life warning! Please use expiring items today.",
  angry: "Refrigerator door left open! Cold air is escaping!",
  sad: "Oh no... food went to waste. Let us try to consume on time.",
  celebration: "Magnificent! You consumed groceries on time: +10 Points! 🎉",
  error: "Neural confusion: operation encountered an issue.",
};

// ================= DOM ELEMENTS =================
const alinaSvg = document.getElementById("alina-character-svg");
const alinaCharacterBox = document.getElementById("alina-character-box");
const alinaAmbientBackdrop = document.getElementById("alina-ambient-backdrop");
const alinaStateDisplay = document.getElementById("alina-state-display");
const alinaSpeechRibbon = document.getElementById("alina-speech-ribbon");
const alinaMouthPath = document.getElementById("alina-mouth-path");
const foodCardsGrid = document.getElementById("food-cards-grid");
const inventoryTbody = document.getElementById("inventory-tbody");
const emptyInventory = document.getElementById("empty-inventory");
const chatHistory = document.getElementById("chat-history");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input-text");
const eventsList = document.getElementById("events-list");

// Telemetry Elements
const cardTemp = document.getElementById("card-temp");
const cardTempSub = document.getElementById("card-temp-sub");
const cardDoor = document.getElementById("card-door");
const cardDoorSub = document.getElementById("card-door-sub");
const cardFoodCount = document.getElementById("card-food-count");
const cardExpiringSub = document.getElementById("card-expiring-sub");
const cardWeight = document.getElementById("card-weight");
const headerPointsBadge = document.getElementById("header-points-badge");

// Modals
const modalAddFood = document.getElementById("modal-add-food");
const modalScanFood = document.getElementById("modal-scan-food");
const modalConsumption = document.getElementById("modal-consumption-confirm");

// ================= FLOATING BACKGROUND PARTICLES =================

function initFloatingParticles() {
  const container = document.getElementById("floating-particles-layer");
  if (!container) return;
  container.innerHTML = "";

  const colors = ["#22D3EE", "#8B5CF6", "#EC4899", "#FFFFFF", "#38BDF8"];
  const particleCount = 28;

  for (let i = 0; i < particleCount; i++) {
    const p = document.createElement("div");
    p.className = "particle-dot";
    const size = Math.random() * 4 + 2; // 2px to 6px
    const left = Math.random() * 100;
    const duration = Math.random() * 12 + 10; // 10s to 22s
    const delay = Math.random() * 15;
    const color = colors[Math.floor(Math.random() * colors.length)];
    const opacity = Math.random() * 0.5 + 0.3;

    p.style.width = `${size}px`;
    p.style.height = `${size}px`;
    p.style.left = `${left}%`;
    p.style.backgroundColor = color;
    p.style.boxShadow = `0 0 ${size * 2}px ${color}`;
    p.style.animationDuration = `${duration}s`;
    p.style.animationDelay = `${delay}s`;
    p.style.opacity = `${opacity}`;

    container.appendChild(p);
  }
}

// ================= DYNAMIC TIME GREETING =================

function updateDynamicGreeting() {
  const heading = document.getElementById("hero-greeting-heading");
  const sub = document.getElementById("hero-greeting-sub");
  if (!heading) return;

  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) {
    heading.textContent = "Good morning! ☀️";
    if (sub) sub.textContent = "Your fridge is fresh and ready for breakfast.";
  } else if (hour >= 12 && hour < 18) {
    heading.textContent = "Good afternoon! 👋";
    if (sub) sub.textContent = "Your fridge is looking great today.";
  } else {
    heading.textContent = "Good evening! 🌙";
    if (sub) sub.textContent = "Check out quick recipes to cook dinner tonight.";
  }
}

// ================= ALINA CHARACTER STATE MACHINE =================

function setAlinaState(stateName, durationMs = null) {
  const validStates = [
    "idle", "listening", "thinking", "happy", "excited",
    "concerned", "warning", "angry", "sad", "celebration", "error"
  ];
  const state = validStates.includes(stateName) ? stateName : "idle";
  currentAlinaState = state;

  if (stateResetTimeout) {
    clearTimeout(stateResetTimeout);
    stateResetTimeout = null;
  }

  // 1. Update SVG Class
  if (alinaSvg) {
    alinaSvg.className.baseVal = `alina-svg state-${state} alina-float-rig`;
  }

  // 2. Update Mouth Path Morph
  if (alinaMouthPath && MOUTH_PATHS[state]) {
    alinaMouthPath.setAttribute("d", MOUTH_PATHS[state]);
  }

  // 3. Update Pill Badge
  if (alinaStateDisplay) {
    alinaStateDisplay.textContent = state.toUpperCase();
    if (state === "angry" || state === "error") {
      alinaStateDisplay.style.borderColor = "var(--color-critical)";
      alinaStateDisplay.style.color = "var(--color-critical)";
      alinaStateDisplay.style.boxShadow = "0 0 10px rgba(239, 68, 68, 0.4)";
    } else if (state === "warning" || state === "concerned") {
      alinaStateDisplay.style.borderColor = "var(--color-warning)";
      alinaStateDisplay.style.color = "var(--color-warning)";
      alinaStateDisplay.style.boxShadow = "0 0 10px rgba(245, 158, 11, 0.4)";
    } else if (state === "celebration" || state === "excited") {
      alinaStateDisplay.style.borderColor = "var(--color-pink)";
      alinaStateDisplay.style.color = "var(--color-pink)";
      alinaStateDisplay.style.boxShadow = "0 0 10px rgba(236, 72, 153, 0.4)";
    } else {
      alinaStateDisplay.style.borderColor = "var(--color-cyan)";
      alinaStateDisplay.style.color = "var(--color-cyan)";
      alinaStateDisplay.style.boxShadow = "0 0 10px rgba(34, 211, 238, 0.4)";
    }
  }

  // 4. Update Backdrop Ambient Glow
  if (alinaAmbientBackdrop) {
    alinaAmbientBackdrop.className = "alina-ambient-backdrop";
    if (state === "concerned" || state === "warning") {
      alinaAmbientBackdrop.classList.add("mood-concerned");
    } else if (state === "angry" || state === "error") {
      alinaAmbientBackdrop.classList.add("mood-angry");
    } else if (state === "celebration" || state === "excited") {
      alinaAmbientBackdrop.classList.add("mood-celebration");
    } else if (state === "listening") {
      alinaAmbientBackdrop.classList.add("mood-listening");
    }
  }

  // 5. Update Speech Ribbon
  if (alinaSpeechRibbon && STATE_THOUGHTS[state]) {
    alinaSpeechRibbon.textContent = STATE_THOUGHTS[state];
  }

  // 6. Trigger Celebration Sparks
  if (state === "celebration" || state === "excited") {
    triggerCelebrationParticles();
    showFloatingPointsReward("+10 PTS");
  }

  // 7. Temporary state auto-revert
  if (durationMs) {
    stateResetTimeout = setTimeout(() => {
      evaluateBaselineMood();
    }, durationMs);
  }
}

// Determines character baseline emotion based on actual fridge health
function evaluateBaselineMood() {
  if (lastDoorStatus === "open") {
    setAlinaState("warning");
    return;
  }

  const active = allFoods.filter(f => f.status === "active");
  const critical = active.filter(f => f.days_remaining <= 1 && f.days_remaining >= 0);
  const expired = active.filter(f => f.days_remaining < 0);
  const soon = active.filter(f => f.days_remaining <= 3 && f.days_remaining > 1);

  if (expired.length > 0) {
    setAlinaState("sad");
  } else if (critical.length > 0) {
    setAlinaState("warning");
  } else if (soon.length > 0) {
    setAlinaState("concerned");
  } else {
    setAlinaState("idle");
  }
}

// Floating +10 Points Animation Badge
function showFloatingPointsReward(tagText = "+10 PTS") {
  if (!headerPointsBadge) return;
  const tag = document.createElement("span");
  tag.className = "floating-points-tag";
  tag.textContent = tagText;
  headerPointsBadge.appendChild(tag);
  setTimeout(() => tag.remove(), 1900);
}

// ================= PARTICLE CELEBRATION CANVAS EFFECT =================

function triggerCelebrationParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = canvas.parentElement.offsetWidth;
  canvas.height = canvas.parentElement.offsetHeight;

  const particles = [];
  const colors = ["#22D3EE", "#38BDF8", "#22C55E", "#8B5CF6", "#FEF08A", "#EC4899"];

  for (let i = 0; i < 45; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height / 2,
      vx: (Math.random() - 0.5) * 8,
      vy: (Math.random() - 0.7) * 9,
      size: Math.random() * 5 + 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1,
      decay: Math.random() * 0.02 + 0.015,
    });
  }

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = false;
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.2; // gravity
      p.alpha -= p.decay;

      if (p.alpha > 0) {
        alive = true;
        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    });

    if (alive) {
      requestAnimationFrame(render);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  render();
}

// ================= INITIALIZATION =================

document.addEventListener("DOMContentLoaded", () => {
  initFloatingParticles();
  updateDynamicGreeting();
  setupEventListeners();
  loadAllData();

  // Periodic Telemetry Polling
  setInterval(pollSensors, 2500);
  setInterval(loadEvents, 5000);
});

function setupEventListeners() {
  // Sync button
  document.getElementById("btn-refresh-all").addEventListener("click", loadAllData);

  // Sidebar navigation active state toggle
  document.querySelectorAll(".sidebar-nav-item a").forEach(link => {
    link.addEventListener("click", (e) => {
      document.querySelectorAll(".sidebar-nav-item").forEach(item => item.classList.remove("active"));
      link.closest(".sidebar-nav-item").classList.add("active");
    });
  });

  // Filter buttons
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      const filter = e.target.dataset.filter;
      document.getElementById("inventory-filter").value = filter;
      renderInventory(allFoods);
    });
  });

  // Prompt suggestion chips
  document.querySelectorAll(".suggestion-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      submitAssistantQuery(q);
    });
  });

  // Add Food Modal
  document.getElementById("btn-open-add-modal").addEventListener("click", () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById("add-food-expiry").value = tomorrow.toISOString().split("T")[0];
    modalAddFood.classList.add("active");
  });
  document.getElementById("btn-close-add-modal").addEventListener("click", () => modalAddFood.classList.remove("active"));
  document.getElementById("btn-cancel-add").addEventListener("click", () => modalAddFood.classList.remove("active"));
  document.getElementById("form-add-food").addEventListener("submit", handleAddFoodSubmit);

  // Scan Food Modal
  document.getElementById("btn-open-scan-modal").addEventListener("click", () => {
    modalScanFood.classList.add("active");
  });
  document.getElementById("btn-close-scan-modal").addEventListener("click", () => modalScanFood.classList.remove("active"));
  document.getElementById("btn-cancel-scan").addEventListener("click", () => modalScanFood.classList.remove("active"));
  document.getElementById("btn-trigger-capture").addEventListener("click", handleCameraScan);
  document.getElementById("form-scan-save").addEventListener("submit", handleScanSave);

  // Chat & Voice
  chatForm.addEventListener("submit", handleChatSubmit);
  document.getElementById("btn-mic-chat").addEventListener("click", handleVoiceClick);
  document.getElementById("btn-listen-voice").addEventListener("click", handleVoiceClick);

  // Cook Spotlight actions
  document.getElementById("btn-suggest-recipe").addEventListener("click", () => {
    submitAssistantQuery("What should I cook today?");
  });
  document.getElementById("btn-cook-now").addEventListener("click", () => {
    submitAssistantQuery("What should I cook today?");
  });
  document.getElementById("btn-show-recipes").addEventListener("click", () => {
    submitAssistantQuery("Show alternate recipes for soonest expiring food");
  });

  // Simulation Controls
  document.getElementById("btn-sim-door-open").addEventListener("click", () => {
    setAlinaState("warning");
    simulateSensor({ door: "open" });
    showToast("🚪 Simulated Door Opened! 15s alarm armed.");
  });
  document.getElementById("btn-sim-door-close").addEventListener("click", () => {
    simulateSensor({ door: "closed" });
    showToast("🔒 Simulated Door Closed.");
  });
  document.getElementById("btn-sim-weight-drop").addEventListener("click", handleSimulateWeightDrop);
  document.getElementById("btn-sim-weight-reset").addEventListener("click", () => {
    simulateSensor({ weight: 520 });
    showToast("⚖️ Scale Weight reset to 520g.");
  });
  document.getElementById("btn-test-buzzer").addEventListener("click", () => testActuator("BUZZER_ON"));
  document.getElementById("btn-test-servo").addEventListener("click", () => testActuator("SERVO_OPEN"));

  // Toggle drawer button
  document.getElementById("btn-toggle-demo-sim").addEventListener("click", () => {
    const drawer = document.getElementById("simulation-panel");
    if (drawer) drawer.scrollIntoView({ behavior: "smooth" });
  });

  // Consumption Modal Buttons
  document.getElementById("btn-consumption-yes").addEventListener("click", () => submitConsumptionConfirm(true));
  document.getElementById("btn-consumption-no").addEventListener("click", () => submitConsumptionConfirm(false));
}

// ================= DATA FETCHING =================

async function loadAllData() {
  await Promise.all([
    fetchInventory(),
    pollSensors(),
    fetchSystemStatus(),
    fetchPoints(),
    loadEvents()
  ]);
  evaluateBaselineMood();
}

async function fetchInventory() {
  try {
    const res = await fetch(`${API_BASE}/foods?status=all`);
    if (!res.ok) throw new Error("Failed to load inventory");
    allFoods = await res.json();
    renderInventory(allFoods);
    updateTelemetrySummaries(allFoods);
    updateCookSpotlight(allFoods);
  } catch (err) {
    console.error("fetchInventory error:", err);
  }
}

function updateTelemetrySummaries(foods) {
  const active = foods.filter(f => f.status === "active");
  if (cardFoodCount) cardFoodCount.textContent = `${active.length} Items`;

  const expiringSoon = active.filter(f => f.days_remaining <= 3 && f.days_remaining >= 0);
  if (cardExpiringSub) {
    if (expiringSoon.length > 0) {
      const top = expiringSoon[0];
      cardExpiringSub.textContent = `Alert: ${top.name} (${top.days_remaining}d left)`;
      cardExpiringSub.style.color = "var(--color-warning)";
    } else {
      cardExpiringSub.textContent = "All inventory fresh";
      cardExpiringSub.style.color = "var(--color-success)";
    }
  }
}

function updateCookSpotlight(foods) {
  const active = foods.filter(f => f.status === "active");
  const cookTitle = document.getElementById("cook-title");
  const cookReason = document.getElementById("cook-reason");
  const cookIcon = document.getElementById("cook-spotlight-icon");

  if (!active.length) {
    if (cookTitle) cookTitle.textContent = "Fridge Clear";
    if (cookReason) cookReason.textContent = "Add groceries to receive personalized anti-waste recipe ideas!";
    if (cookIcon) cookIcon.textContent = "🥗";
    return;
  }

  // Sort by earliest expiry
  const sorted = [...active].sort((a, b) => a.days_remaining - b.days_remaining);
  const urgent = sorted[0];

  let dish = `${urgent.name} Special`;
  let icon = getFoodEmoji(urgent.name);

  if (urgent.name.toLowerCase().includes("chicken")) {
    dish = "Savory Chicken Rice";
    icon = "🍗";
  } else if (urgent.name.toLowerCase().includes("milk")) {
    dish = "Golden Milk Pancakes";
    icon = "🥛";
  } else if (urgent.name.toLowerCase().includes("egg")) {
    dish = "Herb Omelette & Toast";
    icon = "🥚";
  } else if (urgent.name.toLowerCase().includes("cheese")) {
    dish = "Crispy Grilled Cheese";
    icon = "🧀";
  } else if (urgent.name.toLowerCase().includes("apple")) {
    dish = "Cinnamon Apple Oatmeal";
    icon = "🍎";
  }

  if (cookTitle) cookTitle.textContent = `Recommended Dish: ${dish}`;
  if (cookIcon) cookIcon.textContent = icon;
  if (cookReason) {
    let daysDesc = urgent.days_remaining === 1 ? "expires tomorrow" : urgent.days_remaining === 0 ? "expires today" : `expires in ${urgent.days_remaining} days`;
    cookReason.textContent = `${urgent.name} ${daysDesc} • HIGH PRIORITY • Prevent food waste and earn +10 points!`;
  }
}

// ================= INVENTORY RENDERING =================

function getFoodEmoji(name) {
  const lower = (name || "").toLowerCase();
  for (const [key, emoji] of Object.entries(FOOD_ICONS)) {
    if (lower.includes(key)) return emoji;
  }
  return "🥗";
}

function renderInventory(foods) {
  const filter = document.getElementById("inventory-filter").value;
  let filtered = foods;
  if (filter === "active") {
    filtered = foods.filter(f => f.status === "active");
  } else if (filter === "consumed") {
    filtered = foods.filter(f => f.status === "consumed");
  }

  // 1. Render Glass Food Cards Grid
  foodCardsGrid.innerHTML = "";
  if (!filtered.length) {
    emptyInventory.style.display = "flex";
  } else {
    emptyInventory.style.display = "none";
  }

  filtered.forEach(item => {
    const card = document.createElement("div");
    card.className = `glass-food-card priority-${item.priority}`;

    let daysText = `${item.days_remaining} days left`;
    if (item.days_remaining < 0) daysText = `Expired (${Math.abs(item.days_remaining)}d ago)`;
    else if (item.days_remaining === 0) daysText = "Expires Today";
    else if (item.days_remaining === 1) daysText = "Expires Tomorrow";

    card.innerHTML = `
      <div class="food-card-top-row">
        <div class="food-info-block">
          <div class="food-card-emoji">${getFoodEmoji(item.name)}</div>
          <div class="food-text-lines">
            <h4>${item.name}</h4>
            <span>${item.category} • ${item.quantity} ${item.unit} ${item.weight_grams ? `(${item.weight_grams}g)` : ''}</span>
          </div>
        </div>
        <span class="priority-badge-tag ${item.priority}">${item.priority}</span>
      </div>
      <div class="food-card-details-row">
        <span>EXP: <strong>${item.expiry_date}</strong></span>
        <span style="font-weight: 700; color: ${item.priority === 'CRITICAL' ? 'var(--color-critical)' : item.priority === 'HIGH' ? 'var(--color-warning)' : 'var(--color-success)'}">
          ${daysText}
        </span>
      </div>
      <div class="card-action-buttons">
        ${item.status === 'active' ? `
          <button class="btn-item-consume" onclick="consumeFoodItem(${item.id})">
            ✨ Consume (+10 PTS)
          </button>
          <button class="btn-item-delete" onclick="deleteFoodItem(${item.id})">
            🗑️ Remove
          </button>
        ` : `
          <span style="font-size: 0.78rem; color: var(--text-dim); font-style: italic; padding: 4px 0;">
            Consumed on ${item.consumed_date || 'previously'}
          </span>
        `}
      </div>
    `;
    foodCardsGrid.appendChild(card);
  });

  // 2. Keep legacy tbody in sync for automated tests
  if (inventoryTbody) {
    inventoryTbody.innerHTML = "";
    filtered.forEach(item => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.name}</td>
        <td>${item.quantity} ${item.unit}</td>
        <td>${item.expiry_date}</td>
        <td>${item.days_remaining}</td>
        <td>${item.priority}</td>
        <td>
          <button onclick="consumeFoodItem(${item.id})">Consume</button>
          <button onclick="deleteFoodItem(${item.id})">Delete</button>
        </td>
      `;
      inventoryTbody.appendChild(tr);
    });
  }
}

// ================= SENSOR & TELEMETRY =================

async function pollSensors() {
  try {
    const res = await fetch(`${API_BASE}/sensors`);
    if (!res.ok) return;
    const data = await res.json();

    // Temperature
    if (data.temperature !== null) {
      cardTemp.textContent = `${data.temperature.toFixed(1)} °C`;
      cardTempSub.textContent = data.temp_eval ? data.temp_eval.message : "Preservation active";
    }

    // Door Status
    const door = (data.door || "closed").toUpperCase();
    cardDoor.textContent = door;
    lastDoorStatus = door.toLowerCase();

    if (door === "OPEN") {
      cardDoor.classList.add("door-warning-pulse");
      const secs = data.door_eval ? data.door_eval.duration_open_seconds : 0;
      cardDoorSub.textContent = `Door Open: ${secs}s ${data.door_eval && data.door_eval.alarm_triggered ? '⚠️ ALARM' : ''}`;
      if (secs > 15) {
        setAlinaState("angry");
      } else {
        setAlinaState("warning");
      }
    } else {
      cardDoor.classList.remove("door-warning-pulse");
      cardDoorSub.textContent = "Magnetic seal active";
    }

    // Weight
    if (data.weight !== null) {
      cardWeight.textContent = `${Math.round(data.weight)} g`;
    }

  } catch (err) {
    console.error("pollSensors error:", err);
  }
}

async function fetchSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) return;
    const s = await res.json();

    const dbEl = document.getElementById("diag-db");
    if (dbEl) dbEl.textContent = s.database;
    const dbBadge = document.getElementById("diag-db-badge");
    if (dbBadge) dbBadge.textContent = s.database === "ONLINE" ? "SQLITE ONLINE" : s.database;

    const camEl = document.getElementById("diag-cam");
    if (camEl) camEl.textContent = s.camera;
    const micEl = document.getElementById("diag-mic");
    if (micEl) micEl.textContent = s.microphone;
    const spkEl = document.getElementById("diag-spk");
    if (spkEl) spkEl.textContent = s.speaker;
    const ocrEl = document.getElementById("diag-ocr");
    if (ocrEl) ocrEl.textContent = s.ocr;
    const espEl = document.getElementById("diag-esp");
    if (espEl) espEl.textContent = s.esp32;
    const aiEl = document.getElementById("diag-ai");
    if (aiEl) aiEl.textContent = s.ai;

    const modeBadge = document.getElementById("system-mode-badge");
    if (modeBadge) {
      modeBadge.textContent = s.demo_mode ? "SIMULATION MODE" : "ESP32 HARDWARE";
    }
  } catch (err) {
    console.error("fetchSystemStatus error:", err);
  }
}

async function fetchPoints() {
  try {
    const res = await fetch(`${API_BASE}/points`);
    if (!res.ok) return;
    const data = await res.json();
    headerPointsBadge.textContent = `🏆 ${data.current_points} PTS`;
  } catch (err) {
    console.error("fetchPoints error:", err);
  }
}

async function loadEvents() {
  try {
    const res = await fetch(`${API_BASE}/events?limit=8`);
    if (!res.ok) return;
    const events = await res.json();
    if (!eventsList) return;
    eventsList.innerHTML = "";
    events.forEach(e => {
      const li = document.createElement("li");
      const timeStr = e.timestamp ? e.timestamp.split("T")[1]?.slice(0, 8) : "";
      li.innerHTML = `<span style="color:var(--color-cyan);">[${timeStr}]</span> <strong>${e.event_type}</strong>: ${e.message}`;
      eventsList.appendChild(li);
    });
  } catch (err) {
    console.error("loadEvents error:", err);
  }
}

// ================= FOOD ACTIONS =================

async function handleAddFoodSubmit(e) {
  e.preventDefault();
  setAlinaState("thinking");

  const payload = {
    name: document.getElementById("add-food-name").value,
    quantity: parseFloat(document.getElementById("add-food-qty").value) || 1.0,
    unit: document.getElementById("add-food-unit").value,
    expiry_date: document.getElementById("add-food-expiry").value,
    category: document.getElementById("add-food-category").value,
    weight_grams: parseFloat(document.getElementById("add-food-weight").value) || null,
  };

  try {
    const res = await fetch(`${API_BASE}/foods`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to store food item");
    modalAddFood.classList.remove("active");
    document.getElementById("form-add-food").reset();

    // Trigger Excited Character State
    setAlinaState("excited", 3500);
    showToast(`✨ Added ${payload.name} to fridge!`);
    await loadAllData();
    triggerAlinaChatResponse(`Got it! I've logged ${payload.name} (${payload.quantity} ${payload.unit}) into your fridge. Freshness tracking is now active!`);
  } catch (err) {
    setAlinaState("error", 3000);
    alert("Error adding food: " + err.message);
  }
}

window.consumeFoodItem = async function(id) {
  setAlinaState("thinking");
  try {
    const res = await fetch(`${API_BASE}/foods/${id}/consume`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to consume item");
    const data = await res.json();

    // Trigger Celebration!
    setAlinaState("celebration", 4500);
    showToast(`🎉 +10 POINTS! Consumed ${data.name} on time!`);
    await loadAllData();
    triggerAlinaChatResponse(`Great job! You used the ${data.name} before it expired. I've awarded you +10 sustainability points! 🎉`);
  } catch (err) {
    setAlinaState("error", 2500);
    alert("Error: " + err.message);
  }
};

window.deleteFoodItem = async function(id) {
  if (!confirm("Remove this grocery item from active inventory?")) return;
  try {
    const res = await fetch(`${API_BASE}/foods/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete item");
    showToast("Grocery item removed.");
    await loadAllData();
  } catch (err) {
    alert("Error: " + err.message);
  }
};

// ================= LASER OCR SCANNING =================

async function handleCameraScan() {
  const spinner = document.getElementById("scan-loading-spinner");
  const idle = document.getElementById("scan-idle-state");
  const statusBox = document.getElementById("scan-status-box");
  const laser = document.getElementById("scanner-laser");

  spinner.style.display = "block";
  idle.style.display = "none";
  statusBox.style.display = "none";
  if (laser) laser.style.display = "block";

  setAlinaState("listening");

  try {
    const res = await fetch(`${API_BASE}/scan`, { method: "POST" });
    const data = await res.json();

    spinner.style.display = "none";
    idle.style.display = "block";
    if (laser) laser.style.display = "none";

    statusBox.style.display = "block";
    statusBox.textContent = data.status_message || "Optical scan complete.";

    if (data.detected_food) {
      document.getElementById("scan-food-name").value = data.detected_food;
      setAlinaState("happy", 3000);
    } else {
      setAlinaState("concerned", 3000);
    }

    if (data.detected_expiry) {
      document.getElementById("scan-food-expiry").value = data.detected_expiry;
    } else {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      document.getElementById("scan-food-expiry").value = tomorrow.toISOString().split("T")[0];
    }
    if (data.default_unit) document.getElementById("scan-food-unit").value = data.default_unit;
    if (data.default_qty) document.getElementById("scan-food-qty").value = data.default_qty;
    document.getElementById("scan-raw-text").value = data.raw_text || "(No text recognized by OCR)";

  } catch (err) {
    spinner.style.display = "none";
    idle.style.display = "block";
    if (laser) laser.style.display = "none";
    statusBox.style.display = "block";
    statusBox.textContent = "Camera or scan error: " + err.message;
    setAlinaState("error", 2500);
  }
}

async function handleScanSave(e) {
  e.preventDefault();
  setAlinaState("thinking");

  const payload = {
    name: document.getElementById("scan-food-name").value,
    quantity: parseFloat(document.getElementById("scan-food-qty").value) || 1.0,
    unit: document.getElementById("scan-food-unit").value || "pieces",
    expiry_date: document.getElementById("scan-food-expiry").value,
    category: "General"
  };

  try {
    const res = await fetch(`${API_BASE}/foods`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to save scanned item");
    modalScanFood.classList.remove("active");

    setAlinaState("excited", 3500);
    showToast(`📦 Scanned item stored: ${payload.name}`);
    await loadAllData();
    triggerAlinaChatResponse(`Optical scan confirmed! I have logged ${payload.name} expiring on ${payload.expiry_date} into your fridge.`);
  } catch (err) {
    setAlinaState("error", 2500);
    alert("Error saving scanned food: " + err.message);
  }
}

// ================= NEURAL CHAT & VOICE WITH ANIMATION SEQUENCE =================

function appendChatMessage(sender, text) {
  const unit = document.createElement("div");
  const isAlina = sender.toLowerCase() === "alina";
  unit.className = `chat-bubble-unit ${isAlina ? 'alina' : 'user'}`;

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  unit.innerHTML = `
    <div class="unit-avatar ${isAlina ? 'alina' : 'user'}">
      ${isAlina ? '❄️' : '👤'}
    </div>
    <div>
      <div class="bubble-text-frame">${text}</div>
      <div class="bubble-timestamp">${isAlina ? 'ALINA' : 'YOU'} • ${timeStr}</div>
    </div>
  `;

  chatHistory.appendChild(unit);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

// ALINA Chat Response Choreography Sequence
function triggerAlinaChatResponse(text, emotion = "happy") {
  // 1. Robot becomes active & turns slightly toward chat
  if (alinaCharacterBox) alinaCharacterBox.classList.add("glance-chat");

  // 2. Set character state & speech ribbon
  setAlinaState(emotion, 4000);

  // 3. Message bubble appears with slide-in animation
  appendChatMessage("alina", text);

  // 4. Return from glance back to center after 1.6s
  setTimeout(() => {
    if (alinaCharacterBox) alinaCharacterBox.classList.remove("glance-chat");
  }, 1600);
}

async function submitAssistantQuery(query) {
  appendChatMessage("user", query);
  setAlinaState("thinking");

  const voiceToggle = document.getElementById("toggle-speech-audio");
  const speakOutput = voiceToggle ? voiceToggle.checked : false;

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, speak_output: speakOutput })
    });

    let data;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      const rawText = await res.text();
      console.error("Non-JSON response from server:", res.status, rawText);
      throw new Error(`Server returned status ${res.status}: ${rawText.slice(0, 80)}`);
    }

    if (!res.ok) {
      const errMsg = data.message || data.error || data.response || `Server returned error (${res.status})`;
      throw new Error(errMsg);
    }

    const replyText = data.message || data.response || "I have processed your request.";
    const emotion = data.alina_state || "happy";

    triggerAlinaChatResponse(replyText, emotion);
    await loadAllData();
  } catch (err) {
    console.error("submitAssistantQuery error:", err);
    setAlinaState("error", 3000);
    appendChatMessage("alina", "Sorry, I had trouble processing that request: " + err.message);
  }
}

function handleChatSubmit(e) {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  submitAssistantQuery(text);
}

function handleVoiceClick() {
  setAlinaState("listening");
  const micBtn = document.getElementById("btn-mic-chat");
  if (micBtn) micBtn.classList.add("is-listening");

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    const rec = new SpeechRec();
    rec.lang = "en-US";
    rec.onresult = (evt) => {
      if (micBtn) micBtn.classList.remove("is-listening");
      const transcript = evt.results[0][0].transcript;
      submitAssistantQuery(transcript);
    };
    rec.onerror = () => {
      if (micBtn) micBtn.classList.remove("is-listening");
      setAlinaState("concerned", 2500);
      triggerAlinaChatResponse("Audio stream lost or unclear. You can type your request in the prompt bar.", "concerned");
    };
    rec.start();
  } else {
    if (micBtn) micBtn.classList.remove("is-listening");
    triggerAlinaChatResponse("Microphone voice interface active. Type your command in the prompt bar!", "happy");
    chatInput.focus();
  }
}

// ================= SIMULATION CONTROLS =================

async function simulateSensor(payload) {
  try {
    const res = await fetch(`${API_BASE}/sensors/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await pollSensors();
    await loadEvents();
  } catch (err) {
    console.error("Simulation error:", err);
  }
}

function handleSimulateWeightDrop() {
  const active = allFoods.filter(f => f.status === "active");
  const candidate = active.find(f => f.name.toLowerCase().includes("chicken")) || active[0];

  if (!candidate) {
    alert("Please add groceries first to test scale reduction detection!");
    return;
  }

  // Simulate scale drop
  simulateSensor({ weight: 120 });
  pendingConsumptionFoodId = candidate.id;
  pendingConsumedWeight = 400;

  setAlinaState("concerned");
  document.getElementById("consumption-prompt-text").textContent =
    `Scale reduction detected (~400g). Did you consume or cook the ${candidate.name}?`;
  modalConsumption.classList.add("active");
}

async function submitConsumptionConfirm(confirmed) {
  modalConsumption.classList.remove("active");
  if (!pendingConsumptionFoodId) return;

  try {
    const res = await fetch(`${API_BASE}/consumption/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        food_id: pendingConsumptionFoodId,
        confirmed: confirmed,
        consumed_weight_grams: pendingConsumedWeight
      })
    });
    const result = await res.json();

    if (confirmed) {
      setAlinaState("celebration", 4500);
      showToast("🎉 +10 Sustainability Points Awarded!");
    } else {
      setAlinaState("idle");
    }

    triggerAlinaChatResponse(result.message, confirmed ? "celebration" : "idle");
    await loadAllData();
  } catch (err) {
    alert("Error confirming consumption: " + err.message);
  } finally {
    pendingConsumptionFoodId = null;
    pendingConsumedWeight = null;
  }
}

async function testActuator(action) {
  try {
    const res = await fetch(`${API_BASE}/actuators/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    showToast(`⚡ Actuator Command Dispatched: ${action}`);
  } catch (err) {
    alert("Actuator error: " + err.message);
  }
}

function showToast(msg) {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}
