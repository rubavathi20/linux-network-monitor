
"use strict";

const $ = (id) => document.getElementById(id);

const API = {
    report: "/api/report",
    refresh: "/api/refresh",
    troubleshoot: "/api/troubleshoot"
};

// Safely find the first available value.
function firstValue(objects, keys, fallback = null) {
    for (const object of objects) {
        if (!object || typeof object !== "object") continue;

        for (const key of keys) {
            const value = object[key];
            if (value !== undefined && value !== null && value !== "") {
                return value;
            }
        }
    }
    return fallback;
}

function numberValue(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
        return value;
    }

    if (typeof value === "string" && value.trim() !== "") {
        const number = Number(value.replace("%", "").trim());
        return Number.isFinite(number) ? number : null;
    }

    return null;
}

function formatPercent(value) {
    const number = numberValue(value);
    return number === null ? "--" : String(Math.round(number * 10) / 10);
}

function formatUptime(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }

    if (
        typeof value === "string" &&
        !/^\d+(\.\d+)?$/.test(value.trim())
    ) {
        return value;
    }

    const seconds = Number(value);

    if (!Number.isFinite(seconds) || seconds < 0) {
        return "--";
    }

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

function formatTimestamp(value) {
    if (!value) return "Not available";

    const date = new Date(value);

    return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleString();
}

// Normalize health values from the API.
function statusOf(value) {
    if (value === true) return "healthy";
    if (value === false || value == null) return "unknown";

    if (typeof value === "object") {
        return statusOf(
            firstValue(
                [value],
                ["status", "state", "result", "healthy", "success"]
            )
        );
    }

    const status = String(value).toLowerCase().trim();

    if (
        [
            "healthy", "ok", "success", "passed", "pass",
            "connected", "reachable", "online", "up",
            "resolved", "available", "true"
        ].includes(status)
    ) {
        return "healthy";
    }

    if (
        ["warning", "degraded", "partial", "unstable"].includes(status)
    ) {
        return "warning";
    }

    if (
        [
            "failed", "failure", "error", "critical", "down",
            "offline", "unhealthy", "unreachable",
            "disconnected", "false", "timeout"
        ].includes(status)
    ) {
        return "critical";
    }

    return "unknown";
}

function statusLabel(status) {
    return {
        healthy: "HEALTHY",
        warning: "WARNING",
        critical: "FAILED",
        unknown: "UNKNOWN"
    }[status] || "UNKNOWN";
}

function setBadge(id, status) {
    const element = $(id);
    if (!element) return;

    element.className = `status-pill status-${status}`;
    element.textContent = statusLabel(status);
}

function setOverall(status, message) {
    const element = $("overallStatus");
    const text = $("overallStatusText");

    if (element) element.className = `overall-status ${status}`;
    if (text) text.textContent = message;
}

function setText(id, value) {
    const element = $(id);
    if (element) element.textContent = String(value);
}

// Display CPU, memory, and disk utilization.
function setMetric(valueId, barId, stateId, value) {
    const number = numberValue(value);
    const valueElement = $(valueId);
    const bar = $(barId);
    const state = $(stateId);

    if (!valueElement || !bar || !state) return null;

    if (number === null) {
        valueElement.textContent = "--";
        bar.style.width = "0%";
        state.textContent = "Unavailable";
        state.className = "";
        return null;
    }

    valueElement.textContent = `${formatPercent(number)}%`;
    bar.style.width = `${Math.max(0, Math.min(100, number))}%`;

    if (number >= 90) {
        state.textContent = "Critical";
        state.className = "state-critical";
    } else if (number >= 75) {
        state.textContent = "High";
        state.className = "state-warning";
    } else {
        state.textContent = "Normal";
        state.className = "";
    }

    return number;
}


function testDescription(test, fallback) {
    if (test == null) return fallback;
    if (typeof test === "string") return test;
    if (typeof test === "boolean") {
        return test ? "Check passed" : "Check failed";
    }

    const status = statusOf(test);

    if (status === "healthy" && test.http_status) {
        return `HTTPS reachable — HTTP ${test.http_status}`;
    }

    return String(
        firstValue(
            [test],
            ["message", "details", "description", "error"],
            fallback
        )
    );
}

// Render connectivity, DNS, and HTTPS results.
function renderHealth(
    test,
    badgeId,
    descriptionId,
    detailId,
    fallback
) {
    const status = statusOf(test);

    setBadge(badgeId, status);
    setText(descriptionId, testDescription(test, fallback));

    let detail = statusLabel(status);

    if (test && typeof test === "object") {
        if (
            Array.isArray(test.resolved_ips) &&
            test.resolved_ips.length > 0
        ) {
            detail = test.resolved_ips.join(", ");
        } else {
            detail = firstValue(
                [test],
                [
                    "host",
                    "hostname",
                    "url",
                    "http_status",
                    "resolver",
                    "address"
                ],
                statusLabel(status)
            );
        }
    }

    setText(detailId, detail);
    return status;
}

