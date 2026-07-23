const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "IlluQC project";
pptx.subject = "Basic steps required to work with IlluQC";
pptx.title = "Working with IlluQC";
pptx.company = "IlluQC";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "IlluQC_MASTER",
  background: { color: "F5F7FA" },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.12, fill: { color: "00A6A6" }, line: { color: "00A6A6" } } },
    { text: { text: "IlluQC · BASIC WORKFLOW", options: { x: 0.55, y: 7.12, w: 5.4, h: 0.18, fontFace: "Aptos", fontSize: 8, color: "5D6B78", margin: 0 } } },
    { text: { text: "Research software · Validate locally before production use", options: { x: 7.25, y: 7.12, w: 5.5, h: 0.18, fontFace: "Aptos", fontSize: 8, color: "5D6B78", align: "right", margin: 0 } } },
  ],
  slideNumber: { x: 12.82, y: 7.1, color: "5D6B78", fontSize: 8 },
});

const C = {
  navy: "14324A", teal: "008C8C", cyan: "DDF4F3", blue: "3076B5",
  paleBlue: "E8F1FA", orange: "F2994A", paleOrange: "FCE8D5",
  green: "2E8B57", paleGreen: "E1F3E8", red: "C64B4B", paleRed: "F9E3E3",
  ink: "23313D", muted: "5D6B78", white: "FFFFFF", line: "D4DDE5",
};

function addTitle(slide, title, subtitle) {
  slide.addText(title, { x: 0.62, y: 0.42, w: 11.9, h: 0.45, fontSize: 25, bold: true, color: C.navy, margin: 0 });
  if (subtitle) slide.addText(subtitle, { x: 0.64, y: 0.92, w: 11.7, h: 0.3, fontSize: 11.5, color: C.muted, margin: 0 });
}

function addStep(slide, n, title, text, x, y, w, color = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 1.12, rectRadius: 0.08, fill: { color: C.white }, line: { color: C.line, width: 1 } });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.18, y: y + 0.22, w: 0.6, h: 0.6, fill: { color }, line: { color } });
  slide.addText(String(n), { x: x + 0.18, y: y + 0.31, w: 0.6, h: 0.25, fontSize: 15, bold: true, color: C.white, align: "center", margin: 0 });
  slide.addText(title, { x: x + 0.95, y: y + 0.2, w: w - 1.15, h: 0.28, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  slide.addText(text, { x: x + 0.95, y: y + 0.53, w: w - 1.15, h: 0.38, fontSize: 10.5, color: C.muted, breakLine: false, margin: 0 });
}

function addCode(slide, code, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.05, fill: { color: "17232D" }, line: { color: "17232D" } });
  slide.addText(code, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h - 0.3, fontFace: "Courier New", fontSize: 11.5, color: "EAF3F5", margin: 0.02, breakLine: false, valign: "mid" });
}

function addCallout(slide, title, text, x, y, w, h, fill = C.paleOrange, accent = C.orange) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.05, fill: { color: fill }, line: { color: accent, width: 1.2 } });
  slide.addText(title, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.25, fontSize: 12.5, bold: true, color: C.ink, margin: 0 });
  slide.addText(text, { x: x + 0.2, y: y + 0.45, w: w - 0.4, h: h - 0.58, fontSize: 10.5, color: C.ink, margin: 0 });
}

// 1 — Title
{
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.18, h: 7.5, fill: { color: "00B8B8" }, line: { color: "00B8B8" } });
  s.addText("WORKING WITH\nIlluQC", { x: 0.85, y: 1.05, w: 7.5, h: 1.65, fontSize: 38, bold: true, color: C.white, margin: 0, breakLine: false });
  s.addText("Basic steps from raw sequencing data to an interactive QC dashboard", { x: 0.9, y: 2.95, w: 7.6, h: 0.7, fontSize: 20, color: "CFE3EC", margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, { x: 9.0, y: 1.15, w: 3.1, h: 4.65, rectRadius: 0.08, fill: { color: "1E435E", transparency: 5 }, line: { color: "4E7892" } });
  ["Configure", "Prepare data", "Parse", "Load", "Explore", "Back up"].forEach((t, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 9.42, y: 1.53 + i * 0.65, w: 0.38, h: 0.38, fill: { color: i < 4 ? "00B8B8" : "F2994A" }, line: { color: i < 4 ? "00B8B8" : "F2994A" } });
    s.addText(String(i + 1), { x: 9.42, y: 1.61 + i * 0.65, w: 0.38, h: 0.14, fontSize: 8.5, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(t, { x: 10.0, y: 1.55 + i * 0.65, w: 1.65, h: 0.25, fontSize: 14, color: C.white, margin: 0 });
  });
  s.addText("IlluQC", { x: 0.9, y: 6.75, w: 2, h: 0.25, fontSize: 11, bold: true, color: "8EB7C9", margin: 0 });
}

