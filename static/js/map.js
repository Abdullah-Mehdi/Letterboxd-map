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

// Overseas territories / dependencies → parent sovereign alpha-3.
// Keyed by the TopoJSON numeric ID. Territories listed here are visually
// folded into the parent country (same color, parent's name in tooltip,
// parent's film list on click).
//
// Preserved as separate (NOT in this map):
//   HKG (344), MAC (446)  - distinct film industries
//   TWN (158)             - politically separate
//   GRL (304)             - manually preserved as separate
const NUM_TO_PARENT_ALPHA3 = {
    "016":"USA",  // American Samoa
    "060":"GBR",  // Bermuda
    "086":"GBR",  // British Indian Ocean Territory
    "092":"GBR",  // British Virgin Islands
    "136":"GBR",  // Cayman Islands
    "184":"NZL",  // Cook Islands
    "238":"GBR",  // Falkland Islands
    "258":"FRA",  // French Polynesia
    "260":"FRA",  // French Southern Territories
    "316":"USA",  // Guam
    "334":"AUS",  // Heard and McDonald Islands
    "500":"GBR",  // Montserrat
    "533":"NLD",  // Aruba
    "534":"NLD",  // Sint Maarten
    "540":"FRA",  // New Caledonia
    "570":"NZL",  // Niue
    "574":"AUS",  // Norfolk Island
    "580":"USA",  // Northern Mariana Islands
    "612":"GBR",  // Pitcairn Islands
    "630":"USA",  // Puerto Rico
    "652":"FRA",  // Saint Barthélemy
    "654":"GBR",  // Saint Helena
    "660":"GBR",  // Anguilla
    "663":"FRA",  // Saint Martin (French)
    "666":"FRA",  // Saint Pierre and Miquelon
    "796":"GBR",  // Turks and Caicos
    "831":"GBR",  // Guernsey
    "832":"GBR",  // Jersey
    "833":"GBR",  // Isle of Man
    "850":"USA",  // US Virgin Islands
    "876":"FRA",  // Wallis and Futuna
};

// Some TopoJSON features can't be resolved by numeric id alone — for
// example, "Ashmore and Cartier Is." shares id "036" with Australia, and
// "Indian Ocean Ter." (Christmas / Cocos Islands) ships with an empty id.
// These are matched by feature name instead.
const NAME_TO_PARENT_ALPHA3 = {
    "Ashmore and Cartier Is.": "AUS",
    "Indian Ocean Ter.": "AUS",
};

// Display names for parent countries (used when a territory polygon is
// shown/hovered/clicked, so the user sees e.g. "France" rather than
// "French Guiana").
const ALPHA3_DISPLAY_NAME = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "FRA": "France",
    "NLD": "Netherlands",
    "NZL": "New Zealand",
    "AUS": "Australia",
};

// --------------- DOM refs ---------------
const inputSection    = document.getElementById("input-section");
const progressSection = document.getElementById("progress-section");
const progressBarWrap = document.getElementById("progress-bar-wrapper");
const progressBar     = document.getElementById("progress-bar");
const progressText    = document.getElementById("progress-text");
const spinner         = document.getElementById("spinner");
const errorBanner     = document.getElementById("error-banner");
const errorText       = document.getElementById("error-text");
const mapSection      = document.getElementById("map-section");
const mapContainer    = document.getElementById("map-container");

document.getElementById("error-dismiss").addEventListener("click", () => {
    errorBanner.classList.add("hidden");
});

// --------------- File input label ---------------
document.getElementById("file-input").addEventListener("change", e => {
    const name = e.target.files[0]?.name || "Choose watched.csv or export .zip";
    document.getElementById("file-name").textContent = name;
});

// --------------- Form submission ---------------
document.getElementById("upload-form").addEventListener("submit", async e => {
    e.preventDefault();
    const file = document.getElementById("file-input").files[0];
    if (!file) return;
    disableForms();
    showSpinner("Uploading and parsing...");

    try {
        const form = new FormData();
        form.append("file", file);
        const resp = await fetch("/api/upload", {method: "POST", body: form});
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || "Upload failed");
        showProgressBar();
        listenForProgress(data.job_id, data.total_films);
    } catch (err) {
        showError(err.message);
    }
});

// --------------- SSE progress ---------------
let _filmsByCountry = {};
let _avgRatings = {};

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
            _filmsByCountry = msg.films || {};
            _avgRatings = msg.avg_ratings || {};
            renderMap(msg.counts);
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
const tooltip = document.getElementById("tooltip");
const filmPanel = document.getElementById("film-panel");