// Render TCP listening ports from network.listening_tcp_ports.ports.
function renderPorts(network) {
    const portReport = network?.listening_tcp_ports;

    const ports = Array.isArray(portReport)
        ? portReport
        : Array.isArray(portReport?.ports)
            ? portReport.ports
            : Array.isArray(network?.ports)
                ? network.ports
                : [];

    const table = $("portsTable");
    if (!table) return;

    table.replaceChildren();

    setText(
        "portCount",
        `${ports.length} port${ports.length === 1 ? "" : "s"}`
    );

    if (ports.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.className = "empty-state";
        cell.textContent =
            portReport?.message || "No listening TCP ports found.";

        row.appendChild(cell);
        table.appendChild(row);
        return;
    }

    ports.forEach((portInfo) => {
        const item =
            typeof portInfo === "object" && portInfo !== null
                ? portInfo
                : { port: portInfo };

        const address = item.address ?? item.local_address ?? "--";
        const port = item.port ?? item.port_number ?? "--";
        const service = item.service ?? item.process ?? item.name ?? "Unknown";
        const state = item.state ?? "LISTENING";

        const row = document.createElement("tr");

        const portCell = document.createElement("td");
        portCell.className = "port-number";
        portCell.textContent = String(port);

        const addressCell = document.createElement("td");
        addressCell.textContent = String(address);

        const serviceCell = document.createElement("td");
        serviceCell.className = "port-service";
        serviceCell.textContent = String(service);

        const stateCell = document.createElement("td");
        const badge = document.createElement("span");

        badge.className = "port-state";
        badge.textContent = String(state).toUpperCase();

        stateCell.appendChild(badge);
        row.append(portCell, addressCell, serviceCell, stateCell);
        table.appendChild(row);
    });
}

// Render alerts returned by the monitoring API.
function renderAlerts(alerts) {
    const list = $("alertsList");
    if (!list) return;

    list.replaceChildren();

    if (!Array.isArray(alerts) || alerts.length === 0) {
        const empty = document.createElement("div");

        empty.className = "empty-state";
        empty.textContent =
            "No alerts reported. No configured thresholds were exceeded.";

        list.appendChild(empty);
        setText("alertCount", "0 alerts");
        return;
    }

    setText(
        "alertCount",
        `${alerts.length} alert${alerts.length === 1 ? "" : "s"}`
    );

    alerts.forEach((alert) => {
        const object =
            typeof alert === "object" && alert !== null ? alert : {};

        const message =
            typeof alert === "string"
                ? alert
                : firstValue(
                    [object],
                    ["message", "description", "detail", "name"],
                    "Monitoring alert"
                );

        const severity = String(
            firstValue([object], ["severity", "level", "type"], "warning")
        ).toLowerCase();

        const item = document.createElement("div");

        item.className = `alert-item ${
            severity.includes("critical") || severity.includes("error")
                ? "critical"
                : severity.includes("info")
                    ? "info"
                    : ""
        }`;

        const marker = document.createElement("span");
        marker.className = "alert-marker";

        const copy = document.createElement("div");
        copy.className = "alert-copy";

        const title = document.createElement("strong");
        title.textContent = String(message);

        const detail = document.createElement("p");
        detail.textContent = severity.toUpperCase();

        copy.append(title, detail);
        item.append(marker, copy);
        list.appendChild(item);
    });
}