// 2 — Workflow at a glance
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "The workflow at a glance", "Three services transform external files into a browsable QC database");
  const items = [
    ["Raw data", "Illumina folders\nThermo Fisher JSON\nMultiQC statistics", C.paleBlue, C.blue],
    ["Parser", "Normalizes vendor data\ninto stable CSV files", C.cyan, C.teal],
    ["Loader", "Validates headers and\ninserts records safely", C.paleOrange, C.orange],
    ["PostgreSQL", "Stores runs, samples,\nlibraries and metrics", C.paleGreen, C.green],
    ["Dashboard", "Explore runs, protocols,\nsamples and trends", "E8E2F6", "7655A3"],
  ];
  items.forEach((it, i) => {
    const x = 0.55 + i * 2.55;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 2.05, w: 2.05, h: 2.25, rectRadius: 0.06, fill: { color: it[2] }, line: { color: it[3], width: 1.4 } });
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.68, y: 2.34, w: 0.7, h: 0.7, fill: { color: it[3] }, line: { color: it[3] } });
    s.addText(String(i + 1), { x: x + 0.68, y: 2.51, w: 0.7, h: 0.2, fontSize: 14, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(it[0], { x: x + 0.15, y: 3.2, w: 1.75, h: 0.3, fontSize: 16, bold: true, align: "center", color: C.ink, margin: 0 });
    s.addText(it[1], { x: x + 0.18, y: 3.58, w: 1.69, h: 0.52, fontSize: 10.5, align: "center", color: C.muted, margin: 0 });
    if (i < items.length - 1) s.addShape(pptx.ShapeType.chevron, { x: x + 2.12, y: 2.92, w: 0.35, h: 0.45, fill: { color: "A9B7C3" }, line: { color: "A9B7C3" } });
  });
  addCallout(s, "Core principle", "Raw data, processed CSVs, logs, backups and PostgreSQL storage remain outside containers and persist independently.", 1.55, 5.05, 10.25, 0.95, C.paleBlue, C.blue);
}

// 3 — Prerequisites
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "1 · Prepare the workstation", "Confirm the required software and access before configuring IlluQC");
  addStep(s, 1, "Install", "Git · Docker · Docker Compose v2 · Make", 0.7, 1.55, 5.7, C.blue);
  addStep(s, 2, "Check Docker", "The Docker daemon must be running and reachable by your account.", 6.9, 1.55, 5.7, C.teal);
  addStep(s, 3, "Check storage", "You need read access to raw data and write access to processed data, logs, backups and PostgreSQL storage.", 0.7, 3.05, 5.7, C.orange);
  addStep(s, 4, "Protect data", "Use institutional storage, permissions and access controls appropriate for laboratory metadata.", 6.9, 3.05, 5.7, C.green);
  addCode(s, "git --version\ndocker --version\n./scripts/runtime/compose.sh version\nmake --version", 2.65, 4.8, 8.05, 1.28);
}