document.getElementById("panel-close").addEventListener("click", closeFilmPanel);

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

    // Zoomable group
    const g = svg.append("g");

    const zoom = d3.zoom()
        .scaleExtent([1, 8])
        .on("zoom", e => g.attr("transform", e.transform));

    svg.call(zoom);

    const world = await d3.json("/static/data/countries-50m.json");
    const countries = topojson.feature(world, world.objects.countries);

    // Log scale with blue-to-purple palette
    const maxCount = Math.max(1, ...Object.values(countryData));
    const colorScale = d3.scaleSequentialLog(d3.interpolateBuPu)
        .domain([1, Math.max(2, maxCount)]);

    // Lookup helpers. Territories are folded into their parent sovereign
    // country, so a click/hover on e.g. French Guiana resolves to France.
    function getParentAlpha3(d) {
        return NAME_TO_PARENT_ALPHA3[d.properties.name] ||
               NUM_TO_PARENT_ALPHA3[d.id] ||
               null;
    }

    function getResolvedAlpha3(d) {
        return getParentAlpha3(d) || NUM_TO_ALPHA3[d.id] || null;
    }

    function getResolvedName(d) {
        const parent = getParentAlpha3(d);
        if (parent) {
            return ALPHA3_DISPLAY_NAME[parent] || parent;
        }
        return d.properties.name || "Unknown";
    }

    function getCount(d) {
        const alpha3 = getResolvedAlpha3(d);
        return alpha3 ? (countryData[alpha3] || 0) : 0;
    }

    // Draw countries inside zoomable group
    countryPaths = g.selectAll(".country")
        .data(countries.features)
        .join("path")
        .attr("d", path)
        .attr("class", d => getCount(d) > 0 ? "country" : "country no-data")
        .attr("fill", d => {
            const c = getCount(d);
            return c > 0 ? colorScale(c) : null;
        })
        .on("mouseenter", function (event, d) {
            d3.selectAll(".country").style("opacity", 0.4);
            d3.select(this).style("opacity", 1);
            const alpha3 = getResolvedAlpha3(d);
            showTooltip(event, getResolvedName(d), getCount(d), alpha3 ? _avgRatings[alpha3] : undefined);
        })
        .on("mousemove", function (event) {
            positionTooltip(event);
        })
        .on("mouseleave", function () {
            d3.selectAll(".country").style("opacity", null);
            hideTooltip();
        })
        .on("click", function (event, d) {
            const alpha3 = getResolvedAlpha3(d);
            const name = getResolvedName(d);
            const count = getCount(d);
            const films = alpha3 ? (_filmsByCountry[alpha3] || []) : [];
            const avgRating = alpha3 ? _avgRatings[alpha3] : undefined;
            openFilmPanel(name, count, films, avgRating);
        });

    // Circle markers for tiny countries that have data.
    // Skip territories - they should silently inherit the parent country's
    // color from the polygon below (and adding a marker for them would
    // re-introduce the territory clutter we're trying to remove).
    //
    // Use projected polygon area (path.area), not bounding-box area: spread
    // -out Pacific island nations like the Marshall Islands, Kiribati, FSM,
    // Tuvalu and Palau have a huge bbox but a vanishingly small landmass.
    // Path-area correctly catches both compact city-states and scattered
    // archipelagos.
    const minVisibleArea = 40;
    const smallCountries = countries.features.filter(d => {
        if (getParentAlpha3(d)) return false;
        if (getCount(d) === 0) return false;
        return path.area(d) < minVisibleArea;
    });

    g.selectAll(".small-marker")
        .data(smallCountries)
        .join("circle")
        .attr("class", "small-marker")
        .attr("cx", d => {
            const centroid = path.centroid(d);
            return centroid[0];
        })
        .attr("cy", d => {
            const centroid = path.centroid(d);
            return centroid[1];
        })
        .attr("r", 3)
        .attr("fill", d => colorScale(getCount(d)))
        .attr("stroke", "#fff")
        .attr("stroke-width", 0.5)
        .style("cursor", "pointer")
        .on("mouseenter", function (event, d) {
            d3.selectAll(".country").style("opacity", 0.4);
            const alpha3 = getResolvedAlpha3(d);
            showTooltip(event, getResolvedName(d), getCount(d), alpha3 ? _avgRatings[alpha3] : undefined);
        })
        .on("mousemove", function (event) {
            positionTooltip(event);
        })
        .on("mouseleave", function () {
            d3.selectAll(".country").style("opacity", null);
            hideTooltip();
        })
        .on("click", function (event, d) {
            const alpha3 = getResolvedAlpha3(d);
            const name = getResolvedName(d);
            const count = getCount(d);
            const films = alpha3 ? (_filmsByCountry[alpha3] || []) : [];
            const avgRating = alpha3 ? _avgRatings[alpha3] : undefined;
            openFilmPanel(name, count, films, avgRating);
        });

    drawLegend(svg, colorScale, maxCount, width, height);
    buildRanking(countryData, countries);
}

