// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 Philipp Geisseler / PitNode project
// https://github.com/pitnode/pitnode
// https://www.pitnode.de

// Probe State enum
const ProbeState = {
  OK: 0,
  OPEN: 1,
  SHORT: 2,
  INVALID: 3,
};

// State definition
const state = {
  channels: {},
  bbq: {
    temp: null
  },
  system: {
    unit: "°C",
    wifi: {}
  }
};

// Settings
const baseRangeC = { min: 0, max: 150 };
let userInteracting = false;

const channelsEl = {};  // { ch: { tempEl, targetEl, sliderEl } }


// Open Websocket
const ws = new WebSocket("ws://" + location.host + "/ws");
ws.onopen = () => console.log("WS open");

// Handle Websocket messages
ws.onmessage = e => handleMessage(e.data);

function handleMessage(msg) {
  let parsed;

  try {
    parsed = JSON.parse(msg);
  } catch (e) {
    console.error("Invalid JSON", msg);
    return;
  }

  if (parsed.type !== "update") {
    console.warn("Unknown message type:", parsed.type);
    return;
  }

  if (parsed.data.channels !== undefined) {
    state.channels = parsed.data.channels;
  }

  if (parsed.data.bbq !== undefined) {
    state.bbq = parsed.data.bbq;
  }

  if (parsed.data.system !== undefined) {
    state.system = parsed.data.system;
  }
  
  render();
}

// Render html
function render() {
  renderChannels();
  renderBBQ();
  renderSystem();
}

function renderChannels() {
  const channelsData = state.channels;

  for (const ch in channelsData) {
    
    if (!channelsEl[ch]) {
      createChannel(Number(ch));
    }

    const channelData = channelsData[ch];
    const channelUI = channelsEl[ch];
    if (!channelData) continue;

    const probe_state = channelData.state;
    const temp = channelData.temp;

    console.log(probe_state)
    if (!Number.isFinite(temp)) {
      channelUI.tempEl.innerText = "Probe not connected";
      channelUI.unitEls.forEach(el => el.innerText = "");
      continue;
    }

    channelUI.tempEl.innerText = temp.toFixed(1);
    channelUI.unitEls.forEach(el => el.innerText = " " + state.system.unit);

    const target = channelData.target ?? 0;

    if (!userInteracting) {
      channelUI.targetEl.innerText = target;
      channelUI.sliderEl.value = target;
    }

    const alarm = channelData.alarm ?? false;
    setAlarmActive(ch, alarm);
  }
}

const bbqElements = {
  title: document.querySelector(".bbq-title"),
  temp: document.querySelector(".bbq-temp"),
  unit: document.querySelector(".bbq-unit")
};

function renderBBQ() {
  bbqElements.title.innerText = "BBQ";

  const temp = state.bbq.temp;

  if (!Number.isFinite(temp)) {
    bbqElements.temp.innerText = "Probe not connected";
    if (bbqElements.unit) bbqElements.unit.innerText = "";
    return;
  }

  bbqElements.temp.innerText = temp.toFixed(1);
}

function renderSystem() {
  updateAllUnits();
  updateSliderRanges();
}

function updateAllUnits() {
  document.querySelectorAll(".unit").forEach(el => {
    el.innerText = " " + state.system.unit;
  });
}

function updateSliderRanges() {
  const r = getRange(state.system.unit);

  document.querySelectorAll(".ch-slider").forEach(slider => {
    slider.min = r.min;
    slider.max = r.max;
  });
}

function getRange(unit) {
  if (unit === "°C") return baseRangeC;

  if (unit === "°F") {
    return {
      min: Math.round(baseRangeC.min * 9/5 + 32),
      max: Math.round(baseRangeC.max * 9/5 + 32)
    };
  }

  return baseRangeC;
}

function createChannel(ch) {
  console.log("CREATE CHANNEL:", ch);
  ssid = document.querySelector(".ssid-name")
  const wifi_icon = document.querySelector('.wlan_icon');

  if (state.system.wifi.ssid !== null) {
    ssid.innerText = state.system.wifi.ssid
    wifi_icon.style.color = "limegreen";
  }

  const root = document.getElementById("channels");
  const tpl = document.getElementById("channel-template");

  const clone = tpl.content.cloneNode(true);
  const title  = clone.querySelector(".ch-title");
  const temp   = clone.querySelector(".ch-temp");
  const target = clone.querySelector(".ch-target");
  const slider = clone.querySelector(".ch-slider");
  const alarmBtn = clone.querySelector(".alarm-btn");
  const probe_type = clone.querySelector(".probe-type");
  const probe_param = clone.querySelector(".probe-param");
  const ch_circle = clone.querySelector(".ch-circle");

  //title.style.backgroundColor = getChannelColor(ch);
  ch_circle.style.backgroundColor = getChannelColor(ch);

  const r = getRange(state.system.unit);
  slider.min = r.min;
  slider.max = r.max;
  
  const units = clone.querySelectorAll(".unit");
  
  units.forEach(el => {
    el.innerText = " " + state.system.unit;
  });

  let ch_text = ch + 1;
  title.innerText = "Channel " + ch_text;
  probe_type.innerText = state.channels[ch].probe_type
  console.log("Probe Type", state.channels[ch].probe_type);
  probe_param.innerText = state.channels[ch].probe_model;


  slider.addEventListener("pointerdown", () => userInteracting = true);
  slider.addEventListener("pointerup", () => userInteracting = false);
  slider.addEventListener("input", e => {
    const val = Number(e.target.value);
    target.innerText = val;
    userInteracting = true;
  });

  slider.addEventListener("change", e => {
    const val = Number(e.target.value);
    userInteracting = false;

    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        cmd: "set_target",
        ch: ch,
        value: val
      }));
    }
  });

  alarmBtn.addEventListener("click", () => {
  if (ws.readyState === WebSocket.OPEN) {
      console.log("Confirm clicked for channel:", ch);
      ws.send(JSON.stringify({
      cmd: "confirm_alarm",
      ch: ch
      }));
  }
  });


  root.appendChild(clone);

  channelsEl[ch] = {
    tempEl: temp,
    targetEl: target,
    sliderEl: slider,
    alarmBtn: alarmBtn,
    unitEls: units
  };
}

function getChannelColor(ch) {
  const colors = [
    "#f8e324",
    "#0b5704",
    "#0813a7",
  ];

  return colors[ch % colors.length];
}

function setAlarmActive(ch, active) {
  const btn = channelsEl[ch].alarmBtn;

  if (active) {
    btn.disabled = false;
    btn.classList.add("alarm-active");
  } else {
    btn.disabled = true;
    btn.classList.remove("alarm-active");
  }
}
