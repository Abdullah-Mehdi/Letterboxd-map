// --------------- Numeric ISO → alpha-3 lookup ---------------
const NUM_TO_ALPHA3 = {
    "-99":"XKX","004":"AFG","008":"ALB","010":"ATA","012":"DZA","016":"ASM",
    "020":"AND","024":"AGO","028":"ATG","031":"AZE","032":"ARG","036":"AUS",
    "040":"AUT","044":"BHS","048":"BHR","050":"BGD","051":"ARM","052":"BRB",
    "056":"BEL","060":"BMU","064":"BTN","068":"BOL","070":"BIH","072":"BWA",
    "076":"BRA","084":"BLZ","090":"SLB","096":"BRN","100":"BGR","104":"MMR",
    "108":"BDI","112":"BLR","116":"KHM","120":"CMR","124":"CAN","132":"CPV",
    "140":"CAF","144":"LKA","148":"TCD","152":"CHL","156":"CHN","158":"TWN",
    "170":"COL","174":"COM","178":"COG","180":"COD","188":"CRI","191":"HRV",
    "192":"CUB","196":"CYP","203":"CZE","204":"BEN","208":"DNK","212":"DMA",
    "214":"DOM","218":"ECU","222":"SLV","226":"GNQ","231":"ETH","232":"ERI",
    "233":"EST","238":"FLK","242":"FJI","246":"FIN","250":"FRA","260":"ATF",
    "262":"DJI","266":"GAB","268":"GEO","270":"GMB","275":"PSE","276":"DEU",
    "288":"GHA","296":"KIR","300":"GRC","304":"GRL","308":"GRD","320":"GTM",
    "324":"GIN","328":"GUY","332":"HTI","340":"HND","344":"HKG","348":"HUN",
    "352":"ISL","356":"IND","360":"IDN","364":"IRN","368":"IRQ","372":"IRL",
    "376":"ISR","380":"ITA","384":"CIV","388":"JAM","392":"JPN","398":"KAZ",
    "400":"JOR","404":"KEN","408":"PRK","410":"KOR","414":"KWT","417":"KGZ",
    "418":"LAO","422":"LBN","426":"LSO","428":"LVA","430":"LBR","434":"LBY",
    "438":"LIE","440":"LTU","442":"LUX","446":"MAC","450":"MDG","454":"MWI",
    "458":"MYS","462":"MDV","466":"MLI","470":"MLT","478":"MRT","480":"MUS",
    "484":"MEX","492":"MCO","496":"MNG","498":"MDA","499":"MNE","504":"MAR",
    "508":"MOZ","512":"OMN","516":"NAM","520":"NRU","524":"NPL","528":"NLD",
    "540":"NCL","548":"VUT","554":"NZL","558":"NIC","562":"NER","566":"NGA",
    "578":"NOR","583":"FSM","584":"MHL","585":"PLW","586":"PAK","591":"PAN",
    "598":"PNG","600":"PRY","604":"PER","608":"PHL","616":"POL","620":"PRT",
    "624":"GNB","626":"TLS","630":"PRI","634":"QAT","642":"ROU","643":"RUS",
    "646":"RWA","659":"KNA","662":"LCA","670":"VCT","674":"SMR","678":"STP",
    "682":"SAU","686":"SEN","688":"SRB","690":"SYC","694":"SLE","702":"SGP",
    "703":"SVK","704":"VNM","705":"SVN","706":"SOM","710":"ZAF","716":"ZWE",
    "724":"ESP","728":"SSD","729":"SDN","732":"ESH","736":"SDN","740":"SUR",
    "748":"SWZ","752":"SWE","756":"CHE","760":"SYR","762":"TJK","764":"THA",
    "768":"TGO","776":"TON","780":"TTO","784":"ARE","788":"TUN","792":"TUR",
    "795":"TKM","798":"TUV","800":"UGA","804":"UKR","807":"MKD","818":"EGY",
    "826":"GBR","834":"TZA","840":"USA","854":"BFA","858":"URY","860":"UZB",
    "862":"VEN","882":"WSM","887":"YEM","894":"ZMB"
};

// --------------- DOM refs ---------------
const inputSection    = document.getElementById("input-section");
const progressSection = document.getElementById("progress-section");
const progressBar     = document.getElementById("progress-bar");
const progressText    = document.getElementById("progress-text");
const mapSection      = document.getElementById("map-section");
const mapContainer    = document.getElementById("map-container");

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

    // Build color scale
    const maxCount = Math.max(1, ...Object.values(countryData));
    const colorScale = d3.scaleSequential(d3.interpolateGreens)
        .domain([0, maxCount]);

    // Draw countries
    countryPaths = svg.selectAll(".country")
        .data(countries.features)
        .join("path")
        .attr("d", path)
        .attr("class", d => {
            const alpha3 = NUM_TO_ALPHA3[d.id];
            const count = alpha3 ? (countryData[alpha3] || 0) : 0;
            return count > 0 ? "country" : "country no-data";
        })
        .attr("fill", d => {
            const alpha3 = NUM_TO_ALPHA3[d.id];
            const count = alpha3 ? (countryData[alpha3] || 0) : 0;
            return count > 0 ? colorScale(count) : null;
        });

    drawLegend(svg, colorScale, maxCount, width, height);
}

// --------------- Legend ---------------
function drawLegend(svg, colorScale, maxCount, svgWidth, svgHeight) {
    const legendWidth = 220;
    const legendHeight = 12;
    const legendX = svgWidth - legendWidth - 30;
    const legendY = svgHeight - 40;

    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${legendX}, ${legendY})`);

    // Gradient definition
    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "legend-gradient");

    const steps = 10;
    for (let i = 0; i <= steps; i++) {
        gradient.append("stop")
            .attr("offset", `${(i / steps) * 100}%`)
            .attr("stop-color", colorScale((i / steps) * maxCount));
    }

    // Gradient bar
    legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .attr("rx", 3)
        .style("fill", "url(#legend-gradient)");

    // Tick labels
    const tickValues = buildTickValues(maxCount);
    const tickScale = d3.scaleLinear()
        .domain([0, maxCount])
        .range([0, legendWidth]);

    legend.selectAll(".legend-tick")
        .data(tickValues)
        .join("text")
        .attr("class", "legend-tick")
        .attr("x", d => tickScale(d))
        .attr("y", legendHeight + 14)
        .attr("text-anchor", "middle")
        .attr("fill", "#9ab")
        .attr("font-size", "10px")
        .text(d => d);

    // Title
    legend.append("text")
        .attr("x", 0)
        .attr("y", -6)
        .attr("fill", "#9ab")
        .attr("font-size", "11px")
        .text("Films watched");
}

function buildTickValues(max) {
    if (max <= 5) return d3.range(0, max + 1);
    if (max <= 20) return d3.range(0, max + 1, Math.ceil(max / 5));
    return [0, Math.round(max * 0.25), Math.round(max * 0.5), Math.round(max * 0.75), max];
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