// --------------- Film panel ---------------
function openFilmPanel(name, count, films, avgRating) {
    document.getElementById("panel-country").textContent = name;
    const plural = count === 1 ? "film" : "films";
    let countText = count > 0 ? `${count} ${plural}` : "No films";
    if (avgRating !== undefined) countText += ` · ${avgRating.toFixed(1)}★`;
    document.getElementById("panel-count").textContent = countText;
    const list = document.getElementById("panel-list");
    list.innerHTML = "";
    if (films.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No films watched from this country.";
        li.style.color = "#667";
        list.appendChild(li);
    } else {
        films.forEach(title => {
            const li = document.createElement("li");
            li.textContent = title;
            list.appendChild(li);
        });
    }
    filmPanel.classList.remove("hidden");
    requestAnimationFrame(() => filmPanel.classList.add("visible"));
}

function closeFilmPanel() {
    filmPanel.classList.remove("visible");
    filmPanel.addEventListener("transitionend", () => {
        filmPanel.classList.add("hidden");
    }, {once: true});
}

// --------------- Country ranking ---------------
let _rankingRows = [];
let _rankingSortKey = "count";
let _rankingSortAsc = false;
let _showZeroCountries = false;

function buildRanking(countryData, geoCountries) {
    // Build alpha3 -> display name from real sovereign features only.
    // Skip territory features so we don't add them as separate rows
    // (their counts already fold into the parent in countryData).
    const alpha3ToName = {};
    geoCountries.features.forEach(f => {
        if (NAME_TO_PARENT_ALPHA3[f.properties.name]) return;
        if (NUM_TO_PARENT_ALPHA3[f.id]) return;
        const a3 = NUM_TO_ALPHA3[f.id];
        if (a3 && f.properties.name && !alpha3ToName[a3]) {
            alpha3ToName[a3] = f.properties.name;
        }
    });

    const seen = new Set();
    _rankingRows = [];

    Object.entries(countryData).forEach(([code, count]) => {
        seen.add(code);
        _rankingRows.push({
            code,
            count,
            name: alpha3ToName[code] || code,
            rating: _avgRatings[code] ?? null,
        });
    });

    Object.entries(alpha3ToName).forEach(([code, name]) => {
        if (seen.has(code)) return;
        _rankingRows.push({
            code,
            count: 0,
            name,
            rating: null,
        });
    });

    _rankingSortKey = "count";
    _rankingSortAsc = false;

    const toggle = document.getElementById("show-zero-toggle");
    if (toggle && !toggle._wired) {
        toggle.addEventListener("change", e => {
            _showZeroCountries = e.target.checked;
            _renderRankingRows();
        });
        toggle._wired = true;
    }
    if (toggle) _showZeroCountries = toggle.checked;

    _renderRankingRows();
    _initSortHeaders();
    document.getElementById("ranking-section").classList.remove("hidden");
}

function _renderRankingRows() {
    const filtered = _showZeroCountries
        ? _rankingRows
        : _rankingRows.filter(r => r.count > 0);

    const sorted = filtered.sort((a, b) => {
        let av = a[_rankingSortKey], bv = b[_rankingSortKey];
        if (av === null) av = -Infinity;
        if (bv === null) bv = -Infinity;
        return _rankingSortAsc ? av - bv : bv - av;
    });

    const tbody = document.getElementById("ranking-body");
    tbody.innerHTML = "";

    sorted.forEach((row, i) => {
        const tr = document.createElement("tr");
        if (row.count === 0) tr.classList.add("zero-row");
        const ratingStr = row.rating !== null ? row.rating.toFixed(1) + "★" : "—";
        tr.innerHTML =
            `<td>${i + 1}</td>` +
            `<td>${row.name}</td>` +
            `<td>${row.count}</td>` +
            `<td>${ratingStr}</td>`;
        tr.addEventListener("click", () => {
            const films = _filmsByCountry[row.code] || [];
            openFilmPanel(row.name, row.count, films, row.rating ?? undefined);
        });
        tbody.appendChild(tr);
    });
}

