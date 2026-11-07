const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");

const THEME = {
  name: "OLA Fleet",
  headFontFace: "Arial", bodyFontFace: "Calibri",
  colors: { dk1: "111317", lt1: "FFFFFF", dk2: "1E2229", lt2: "F3F5F0",
            accent1: "C6F432", accent2: "FF5A5F", accent3: "FFB400", accent4: "4DD0E1", accent5: "8A93A3", accent6: "3B4A12",
            hlink: "4DD0E1", folHlink: "8A93A3" }
};
const INK = "111317", LIME = "C6F432", RED = "FF5A5F", AMBER = "FFB400", CYAN = "4DD0E1", GREY = "8A93A3", MIST = "F3F5F0";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";           // 10 x 5.625
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "OLA Ride Bookings: July 2024";
pres.author = "Shubhodip";
const C = pres.SchemeColor;

// ---------- layouts
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: INK },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.35, w: 8.6, h: 1.7, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 3.3, w: 8.6, h: 1.0, fontSize: 18, color: C.accent1, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.95, fontSize: 30, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "OLA ride bookings · July 2024", options: { x: 0.5, y: 5.2, w: 5, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSE_DARK", background: { color: INK },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.95, fontSize: 30, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------- helpers
const chartFont = () => ({ catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt" });
function card(slide, x, y, w, h, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: C.background2 }, line: { type: "none" }, rectRadius: 0.12, objectName: name });
}
function stat(slide, x, y, w, big, label, opt = {}) {
  card(slide, x, y, w, opt.h || 1.55, "Card " + label);
  slide.addText(big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.75, fontSize: opt.size || 36, bold: true, color: opt.color || C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "Stat " + label });
  slide.addText(label, { x: x + 0.2, y: y + 0.9, w: w - 0.4, h: (opt.h || 1.55) - 1.0, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Label " + label });
}
function badge(slide, n, x, y, d = 0.5) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "Badge " + n });
  slide.addText(String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Badge num " + n });
}

