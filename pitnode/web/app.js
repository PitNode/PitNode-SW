// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (c) 2026 Philipp Geisseler / PitNode project
// https://github.com/pitnode/pitnode
// https://www.pitnode.de


// Open Websocket
const ws = new WebSocket("ws://" + location.host + "/ws");
ws.onopen = () => console.log("WS open");

document.addEventListener("change", (e) => {

    if (!e.target.matches(".ch-slider")) {
        return;
    }

    ws.send(JSON.stringify({
        cmd: "set_target",
        ch: Number(e.target.dataset.ch),
        value: Number(e.target.value)
    }));
});

document.addEventListener("click", (e) => {

    if (!e.target.matches(".alarm-btn")) {
        return;
    }

    ws.send(JSON.stringify({
        cmd: "confirm_alarm",
        ch: Number(e.target.dataset.ch)
    }));
});