function _initSortHeaders() {
    document.querySelectorAll("#ranking-table th.sortable").forEach(th => {
        th.addEventListener("click", () => {
            const key = th.dataset.sort;
            if (_rankingSortKey === key) {
                _rankingSortAsc = !_rankingSortAsc;
            } else {
                _rankingSortKey = key;
                _rankingSortAsc = false;
            }
            _updateSortArrows();
            _renderRankingRows();
        });
    });
    _updateSortArrows();
}

function _updateSortArrows() {
    document.querySelectorAll("#ranking-table th.sortable").forEach(th => {
        const arrow = th.querySelector(".sort-arrow");
        const key = th.dataset.sort;
        if (key === _rankingSortKey) {
            th.classList.add("active");
            arrow.textContent = _rankingSortAsc ? "▲" : "▼";
        } else {
            th.classList.remove("active");
            arrow.textContent = "";
        }
    });
}

// --------------- Tooltip ---------------
function showTooltip(event, name, count, avgRating) {
    if (count > 0) {
        const plural = count === 1 ? "film" : "films";
        let html =
            `<div class="tt-country">${name}</div>` +
            `<div class="tt-count">${count} ${plural}</div>`;
        if (avgRating !== undefined) {
            html += `<div class="tt-rating">Avg rating: ${avgRating.toFixed(1)}★</div>`;
        }
        tooltip.innerHTML = html;
    } else {
        tooltip.innerHTML =
            `<div class="tt-country">${name}</div>` +
            `<div class="tt-none">No films watched</div>`;
    }
    tooltip.style.opacity = "1";
    positionTooltip(event);
}

function positionTooltip(event) {
    const pad = 14;
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    const rect = tooltip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - pad;
    if (y + rect.height > window.innerHeight) y = event.clientY - rect.height - pad;
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
}

function hideTooltip() {
    tooltip.style.opacity = "0";
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

    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "legend-gradient");

    // Sample the log color scale across the gradient
    const steps = 20;
    const logMin = Math.log(1);
    const logMax = Math.log(Math.max(2, maxCount));
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const val = Math.exp(logMin + t * (logMax - logMin));
        gradient.append("stop")
            .attr("offset", `${t * 100}%`)
            .attr("stop-color", colorScale(val));
    }

    legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .attr("rx", 3)
        .style("fill", "url(#legend-gradient)");

    // Log-spaced tick labels
    const tickValues = buildLogTickValues(maxCount);
    const tickScale = d3.scaleLog()
        .domain([1, Math.max(2, maxCount)])
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

    legend.append("text")
        .attr("x", 0)
        .attr("y", -6)
        .attr("fill", "#9ab")
        .attr("font-size", "11px")
        .text("Films watched");
}

function buildLogTickValues(max) {
    if (max <= 5) return d3.range(1, max + 1);
    const ticks = [1];
    let v = 1;
    while (v * 10 <= max) { v *= 10; ticks.push(v); }
    if (ticks[ticks.length - 1] !== max) ticks.push(max);
    // Fill in mid-points for small ranges
    if (ticks.length <= 2 && max > 10) {
        ticks.splice(1, 0, Math.round(Math.sqrt(max)));
    }
    return ticks;
}

// --------------- Helpers ---------------
function disableForms() {
    document.querySelectorAll("button[type=submit]").forEach(b => b.disabled = true);
}

function enableForms() {
    document.querySelectorAll("button[type=submit]").forEach(b => b.disabled = false);
}

function showSpinner(message) {
    errorBanner.classList.add("hidden");
    progressSection.classList.remove("hidden");
    spinner.classList.remove("hidden");
    progressBarWrap.classList.add("hidden");
    progressText.textContent = message;
}

function showProgressBar() {
    spinner.classList.add("hidden");
    progressBarWrap.classList.remove("hidden");
    progressBar.style.width = "0%";
    progressText.textContent = "Looking up countries on TMDb...";
}

function showError(msg) {
    progressSection.classList.add("hidden");
    mapSection.classList.add("hidden");
    errorText.textContent = msg;
    errorBanner.classList.remove("hidden");
    enableForms();
}