// 4 — Configure
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "2 · Configure IlluQC", "Create a local environment file and review every external path");
  addCode(s, "cp .env.example .env", 0.75, 1.45, 5.5, 0.78);
  s.addText("Essential values in .env", { x: 0.78, y: 2.62, w: 4.6, h: 0.3, fontSize: 17, bold: true, color: C.ink, margin: 0 });
  const vars = [
    ["POSTGRES_PASSWORD", "Replace the example with a long random secret"],
    ["*_RAW_DATA_DIR", "Point to Illumina and Thermo Fisher inputs"],
    ["PROCESSED_DATA_DIR", "Destination for normalized CSV files"],
    ["POSTGRES_DATA_DIR", "Durable database storage"],
    ["LOCAL_UID / LOCAL_GID", "Match host IDs on Linux"],
  ];
  vars.forEach((v, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 0.83, y: 3.13 + i * 0.55, w: 0.2, h: 0.2, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText(v[0], { x: 1.18, y: 3.05 + i * 0.55, w: 2.35, h: 0.28, fontFace: "Courier New", fontSize: 10.5, bold: true, color: C.navy, margin: 0 });
    s.addText(v[1], { x: 3.45, y: 3.05 + i * 0.55, w: 3.0, h: 0.32, fontSize: 10.5, color: C.muted, margin: 0 });
  });
  addCallout(s, "Never commit .env", "It contains deployment paths and the database password. IlluQC's .gitignore excludes it.", 7.0, 1.45, 5.35, 1.15, C.paleRed, C.red);
  addCallout(s, "Validate interpolation", "Run ./scripts/runtime/compose.sh config --quiet before starting services. Missing required variables fail early.", 7.0, 3.05, 5.35, 1.15, C.paleBlue, C.blue);
  addCallout(s, "Production tip", "Prefer absolute paths and place PostgreSQL data on reliable local or block storage.", 7.0, 4.65, 5.35, 1.15, C.paleGreen, C.green);
}

// 5 — Directories and start
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "3 · Create directories and start services", "IlluQC creates its external working layout, then starts PostgreSQL and Streamlit");
  addCode(s, "make setup-data-dirs\nmake up", 0.75, 1.4, 5.4, 1.2);
  s.addText("Default external layout", { x: 0.8, y: 2.95, w: 4, h: 0.3, fontSize: 17, bold: true, color: C.ink, margin: 0 });
  addCode(s, "../NGS_Data/\n├── raw_data/illumina/\n├── raw_data/thermofisher/\n├── processed/{Runs_Data,Samples_Data}/\n├── logs/{parser,loader,app}/\n├── backups/\n└── postgres_data/", 0.75, 3.38, 5.4, 2.55);
  addStep(s, 1, "PostgreSQL", "Initializes the schema only when postgres_data is empty.", 6.75, 1.4, 5.55, C.blue);
  addStep(s, 2, "Streamlit", "Waits for a healthy database, then serves the dashboard on port 8501.", 6.75, 2.9, 5.55, C.teal);
  addStep(s, 3, "Verify", "Use ./scripts/runtime/compose.sh ps and scripts/runtime/wait_for_database.sh.", 6.75, 4.4, 5.55, C.green);
  s.addText("Open  http://localhost:8501", { x: 7.15, y: 5.95, w: 4.8, h: 0.36, fontSize: 19, bold: true, color: C.teal, align: "center", margin: 0 });
}

// 6 — Reference data
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "4 · Load reference data", "Runs depend on instruments and chemistry; sample metrics also depend on libraries");
  const refs = [
    ["sequencing_instruments.csv", "instruments", "instrument_id · name · model · type · platform"],
    ["sequencing_chemistry.csv", "sequencing_chemistry", "chemistry_id · name · platform"],
    ["library.csv", "library", "library_id · name · version · type"],
  ];
  refs.forEach((r, i) => {
    const y = 1.5 + i * 1.35;
    s.addShape(pptx.ShapeType.roundRect, { x: 0.8, y, w: 7.8, h: 0.98, rectRadius: 0.04, fill: { color: i % 2 ? C.cyan : C.paleBlue }, line: { color: i % 2 ? C.teal : C.blue } });
    s.addText(r[0], { x: 1.05, y: y + 0.18, w: 3.0, h: 0.25, fontFace: "Courier New", fontSize: 12, bold: true, color: C.navy, margin: 0 });
    s.addText("→  " + r[1], { x: 4.1, y: y + 0.18, w: 2.1, h: 0.25, fontSize: 12.5, bold: true, color: C.ink, margin: 0 });
    s.addText(r[2], { x: 1.05, y: y + 0.55, w: 6.95, h: 0.2, fontSize: 9.5, color: C.muted, margin: 0 });
  });
  addCode(s, "# Place files in PROCESSED_DATA_DIR\nilluqc load-lab-data", 9.05, 1.5, 3.55, 1.15);
  addCallout(s, "Check the logs", "Missing reference files are skipped with a warning. Inspect LOG_DIR/loader before continuing.", 9.05, 3.15, 3.55, 1.35, C.paleOrange, C.orange);
  addCallout(s, "Load order matters", "Platform seed data → reference data → runs → metrics → samples.", 9.05, 5.0, 3.55, 1.05, C.paleGreen, C.green);
}

