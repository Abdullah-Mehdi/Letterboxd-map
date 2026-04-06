// --------------- DOM refs ---------------
const inputSection   = document.getElementById("input-section");
const progressSection = document.getElementById("progress-section");
const progressBar    = document.getElementById("progress-bar");
const progressText   = document.getElementById("progress-text");
const mapSection     = document.getElementById("map-section");
const mapContainer   = document.getElementById("map-container");

// --------------- Tab switching ---------------
document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
    });
});

// --------------- File input label ---------------
document.getElementById("file-input").addEventListener("change", e => {
    const name = e.target.files[0]?.name || "Choose watched.csv or export .zip";
    document.getElementById("file-name").textContent = name;
});

// --------------- Form submissions ---------------
document.getElementById("username-form").addEventListener("submit", async e => {
    e.preventDefault();
    const username = document.getElementById("username-input").value.trim();
    if (!username) return;
    disableForms();
    showProgress();

    try {
        const resp = await fetch("/api/scrape", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username}),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || "Request failed");
        listenForProgress(data.job_id, data.total_films);
    } catch (err) {
        showError(err.message);
    }
});

document.getElementById("upload-form").addEventListener("submit", async e => {
    e.preventDefault();
    const file = document.getElementById("file-input").files[0];
    if (!file) return;
    disableForms();
    showProgress();

    try {
        const form = new FormData();
        form.append("file", file);
        const resp = await fetch("/api/upload", {method: "POST", body: form});
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || "Upload failed");
        listenForProgress(data.job_id, data.total_films);
    } catch (err) {
        showError(err.message);
    }
});

// --------------- SSE progress ---------------
function listenForProgress(jobId, totalFilms) {
    const source = new EventSource(`/api/progress/${jobId}`);

    source.onmessage = event => {
        const msg = JSON.parse(event.data);

        if (msg.type === "progress") {
            const pct = Math.round((msg.current / msg.total) * 100);
            progressBar.style.width = pct + "%";
            progressText.textContent = `${msg.current} / ${msg.total} — ${msg.title}`;
        } else if (msg.type === "done") {
            source.close();
            renderMap(msg.data);
        } else if (msg.type === "error") {
            source.close();
            showError(msg.error);
        }
    };

    source.onerror = () => {
        source.close();
        showError("Lost connection to the server.");
    };
}

// --------------- Map rendering ---------------
let projection, path, svg, countryPaths;

async function renderMap(countryData) {
    progressSection.classList.add("hidden");
    mapSection.classList.remove("hidden");
    mapContainer.innerHTML = "";

    const width = 960;
    const height = 500;

    projection = d3.geoNaturalEarth1()
        .scale(155)
        .translate([width / 2, height / 2]);

    path = d3.geoPath().projection(projection);

    svg = d3.select("#map-container")
        .append("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const world = await d3.json("/static/data/world-110m.json");
    const countries = topojson.feature(world, world.objects.countries);

    countryPaths = svg.selectAll(".country")
        .data(countries.features)
        .join("path")
        .attr("class", "country no-data")
        .attr("d", path);
}

// --------------- Helpers ---------------
function disableForms() {
    document.querySelectorAll("button[type=submit]").forEach(b => b.disabled = true);
}

function enableForms() {
    document.querySelectorAll("button[type=submit]").forEach(b => b.disabled = false);
}

function showProgress() {
    progressSection.classList.remove("hidden");
    progressBar.style.width = "0%";
    progressText.textContent = "Starting...";
}

function showError(msg) {
    progressSection.classList.add("hidden");
    mapSection.classList.add("hidden");
    enableForms();
    alert(msg);
}
