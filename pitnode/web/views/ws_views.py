

from pitnode.core.probe import ProbeState

def render_temp(ch, temp, state):
    if not temp:
        return f"""
        <strong id="temp-{ch}" hx-swap-oob="outerHTML">no temp received</strong>
        """
    elif state != ProbeState.OK:
        return f"""
        <strong id="temp-{ch}" hx-swap-oob="outerHTML">{state}</strong>
        """
    else:
        return f"""
        <strong id="temp-{ch}" hx-swap-oob="outerHTML">{temp:.1f}</strong>
        """

def render_unit(unit):
    return f"""
    <span hx-swap-oob="innerHTML:.unit">{unit}</span>
    """

def render_bbq_temp(temp):
    if not temp:
        return f"""
        <strong id="bbq-temp" hx-swap-oob="outerHTML">no temp received</strong>
        """
    else:
        return f"""
        <strong id="bbq-temp" hx-swap-oob="outerHTML">{temp:.1f}</strong>
        """

def render_bbq_type_probe(type):
    return f"""
    <span id="type-bbq-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{type}</span>
    """

def render_ch_probe(ch, type, model):
    return f"""
    <span id="type-ch-{ch}-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{type}</span>
    <span id="model-ch-{ch}-probe" hx-swap-oob="outerHTML" class="badge bg-secondary">{model}</span>
    """

def render_target(ch, target):
    return f"""
    <output id="target-{ch}"
            hx-swap-oob="outerHTML">
        {target}
    </output>
    """

def render_alarm_button(ch, alarm):
    if alarm:
        return f"""
        <button
            id="alarm-{ch}"
            class="btn btn-secondary alarm-btn mt-2 w-100 alarm-active"
            data-ch="{ch}"
            hx-post="/api/confirm-alarm"
            hx-vals='{{"ch":{ch}}}'
            hx-swap-oob="outerHTML">
            Confirm alarm
        </button>
        """
    else:
        return f"""
        <button
            id="alarm-{ch}"
            class="btn btn-secondary alarm-btn mt-2 w-100"
            data-ch="{ch}"
            hx-post="/api/confirm-alarm"
            hx-vals='{{"ch":{ch}}}'
            disabled
            hx-swap-oob="outerHTML">
            Confirm alarm
        </button>
        """

def render_wifi(ssid, rssi):
    return f"""
    <span id="ssid" hx-swap-oob="outerHTML" class="ssid-name m-2">{ssid}</span>
    """

def make_points(values):
    n = len(values)

    if n < 2:
        return ""

    vmin = min(values)
    vmax = max(values)

    # alle Werte gleich
    if vmax == vmin:
        return " ".join(
            f"{i * 100 / (n - 1):.1f},15"
            for i in range(n)
        )

    result = []

    for i, value in enumerate(values):
        x = i * 100 / (n - 1)

        normalized = (value - vmin) / (vmax - vmin)

        y = 28 - normalized * 26

        result.append(f"{x:.1f},{y:.1f}")

    return " ".join(result)

def render_bbq_trend(values):
    points = make_points(values)

    return f"""
    <svg
        id="bbq_trend"
        hx-swap-oob="outerHTML"
        class="trend"
        viewBox="0 0 100 30"
        preserveAspectRatio="none">
        <polyline
            points="{points}"
            fill="none"
            stroke="currentColor"
            stroke-width="2.0"/>
    </svg>
    """