// 7 — Parse runs
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "5 · Parse sequencing runs", "Choose the workflow that matches the instrument source");
  s.addShape(pptx.ShapeType.roundRect, { x: 0.7, y: 1.4, w: 5.95, h: 4.95, rectRadius: 0.06, fill: { color: C.paleBlue }, line: { color: C.blue, width: 1.3 } });
  s.addText("ILLUMINA", { x: 1.05, y: 1.72, w: 2.4, h: 0.35, fontSize: 20, bold: true, color: C.blue, margin: 0 });
  s.addText("Place the run at:\nILLUMINA_RAW_DATA_DIR/RUN_ID", { x: 1.05, y: 2.28, w: 4.8, h: 0.65, fontSize: 13, color: C.ink, margin: 0 });
  addCode(s, "make parse RUN_ID=RUN_ID \\\n  DESCRIPTION=\"Run description\"", 1.0, 3.15, 5.35, 1.1);
  addCode(s, "# All Illumina folders\nilluqc parse-illumina-runs", 1.0, 4.65, 5.35, 0.92);
  s.addShape(pptx.ShapeType.roundRect, { x: 6.9, y: 1.4, w: 5.75, h: 4.95, rectRadius: 0.06, fill: { color: C.paleOrange }, line: { color: C.orange, width: 1.3 } });
  s.addText("THERMO FISHER", { x: 7.25, y: 1.72, w: 3.0, h: 0.35, fontSize: 20, bold: true, color: "C56A1A", margin: 0 });
  s.addText("Place S5 or Genexus JSON below:\nTHERMOFISHER_RAW_DATA_DIR", { x: 7.25, y: 2.28, w: 4.7, h: 0.65, fontSize: 13, color: C.ink, margin: 0 });
  addCode(s, "make parse-thermofisher \\\n  JSON_FILE=serialized_run.json \\\n  MODEL=S5", 7.2, 3.15, 5.1, 1.35);
  addCode(s, "# All supported exports\nmake parse-thermofisher-all MODEL=AUTO", 7.2, 4.9, 5.1, 0.92);
}

// 8 — Load and sample workflow
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "6 · Load runs and optional sample QC", "Run-level loading is simple; sample-level metrics require metadata and library enrichment");
  s.addText("Run-level", { x: 0.8, y: 1.4, w: 2.5, h: 0.35, fontSize: 20, bold: true, color: C.blue, margin: 0 });
  addCode(s, "illuqc load RUN_ID\n\n# Or every parsed run\nilluqc load-runs", 0.8, 1.92, 5.0, 1.65);
  addCallout(s, "Loader behavior", "Validates required columns and skips existing primary keys. It does not update conflicting rows.", 0.8, 4.1, 5.0, 1.3, C.paleBlue, C.blue);
  s.addText("Optional sample-level workflow", { x: 6.35, y: 1.4, w: 4.8, h: 0.35, fontSize: 20, bold: true, color: C.teal, margin: 0 });
  addStep(s, 1, "Validate", "illuqc validate-samples RUN_ID", 6.35, 1.95, 5.9, C.teal);
  addStep(s, 2, "Prepare", "illuqc prepare-samples RUN_ID", 6.35, 3.2, 5.9, C.teal);
  addStep(s, 3, "Load", "illuqc load-samples RUN_ID", 6.35, 4.45, 5.9, C.orange);
  addStep(s, 4, "Or combine", "illuqc ingest-samples RUN_ID", 6.35, 5.7, 5.9, C.green);
}

