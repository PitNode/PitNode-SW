// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 Philipp Geisseler / PitNode project
// https://github.com/pitnode/pitnode
// https://www.pitnode.de

const ProbeState = {
  OK: 0,
  NOT_CONNECTED: 1,
  ERROR: 2
};

let userInteracting = false;
let temps = [];
let targets = [];
let alarms = [];
let bbq_temp = null;
let currentUnit = "C";
const channels = {};  // { ch: { tempEl, targetEl, sliderEl } }

const baseRangeC = { min: 0, max: 150 };

const ws = new WebSocket("ws://" + location.host + "/ws");

ws.onopen = () => console.log("WS open");
ws.onmessage = e => handleMessage(e.data);

function createChannel(ch) {
  const root = document.getElementById("channels");
  const tpl = document.getElementById("channel-template");

  const clone = tpl.content.cloneNode(true);

  const title  = clone.querySelector(".ch-title");
  const temp   = clone.querySelector(".ch-temp");
  const target = clone.querySelector(".ch-target");
  const slider = clone.querySelector(".ch-slider");
  const alarmBtn = clone.querySelector(".alarm-btn");

  const r = getRange(currentUnit);
  slider.min = r.min;
  slider.max = r.max;
  
  const units = clone.querySelectorAll(".unit");
  
  units.forEach(el => {
    el.innerText = " " + currentUnit;
  });

  ch_text = ch + 1
  title.innerText = "Channel " + ch_text;

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

  channels[ch] = {
    tempEl: temp,
    targetEl: target,
    sliderEl: slider,
    alarmBtn: alarmBtn,
    unitEls: units
  };
}

function setAlarmActive(ch, active) {
  const btn = channels[ch].alarmBtn;

  if (active) {
    btn.disabled = false;
    btn.classList.add("alarm-active");
  } else {
    btn.disabled = true;
    btn.classList.remove("alarm-active");
  }
}

function updateChannel(ch) {

  if (!channels[ch]) {
    createChannel(ch);
  }

  const channel = channels[ch];
  const t = temps[ch];

  if (!Number.isFinite(t)) {
    channel.tempEl.innerText = "Probe not connected";
    channel.unitEls.forEach(el => el.innerText = "");
    return;
  }

  channel.tempEl.innerText = t.toFixed(1);
  channel.unitEls.forEach(el => el.innerText = " " + currentUnit);

  const tt = targets[ch] ?? 0;

  if (!userInteracting) {
    channel.targetEl.innerText = tt;
    channel.sliderEl.value = tt;
  }

  const alarmState = alarms[ch] ?? false;
  setAlarmActive(ch, alarmState);
}

function updateBBQ() {
  const bbq_title    = document.querySelector(".bbq-title");
  const bbq_temp_lbl = document.querySelector(".bbq-temp");
  const bbq_unit_lbl = document.querySelector(".bbq-unit");

  bbq_title.innerText = "BBQ";

  if (!Number.isFinite(bbq_temp)) {
    bbq_temp_lbl.innerText = "Probe not connected";
    if (bbq_unit_lbl) bbq_unit_lbl.innerText = "";
    return;
  }

  bbq_temp_lbl.innerText = bbq_temp.toFixed(1) + " " + currentUnit;
}

function updateAllUnits() {
  document.querySelectorAll(".unit").forEach(el => {
    el.innerText = " " + currentUnit;
  });
}

function updateSliderRanges() {
  const r = getRange(currentUnit);

  document.querySelectorAll(".ch-slider").forEach(slider => {
    slider.min = r.min;
    slider.max = r.max;
  });
}

function getRange(unit) {
  if (unit === "C") {
    return baseRangeC;
  }

  if (unit === "F") {
    return {
      min: Math.round(baseRangeC.min * 9/5 + 32),
      max: Math.round(baseRangeC.max * 9/5 + 32)
    };
  }

  // Fallback → C
  return baseRangeC;
}

function handleMessage(msg) {
  const data = JSON.parse(msg);

  switch (data.type) {
    case "temp":
      if (data.state !== ProbeState.OK) {
        temps[data.ch] = null;
      } else {
        temps[data.ch] = data.value;
      }
      updateChannel(data.ch);
      break;

    case "target":
      targets[data.ch] = data.value;
      updateChannel(data.ch);
      break;

    case "alarm":
      alarms[data.ch] = data.value;
      updateChannel(data.ch);
      break;

    case "bbq_temp":
      bbq_temp = data.value;
      updateBBQ();
      break;

    case "unit":
      currentUnit = data.value;
      updateAllUnits();
      updateSliderRanges();
      break;
  }
}