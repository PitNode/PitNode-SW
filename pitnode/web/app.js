let userInteracting = false;
let temps = [];
let targets = [];
let alarms = [];
const channels = {};  // { ch: { tempEl, targetEl, sliderEl } }

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

  title.innerText = "Channel " + ch;

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
  // Presenter-Methode hier eintragen
    presenter.confirm_alarm(ch);
  });

  root.appendChild(clone);

  channels[ch] = {
    tempEl: temp,
    targetEl: target,
    sliderEl: slider,
    alarmBtn: alarmBtn
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
  const t = temps[ch];
  if (typeof t !== "number") return;

  if (!channels[ch]) {
    createChannel(ch);
  }

  const channel = channels[ch];

  channel.tempEl.innerText = t.toFixed(1) + " °C";

  const tt = targets[ch] ?? 0;

  if (!userInteracting) {
    channel.targetEl.innerText = tt;
    channel.sliderEl.value = tt;
  }

  const alarmState = alarms[ch] ?? false;
  setAlarmActive(ch, alarmState);
}


function handleMessage(msg) {
  const data = JSON.parse(msg);

  switch (data.type) {
    case "temp":
      temps[data.ch] = data.value;
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
  }
}