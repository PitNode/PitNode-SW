# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Philipp Geisseler / PitNode project
# https://github.com/pitnode/pitnode
# https://www.pitnode.de


CH_COLORS = [
    "#f8e324",
    "#0b5704",
    "#0813a7",
]

def render_channels(presenter):
    html = ""
    channels = presenter.get_num_probe_channels()
    unit = presenter.get_unit()

    for ch in range(channels):
        html += render_channel(ch, unit)

    return html

def render_channel(ch, unit):
    if unit == "°C":
        min_val = 0
        max_val = 150
    else:
        min_val = 32
        max_val = 302

    return f"""
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card ch-card h-100 bg-dark bg-gradient text-primary">
            <div class="card-header d-flex align-items-center">
                <span class="ch-circle" style="background-color:{CH_COLORS[ch]}; margin-right: 8px;"></span>
                <span class="ch-title text-primary">
                    Channel {ch+1}
                </span>

                <div class="ms-auto">
                    <span id="type-ch-{ch}-probe" class="badge probe-type bg-secondary">
                        --
                    </span>
                    <span id="model-ch-{ch}-probe" class="badge probe-param bg-secondary">
                        --
                    </span>
                </div>
            </div>

            <div class="card-body text-center">
                <p class="display-5 mb-0">
                    <strong id="temp-{ch}">--</strong>
                    <span class="unit fs-6">--</span>
                </p>

                <div class="mt-3">
                    <div class="mb-2">
                        Target:
                        <output id="target-{ch}">--</output>
                        <span class="unit fs-6">--</span>
                    </div>

                    <input
                        id="slider-{ch}"
                        data-ch="{ch}"
                        type="range"
                        min="{min_val}"
                        max="{max_val}"
                        name="value"
                        hx-post="/api/target"
                        hx-vals='{{"ch":{ch}}}'
                        hx-trigger="change"
                        class="form-range ch-slider">

                    <button
                        id="alarm-{ch}"
                        data-ch="{ch}"
                        hx-post="/api/confirm-alarm"
                        hx-vals='{{"ch":{ch}}}'
                        hx-swap="none"
                        type="button"
                        class="btn btn-secondary alarm-btn mt-2 w-100"
                        disabled>
                            Confirm alarm
                    </button>
                </div>
            </div>
        </div>
    </div>
    """