(async () => {
  // ================= 1. Title
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("Where 38% of OLA's demand slips away", { placeholder: "title" });
  s.addText("July 2024 ride bookings · SQL analysis, gamified dashboard and recommendations\nShubhodip · Data analytics internship project", { placeholder: "body" });
  s.addNotes("Open with the headline: of every 100 rides people tried to book in July, about 38 never happened. This deck shows where they are lost, what it costs, and what to do about it. Everything comes from 103,024 bookings in OLA_DataSet.xlsx, analysed with 31 SQL queries and a Streamlit dashboard.");

  // ================= 2. Exec summary
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Opening" });
  s.addText("The month in four numbers", { placeholder: "title" });
  const xs = [0.5, 2.8, 5.1, 7.4];
  stat(s, xs[0], 1.5, 2.1, "103,024", "bookings from 94,544 customers");
  stat(s, xs[1], 1.5, 2.1, "62.1%", "completed as rides");
  stat(s, xs[2], 1.5, 2.1, "₹35.1M", "earned from completed rides");
  stat(s, xs[3], 1.5, 2.1, "₹21.5M", "in quoted fares lost to failed bookings", { color: C.accent2 });
  s.addText("More than a third of demand never becomes a ride, and the fares at stake equal 61% of what OLA actually earned.", { x: 0.5, y: 3.5, w: 9.0, h: 0.9, fontSize: 20, bold: true, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Takeaway" });
  s.addNotes("Four numbers frame the story. 103,024 bookings, 62.1% completed, 35.1 million rupees earned. The last number is the one that matters: failed bookings carried 21.5 million rupees of quoted fares, which is 61% of what was earned. Revenue here means completed rides only; failed bookings are shown as fares at risk, never as revenue.");

  // ================= 3. Approach
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Opening" });
  s.addText("How the analysis was built", { placeholder: "title" });
  const steps = [
    ["Clean", "Excel to SQLite: 103,024 rows, 24 columns, expected blanks labelled, hour and weekday added."],
    ["Query", "31 SQL queries: KPIs, vehicles, time, zones, cancellations, payments and customers."],
    ["Play", "A gamified Streamlit app turns the findings into challenges, a what-if boss battle and a SQL lab."],
  ];
  steps.forEach((t, i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 1.5, 2.85, 3.2, "Step card " + (i + 1));
    badge(s, i + 1, x + 0.25, 1.75, 0.6);
    s.addText(t[0], { x: x + 0.25, y: 2.5, w: 2.4, h: 0.5, fontSize: 22, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Step title " + (i + 1) });
    s.addText(t[1], { x: x + 0.25, y: 3.05, w: 2.4, h: 1.5, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Step body " + (i + 1) });
  });
  s.addNotes("Three stages. First, clean: the Excel sheet became a SQLite database; blanks for ratings and payment on cancelled rides are expected, so they are labelled not applicable rather than dropped. Second, 31 SQL queries cover every angle. Third, the Streamlit dashboard lets a reader test the findings interactively.");

  // ================= 4. Status
  pres.addSection({ title: "Findings" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Only 62 of every 100 bookings complete", { placeholder: "title" });
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Bookings", labels: ["Completed", "Cancelled by driver", "Cancelled by customer", "Driver not found"], values: [63967, 18434, 10499, 10124] }], {
    x: 0.4, y: 1.35, w: 5.0, h: 3.7, holeSize: 58, chartColors: [LIME, RED, AMBER, GREY], showPercent: true, showValue: false, showLegend: true, legendPos: "b", legendFontSize: 12,
    dataLabelColor: INK, dataLabelFontSize: 12, dataBorder: { pt: 2, color: "FFFFFF" }, ...chartFont() });
  [["17.9%", "cancelled by drivers", RED], ["10.2%", "cancelled by customers", AMBER], ["9.8%", "no driver found", GREY]].forEach((r, i) => {
    const y = 1.5 + i * 1.15;
    s.addShape(pres.shapes.OVAL, { x: 5.8, y: y + 0.12, w: 0.3, h: 0.3, fill: { color: r[2] }, line: { type: "none" }, objectName: "Dot " + r[1] });
    s.addText(r[0], { x: 6.3, y, w: 1.6, h: 0.55, fontSize: 30, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "Pct " + r[1] });
    s.addText(r[1], { x: 6.3, y: y + 0.55, w: 3.2, h: 0.4, fontSize: 14, color: C.text2, margin: 0, isTextBox: true, objectName: "Pct label " + r[1] });
  });
  s.addNotes("Of 103,024 bookings, 63,967 completed. The rest split three ways: drivers cancelled 17.9%, customers cancelled 10.2%, and in 9.8% of cases no driver was found. Driver cancellations alone are 47% of all failures.");

  // ================= 5. Cost of failure
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Failed bookings put ₹21.5M of fares at risk", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Fares at risk (₹M)", labels: ["Cancelled by driver", "Cancelled by customer", "Driver not found"], values: [10.18, 5.77, 5.50] }], {
    x: 0.4, y: 1.4, w: 5.6, h: 3.6, barDir: "col", chartColors: [RED], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 14, dataLabelColor: INK, dataLabelFormatCode: "0.00",
    catAxisLabelFontSize: 12, catAxisLabelColor: INK, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Quoted fares on failed bookings (₹M)", titleFontSize: 14, titleColor: INK, barGapWidthPct: 60, ...chartFont() });
  card(s, 6.3, 1.5, 3.2, 3.2, "Callout card");
  s.addText("61%", { x: 6.5, y: 1.7, w: 2.8, h: 1.1, fontSize: 64, bold: true, color: C.accent2, margin: 0, valign: "middle", isTextBox: true, objectName: "Callout number" });
  s.addText("of the ₹35.08M OLA actually earned is sitting in bookings that fell through. Each +1 point of success rate is worth about 1,030 rides and ₹0.57M a month.", { x: 6.5, y: 2.85, w: 2.8, h: 1.7, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Callout text" });
  s.addNotes("Fares quoted on failed bookings add up to 21.45 million rupees: 10.2 million on driver cancellations, 5.8 on customer cancellations, 5.5 on no driver found. That is an upper bound on lost revenue, equal to 61% of realised revenue. As a rule of thumb, one extra point of success rate is about 1,030 rides, or roughly 0.57 million rupees a month.");

  // ================= 6. Why
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Most cancellations start on the supply side", { placeholder: "title" });
  const optsH = (colors, title) => ({ barDir: "bar", chartColors: colors, showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 11, catAxisLabelColor: INK, catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title, titleFontSize: 14, titleColor: INK, barGapWidthPct: 45, valAxisMaxVal: 45, ...chartFont() });
  s.addChart(pres.charts.BAR, [{ name: "% of driver cancels", labels: ["Personal / car issue", "Customer-related issue", "Customer coughing / sick", "Over permitted riders"], values: [35.5, 29.4, 19.8, 15.3] }],
    { x: 0.4, y: 1.3, w: 4.6, h: 3.0, ...optsH([RED, GREY, GREY, GREY], "Why drivers cancel (% of 18,434)") });
  s.addChart(pres.charts.BAR, [{ name: "% of customer cancels", labels: ["Driver not moving to pickup", "Driver asked to cancel", "Change of plans", "AC not working", "Wrong address"], values: [30.2, 25.4, 19.8, 14.9, 9.6] }],
    { x: 5.0, y: 1.3, w: 4.6, h: 3.0, ...optsH([RED, RED, GREY, RED, GREY], "Why customers cancel (% of 10,499)") });
  s.addText([{ text: "71% of customer cancellations", options: { bold: true } }, { text: " point to the driver or the vehicle: not moving, asking to cancel, or a broken AC." }],
    { x: 0.5, y: 4.4, w: 9.0, h: 0.7, fontSize: 16, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Takeaway" });
  s.addNotes("Drivers' own top reason is personal or car-related issues at 35.5%. On the customer side the top two reasons, driver not moving towards pickup and driver asked to cancel, are driver behaviour, and a further 14.9% say the AC was not working. Together that is about 71% of customer cancellations that are supply-side rather than a change of heart. Red bars are supply-side.");

  // ================= 7. Flat
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("No vehicle, hour or zone is the culprit", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Revenue (₹M)", labels: ["Prime Sedan", "eBike", "Auto", "Prime Plus", "Bike", "Mini", "Prime SUV"], values: [5.22, 5.05, 5.05, 5.02, 4.97, 4.89, 4.88] }], {
    x: 0.4, y: 1.35, w: 5.4, h: 3.7, barDir: "col", chartColors: [INK, GREY, GREY, GREY, GREY, GREY, GREY], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFormatCode: "0.00",
    catAxisLabelFontSize: 11, catAxisLabelColor: INK, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Revenue by vehicle type (₹M)", titleFontSize: 14, titleColor: INK, barGapWidthPct: 50, ...chartFont() });
  [["36.4–39.6%", "failure rate in every hour of the day"], ["3,253–3,385", "bookings per day, every weekday"], ["59.8–64.0%", "success rate across all 50 zones"]].forEach((r, i) => {
    const y = 1.4 + i * 1.2;
    card(s, 6.1, y, 3.4, 1.05, "Flat card " + (i + 1));
    s.addText(r[0], { x: 6.3, y: y + 0.08, w: 3.0, h: 0.5, fontSize: 24, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "Flat num " + (i + 1) });
    s.addText(r[1], { x: 6.3, y: y + 0.58, w: 3.0, h: 0.4, fontSize: 14, color: C.text2, margin: 0, isTextBox: true, objectName: "Flat label " + (i + 1) });
  });
  s.addNotes("This is the honest finding: almost nothing varies. The top vehicle beats the bottom by only 7%. Failure rate stays between 36 and 40 percent in every hour. Weekday volumes look uneven in raw totals only because July 2024 had five Mondays, Tuesdays and Wednesdays; per day they are level. Zones range from 59.8 to 64.0 percent success. The one outlier is Auto, with rides about 10 km against 25 km elsewhere. So the lever is system-wide driver fulfilment, not reallocating by time or place.");

  // ================= 8. Customers & payments
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("One-time riders and cash dominate", { placeholder: "title" });
  stat(s, 0.5, 1.4, 4.2, "91.6%", "of customers booked only once in the month", { h: 1.55, size: 40 });
  stat(s, 0.5, 3.2, 4.2, "20.9%", "of revenue comes from the 4.6% of rides priced at ₹2,000 or more", { h: 1.75, size: 40 });
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Payment", labels: ["Cash", "UPI", "Cards"], values: [54.8, 40.5, 4.8] }], {
    x: 5.0, y: 1.4, w: 4.6, h: 3.6, holeSize: 58, chartColors: [AMBER, CYAN, GREY], showPercent: true, showValue: false, showLegend: true, legendPos: "b", legendFontSize: 12,
    dataLabelColor: INK, dataLabelFontSize: 12, dataBorder: { pt: 2, color: "FFFFFF" }, showTitle: true, title: "How completed rides are paid", titleFontSize: 14, titleColor: INK, ...chartFont() });
  s.addNotes("Two commercial signals. Only 8.4% of customers booked more than once, so retention is the open question. And revenue is top-heavy: 2,927 rides priced at 2,000 rupees or more are 4.6% of rides but 20.9% of revenue. Payments are cash-led at 54.8%, UPI 40.5%, cards under 5%.");

  // ================= 9. Prize
  pres.addSection({ title: "Action" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Action" });
  s.addText("Fixing driver cancellations alone gets to 70%", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Success rate %", labels: ["Today", "Driver cancels −25%", "Driver cancels −50%", "All failures −25%"], values: [62.1, 66.6, 71.0, 71.6] }], {
    x: 0.4, y: 1.35, w: 5.6, h: 3.7, barDir: "col", chartColors: [GREY, LIME, LIME, LIME], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 14, dataLabelColor: INK, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 11, catAxisLabelColor: INK, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 85, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Simulated success rate (%)", titleFontSize: 14, titleColor: INK, barGapWidthPct: 50, ...chartFont() });
  [["−25% driver cancels", "+4,609 rides · +₹2.5M a month"], ["−50% driver cancels", "+9,217 rides · +₹5.1M a month"], ["−25% of all failures", "+9,764 rides · +₹5.4M a month"]].forEach((r, i) => {
    const y = 1.45 + i * 1.15;
    card(s, 6.3, y, 3.2, 1.0, "Scenario card " + (i + 1));
    s.addText(r[0], { x: 6.5, y: y + 0.1, w: 2.8, h: 0.4, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Scenario " + (i + 1) });
    s.addText(r[1], { x: 6.5, y: y + 0.52, w: 2.8, h: 0.4, fontSize: 14, color: C.text2, margin: 0, isTextBox: true, objectName: "Scenario gain " + (i + 1) });
  });
  s.addText("Upper bound: assumes every recovered booking completes at the ₹548 average fare.", { x: 6.3, y: 4.85, w: 3.2, h: 0.3, fontSize: 10, color: C.accent5, margin: 0, isTextBox: true, objectName: "Assumption" });
  s.addNotes("This is the Boss Battle from the dashboard. Cutting driver cancellations by 25% wins back about 4,600 rides, adds 4.5 points of success rate and roughly 2.5 million rupees a month. Halving them takes success to 71%, past a 70% target. These are upper bounds because they assume each recovered booking completes at the average fare of 548 rupees.");

  // ================= 10. Recommendations
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Action" });
  s.addText("Six moves to close the gap", { placeholder: "title" });
  const recs = [
    ["Driver accountability", "Rewards and penalties for cancels; nudge stalled pickups."],
    ["Vehicle readiness", "AC, condition and capacity checks before going online."],
    ["Close the supply gap", "Incentives in Vijayanagar, Langford Town and Hosur Road."],
    ["Cut customer friction", "Live ETA, auto-reassign stalled drivers, confirm addresses."],
    ["Win the second ride", "Second-ride offer; UPI cashback to move cash users."],
    ["Audit pricing", "Fare is unrelated to distance; Auto earns 2.5× more per km."],
  ];
  recs.forEach((r, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.5 + col * 3.05, y = 1.4 + row * 1.9;
    card(s, x, y, 2.85, 1.75, "Rec card " + (i + 1));
    badge(s, i + 1, x + 0.2, y + 0.18, 0.45);
    s.addText(r[0], { x: x + 0.8, y: y + 0.18, w: 1.9, h: 0.45, fontSize: 16, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "Rec title " + (i + 1) });
    s.addText(r[1], { x: x + 0.2, y: y + 0.8, w: 2.5, h: 0.85, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Rec body " + (i + 1) });
  });
  s.addNotes("Moves one to four go straight at the failure leak: driver accountability, vehicle readiness, supply incentives in the three weakest zones, and customer-side friction. Move five tackles retention and cash. Move six is a pricing audit: in this data fare has almost no relationship to distance, and Auto earns about 2.5 times more per kilometre because its rides are shorter.");

  // ================= 11. Dashboard
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Action" });
  s.addText("OLA Fleet Commander: the dashboard", { placeholder: "title" });
  s.addImage({ path: path.join(__dirname, "..", "docs", "dashboard_boss_battle.png"), x: 0.5, y: 1.35, w: 5.4, h: 3.86, altText: "Screenshot of the Boss Battle tab with sliders to cut cancellations and a Dragon HP bar", objectName: "Dashboard screenshot" });
  const feats = [["8 tabs", "KPIs, vehicles, boss battle, time, zones, quiz, SQL lab, trophies."], ["XP and badges", "5 levels and 8 badges earned by answering and exploring."], ["Boss Battle", "Slide cancellation cuts and watch success rate climb to 70%."], ["SQL Lab", "Run the 31 project queries live, read-only."]];
  feats.forEach((f, i) => {
    const y = 1.4 + i * 0.95;
    s.addText(f[0], { x: 6.2, y, w: 3.3, h: 0.35, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Feature " + (i + 1) });
    s.addText(f[1], { x: 6.2, y: y + 0.36, w: 3.3, h: 0.55, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "Feature text " + (i + 1) });
  });
  s.addNotes("The Streamlit app turns the analysis into a game. Readers earn XP by predicting results: the top vehicle, the worst hour, the weakest zone, or by answering a five-question quiz. The Boss Battle is a what-if simulator for cancellation reductions. The SQL Lab runs the same 31 queries from the project file against the live database.");

  // ================= 12. Close
  pres.addSection({ title: "Close" });
  s = pres.addSlide({ masterName: "CLOSE_DARK", sectionTitle: "Close" });
  s.addText("Caveats and next steps", { placeholder: "title" });
  s.addText("Read with care", { x: 0.5, y: 1.5, w: 4.2, h: 0.4, fontSize: 20, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "Caveats heading" });
  s.addText([
    { text: "One month, one city: no trend or seasonality view.", options: { bullet: true, breakLine: true } },
    { text: "Fare and distance are almost uncorrelated (0.002); the data looks simulated, so trust direction over exact values.", options: { bullet: true, breakLine: true } },
    { text: "No driver or vehicle IDs, so no driver-level analysis.", options: { bullet: true } },
  ], { x: 0.5, y: 2.0, w: 4.2, h: 2.9, fontSize: 14, color: C.background1, paraSpaceAfter: 8, margin: 0, valign: "top", isTextBox: true, objectName: "Caveats list" });
  s.addText("Next", { x: 5.3, y: 1.5, w: 4.2, h: 0.4, fontSize: 20, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "Next heading" });
  s.addText([
    { text: "Add driver-level and fleet data to test accountability.", options: { bullet: true, breakLine: true } },
    { text: "Extend to more months for trends and seasonality.", options: { bullet: true, breakLine: true } },
    { text: "Pilot the second-ride offer and measure repeat rate.", options: { bullet: true } },
  ], { x: 5.3, y: 2.0, w: 4.2, h: 2.9, fontSize: 14, color: C.background1, paraSpaceAfter: 8, margin: 0, valign: "top", isTextBox: true, objectName: "Next list" });
  s.addNotes("Close with honesty. One month of data cannot show trends, and the near-zero fare-distance correlation suggests a simulated or anonymised extract, so the direction of the findings is more reliable than exact values. Next steps: richer data, more months, and a pilot for the second-ride offer. Then take questions.");

  const out = path.join(__dirname, "OLA_Ride_Analytics.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