// 9 — Dashboard
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "7 · Explore QC in the dashboard", "Use the dashboard for descriptive monitoring—not as a substitute for laboratory validation");
  const pages = [
    ["Summary", "Counts, protocol mix, instruments and registration trends"],
    ["Protocols", "Compare runs grouped by protocol description"],
    ["Runs", "Inspect run metadata and sequencing metrics"],
    ["Samples", "Review sample metrics across runs"],
    ["Libraries", "Explore distributions by library"],
    ["Lab Data", "Inspect instruments, chemistry, libraries and metric definitions"],
  ];
  pages.forEach((p, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.75 + col * 6.15, y = 1.48 + row * 1.42;
    s.addShape(pptx.ShapeType.roundRect, { x, y, w: 5.65, h: 1.05, rectRadius: 0.05, fill: { color: i % 2 ? C.cyan : C.white }, line: { color: i % 2 ? C.teal : C.line } });
    s.addText(p[0], { x: x + 0.25, y: y + 0.17, w: 1.5, h: 0.28, fontSize: 15, bold: true, color: C.navy, margin: 0 });
    s.addText(p[1], { x: x + 1.72, y: y + 0.16, w: 3.62, h: 0.52, fontSize: 10.5, color: C.muted, margin: 0 });
  });
  addCallout(s, "Interpretation boundary", "IlluQC does not define universal pass/fail thresholds. Validate parser units and acceptance criteria locally.", 1.45, 5.78, 10.4, 0.85, C.paleRed, C.red);
}

// 10 — Operate safely
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "8 · Operate safely", "Finish each workflow with logs, health checks and a recoverable backup");
  addStep(s, 1, "Check status", "./scripts/runtime/compose.sh ps", 0.75, 1.45, 5.65, C.blue);
  addStep(s, 2, "Review logs", "make logs · LOG_DIR/parser · LOG_DIR/loader", 6.9, 1.45, 5.65, C.teal);
  addStep(s, 3, "Create backup", "make backup", 0.75, 2.95, 5.65, C.green);
  addStep(s, 4, "Test recovery", "Periodically restore into an isolated database and verify row counts.", 6.9, 2.95, 5.65, C.orange);
  addStep(s, 5, "Stop safely", "make down preserves host-mounted PostgreSQL data.", 0.75, 4.45, 5.65, C.blue);
  addStep(s, 6, "Protect access", "Put Streamlit behind authentication/TLS for sensitive deployments.", 6.9, 4.45, 5.65, C.red);
  addCallout(s, "Important", "A backup is not proven until it has been restored and checked. Keep independent copies outside the primary host.", 1.55, 6.0, 10.25, 0.72, C.paleOrange, C.orange);
}

// 11 — Checklist
{
  const s = pptx.addSlide("IlluQC_MASTER");
  addTitle(s, "Complete working checklist", "Use this as the final handoff slide or operating checklist");
  const checks = [
    "Software installed and Docker running",
    ".env created; password and paths reviewed",
    "External directories created",
    "PostgreSQL and Streamlit healthy",
    "Reference tables loaded",
    "Run data parsed into normalized CSVs",
    "Run records and metrics loaded",
    "Optional sample metadata and QC loaded",
    "Dashboard results reviewed against source reports",
    "Logs checked and backup verified",
  ];
  checks.forEach((t, i) => {
    const col = i < 5 ? 0 : 1, row = i % 5;
    const x = 0.9 + col * 6.15, y = 1.38 + row * 0.95;
    s.addShape(pptx.ShapeType.roundRect, { x, y, w: 5.45, h: 0.68, rectRadius: 0.04, fill: { color: C.white }, line: { color: C.line } });
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.18, y: y + 0.17, w: 0.34, h: 0.34, fill: { color: i < 8 ? C.teal : C.orange }, line: { color: i < 8 ? C.teal : C.orange } });
    s.addText("✓", { x: x + 0.18, y: y + 0.22, w: 0.34, h: 0.15, fontSize: 9, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(t, { x: x + 0.67, y: y + 0.19, w: 4.55, h: 0.27, fontSize: 11, color: C.ink, margin: 0 });
  });
  s.addText("Full documentation:  docs/README.md", { x: 3.45, y: 6.38, w: 6.45, h: 0.35, fontFace: "Courier New", fontSize: 14, bold: true, color: C.teal, align: "center", margin: 0 });
}

pptx.writeFile({ fileName: "docs/IlluQC_Basic_Workflow.pptx" });