// Process the report returned by /api/report.
function renderReport(report) {
    if (!report || typeof report !== "object") {
        throw new Error("The monitoring API returned an empty report.");
    }

    const root =
        report.report && typeof report.report === "object"
            ? report.report
            : report.data && typeof report.data === "object"
                ? report.data
                : report;

    const system =
        root.system || root.metrics || root.system_metrics || {};

    const network = root.network || root.network_metrics || {};
    const systemSources = [system, root];

    const cpu = firstValue(systemSources, [
        "cpu_usage_percent", "cpu_percent", "cpu_usage", "cpu"
    ]);

    const memory = firstValue(systemSources, [
        "memory_usage_percent", "memory_percent", "memory_usage", "ram_percent"
    ]);

    const disk = firstValue(systemSources, [
        "disk_usage_percent", "disk_percent", "disk_usage"
    ]);

    const uptime = firstValue(systemSources, [
        "uptime_seconds", "uptime_human", "uptime"
    ]);

    const cpuNumber = setMetric("cpuValue", "cpuBar", "cpuState", cpu);
    const memoryNumber = setMetric(
        "memoryValue", "memoryBar", "memoryState", memory
    );
    const diskNumber = setMetric("diskValue", "diskBar", "diskState", disk);

    setText("uptimeValue", formatUptime(uptime));
    setText("uptimeState", uptime == null ? "Unknown" : "Reported");

    setText(
        "hostname",
        firstValue(systemSources, ["hostname", "host_name"], "Hostname unavailable")
    );

    setText(
        "osValue",
        firstValue(
            systemSources,
            ["operating_system", "os", "os_name", "platform"],
            "Operating system unavailable"
        )
    );

    setText(
        "lastChecked",
        formatTimestamp(
            firstValue(
                [root],
                ["timestamp_utc", "timestamp", "last_updated", "generated_at"]
            )
        )
    );

    const connectivity = network.connectivity;
    const dns = network.dns;
    const https = network.https;

    const connectivityStatus = renderHealth(
        connectivity,
        "connectivityBadge",
        "connectivityStatus",
        "packetLoss",
        "Connectivity result unavailable"
    );

    const loss = firstValue(
        [connectivity || {}, network],
        ["packet_loss_percent", "packet_loss", "packetLoss"]
    );

    setText("packetLoss", loss == null ? "--" : `${loss}%`);

    const dnsStatus = renderHealth(
        dns,
        "dnsBadge",
        "dnsStatus",
        "dnsDetail",
        "DNS result unavailable"
    );

    const httpsStatus = renderHealth(
        https,
        "httpsBadge",
        "httpsStatus",
        "httpsDetail",
        "HTTPS result unavailable"
    );

    renderPorts(network);
    renderAlerts(root.alerts);

    const statuses = [connectivityStatus, dnsStatus, httpsStatus];
    const explicit = statusOf(root.overall_status);

    const resourceValues = [cpuNumber, memoryNumber, diskNumber];

    if (
        explicit === "critical" ||
        statuses.includes("critical") ||
        resourceValues.some((value) => value !== null && value >= 90)
    ) {
        setOverall("critical", "Attention required");
    } else if (
        explicit === "warning" ||
        explicit === "unknown" ||
        statuses.includes("warning") ||
        statuses.includes("unknown") ||
        resourceValues.some((value) => value !== null && value >= 75)
    ) {
        setOverall("warning", "Check system status");
    } else {
        setOverall("healthy", "All reported checks healthy");
    }
}

// Fetch JSON and show meaningful errors when requests fail.
async function requestJSON(url, options = {}) {
    const response = await fetch(url, {
        cache: "no-store",
        ...options,
        headers: {
            Accept: "application/json",
            ...(options.headers || {})
        }
    });

    const responseText = await response.text();
    let data;

    try {
        data = responseText ? JSON.parse(responseText) : {};
    } catch {
        throw new Error(
            `Server returned invalid JSON (HTTP ${response.status}).`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.error || data.message || `HTTP ${response.status}`
        );
    }

    return data;
}

async function loadReport() {
    try {
        const report = await requestJSON(API.report);
        renderReport(report);
    } catch (error) {
        console.error("Report loading failed:", error);
        setOverall("unknown", "Report unavailable");
        setText("lastChecked", error.message);
    }
}

async function refreshMetrics() {
    const button = $("refreshBtn");
    if (!button) return;

    button.disabled = true;
    button.textContent = "Refreshing...";

    try {
        await requestJSON(API.refresh, { method: "POST" });
        await loadReport();
    } catch (error) {
        console.error("Refresh failed:", error);
        alert(`Unable to refresh metrics: ${error.message}`);
    } finally {
        button.disabled = false;
        button.innerHTML =
            '<span class="button-icon">↻</span> Refresh metrics';
    }
}

async function runTroubleshooting() {
    const button = $("troubleshootBtn");
    const output = $("troubleshootResults");
    const state = $("terminalState");

    if (!button || !output || !state) return;

    button.disabled = true;
    button.textContent = "Running diagnostics...";
    state.textContent = "RUNNING";
    output.textContent = "Running network diagnostics...\nPlease wait.";

    try {
        const result = await requestJSON(API.troubleshoot, {
            method: "POST"
        });

        const diagnosticOutput = firstValue(
            [result],
            ["output", "results", "message", "result"]
        );

        output.textContent =
            diagnosticOutput == null
                ? JSON.stringify(result, null, 2)
                : typeof diagnosticOutput === "string"
                    ? diagnosticOutput
                    : JSON.stringify(diagnosticOutput, null, 2);

        state.textContent =
            result.success === false ? "ISSUES FOUND" : "COMPLETED";

        await loadReport();
    } catch (error) {
        console.error("Troubleshooting failed:", error);
        output.textContent = `Troubleshooting failed:\n${error.message}`;
        state.textContent = "ERROR";
    } finally {
        button.disabled = false;
        button.innerHTML =
            '<span class="button-icon">▶</span> Run troubleshooting';
    }
}

// Start only after the dashboard HTML has loaded.
document.addEventListener("DOMContentLoaded", () => {
    const refreshButton = $("refreshBtn");
    const troubleshootButton = $("troubleshootBtn");

    if (refreshButton) {
        refreshButton.addEventListener("click", refreshMetrics);
    }

    if (troubleshootButton) {
        troubleshootButton.addEventListener("click", runTroubleshooting);
    }

    document.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", () => {
            document.querySelectorAll(".nav-link").forEach((item) => {
                item.classList.remove("active");
            });

            link.classList.add("active");
        });
    });

    loadReport();
});

