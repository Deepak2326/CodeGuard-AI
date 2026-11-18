import { useEffect, useState } from "react";
import {
  Shield,
  LayoutDashboard,
  ScanLine,
  ChartNoAxesCombined,
  Info,
  ArrowUpRight,
  ArrowRight,
  Database,
  Activity,
  GitBranch,
  Check,
  Trash2,
  Menu,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Scanner from "./Scanner";
import { api, errorMessage } from "./api";
import type { Category, ModelInfo, HistoryData } from "./types";
type Page = "Dashboard" | "Code Scanner" | "Model Performance" | "About";
const nav = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Code Scanner", icon: ScanLine },
  { name: "Model Performance", icon: ChartNoAxesCombined },
  { name: "About", icon: Info },
] as const;
const percent = (v?: number) =>
  v === undefined ? "—" : `${(v * 100).toFixed(1)}%`;
export default function App() {
  const [page, setPage] = useState<Page>("Dashboard");
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [ready, setReady] = useState(false);
  const [history, setHistory] = useState<HistoryData>({
    enabled: false,
    scans: [],
    summary: null,
  });
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const refreshHistory = () => {
    api
      .history()
      .then(setHistory)
      .catch(() => {});
  };
  useEffect(() => {
    Promise.all([api.health(), api.info(), api.categories()])
      .then(([health, model, cats]) => {
        setReady(health.model_ready);
        setInfo(model);
        setCategories(cats);
      })
      .catch((e) => setError(errorMessage(e)));
    refreshHistory();
  }, []);
  function navigate(p: Page) {
    setPage(p);
    setOpen(false);
  }
  return (
    <div className="app-shell">
      <aside className={open ? "sidebar is-open" : "sidebar"}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("Dashboard");
          }}
        >
          <span className="brand-icon">
            <Shield size={23} />
          </span>
          <span>
            CodeGuard<span className="brand-ai">AI</span>
          </span>
        </a>
        <div className="workspace-tag">
          <span className="avatar">CG</span>
          <div>
            Local workspace<small>Research edition</small>
          </div>
          <span className="tiny-label">01</span>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav>
          {nav.map((item) => (
            <button
              key={item.name}
              className={page === item.name ? "nav-item active" : "nav-item"}
              onClick={() => navigate(item.name)}
            >
              <item.icon size={18} />
              {item.name}
              {page === item.name && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="engine-card">
            <div>
              <span className={ready ? "status-dot" : "status-dot offline"} />
              <strong>{ready ? "Model online" : "Model unavailable"}</strong>
            </div>
            <p>Local inference · CPU baseline</p>
            <span className="caption">{info?.version || "Awaiting API"}</span>
          </div>
          <div className="privacy">
            <Shield size={15} /> Your code stays in this deployment
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="flex items-center gap-3">
            <button
              className="mobile-toggle icon-button"
              aria-label="Toggle navigation"
              onClick={() => setOpen(!open)}
            >
              <Menu />
            </button>
            <span className="muted">Workspace</span>
            <span className="slash">/</span>
            <span>{page}</span>
          </div>
          <span className="chip">
            <span className={ready ? "status-dot" : "status-dot offline"} />
            {ready ? "System ready" : "Setup required"}
          </span>
        </header>
        <main>
          {error && (
            <div role="alert" className="notice error">
              {error}{" "}
              <button
                className="text-button"
                onClick={() => window.location.reload()}
              >
                Retry connection
              </button>
            </div>
          )}
          {page === "Code Scanner" ? (
            <Scanner
              languages={info?.supported_languages || ["c", "cpp", "java"]}
              onScan={refreshHistory}
            />
          ) : page === "Model Performance" ? (
            <Performance info={info} />
          ) : page === "About" ? (
            <About info={info} />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">
                    SECURE CODE STARTS WITH A CLOSER LOOK
                  </p>
                  <h1>Your code. A clearer perspective.</h1>
                  <p className="muted">
                    Machine learning insights for more informed security
                    reviews.
                  </p>
                </div>
                <span className="chip subtle">RESEARCH BASELINE v1.0</span>
              </div>
              <section className="hero">
                <div>
                  <span className="hero-label">
                    <span className="status-dot" /> INTELLIGENCE FOR YOUR NEXT
                    REVIEW
                  </span>
                  <h2>
                    Find the risk.
                    <br />
                    <span>Understand the fix.</span>
                  </h2>
                  <p>
                    Analyze source code for four vulnerability families.
                    <br />
                    Get a model estimate, clear context, and practical next
                    steps.
                  </p>
                  <button
                    className="primary"
                    onClick={() => navigate("Code Scanner")}
                  >
                    Start a new scan
                    <ArrowRight size={17} />
                  </button>
                  <div className="hero-tags">
                    <span>
                      <Check size={13} /> Real ML inference
                    </span>
                    <span>
                      <Check size={13} /> No code execution
                    </span>
                  </div>
                </div>
                <div className="hero-visual" aria-hidden="true">
                  <div className="orbit orbit-outer" />
                  <div className="orbit orbit-inner" />
                  <div className="shield-center">
                    <Shield size={66} strokeWidth={1.2} />
                    <Check className="shield-check" size={24} />
                  </div>
                  <span className="orbit-label label-one">{"{ }"} source</span>
                  <span className="orbit-label label-two">
                    <Activity size={15} /> inference
                  </span>
                  <span className="orbit-label label-three">
                    <Check size={14} /> insight
                  </span>
                </div>
              </section>
              <div className="section-title">
                <h2>Measured, not assumed.</h2>
                <button
                  className="text-button"
                  onClick={() => navigate("Model Performance")}
                >
                  Explore evaluation
                  <ArrowUpRight size={15} />
                </button>
              </div>
              <div className="stats-grid">
                <Stat
                  label="Test macro F1"
                  value={percent(info?.evaluation.macro_f1)}
                  note="Equal weight for every class"
                />
                <Stat
                  label="Test accuracy"
                  value={percent(info?.evaluation.accuracy)}
                  note="Grouped held-out Juliet examples"
                />
                <Stat
                  label="Curated functions"
                  value={info?.dataset.samples.toLocaleString() || "—"}
                  note="Deduplicated, labeled source code"
                />
                <Stat
                  label="Supported languages"
                  value={info?.supported_languages.length.toString() || "—"}
                  note="C · C++ · Java"
                />
              </div>
              <div className="dashboard-bottom">
                <section>
                  <div className="section-title">
                    <h2>What CodeGuard looks for</h2>
                    <span className="muted text-xs">
                      4 vulnerability families + safe class
                    </span>
                  </div>
                  <div className="category-grid">
                    {categories
                      .filter((c) => c.id !== 4)
                      .map((c, i) => (
                        <div className="category-card" key={c.id}>
                          <div className="flex justify-between items-center">
                            <span className={`category-icon color-${i}`}>
                              <CodeGlyph index={i} />
                            </span>
                            <span className="caption">{c.cwe[0]}</span>
                          </div>
                          <h3>{c.name}</h3>
                          <p>{c.description}</p>
                        </div>
                      ))}
                  </div>
                </section>
                <section className="panel model-card">
                  <div className="panel-heading">
                    <h2>Behind the analysis</h2>
                    <GitBranch size={17} />
                  </div>
                  <div className="model-content">
                    <span className="tiny-label cyan">TRAINED BASELINE</span>
                    <h3>{info?.name || "Model information unavailable"}</h3>
                    <p>
                      Character n-grams capture code patterns. A calibrated
                      classifier estimates the most likely category.
                    </p>
                    <div className="model-row">
                      <span>Dataset</span>
                      <strong>NIST Juliet 1.3</strong>
                    </div>
                    <div className="model-row">
                      <span>Inference</span>
                      <strong>Local · CPU</strong>
                    </div>
                    <div className="model-row">
                      <span>Prediction scope</span>
                      <strong>Single function</strong>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => navigate("About")}
                    >
                      Understand the limitations
                      <ArrowUpRight size={15} />
                    </button>
                  </div>
                </section>
              </div>
              {history.enabled && (
                <section className="panel history">
                  <div className="panel-heading">
                    <h2>Recent scans</h2>
                    <span className="caption">
                      User activity · latest 100 · not evaluation data
                    </span>
                  </div>
                  <div className="history-stats">
                    {history.summary?.total ?? 0} total scans ·{" "}
                    {history.summary?.vulnerable ?? 0} predicted vulnerable ·{" "}
                    {history.summary?.safe ?? 0} predicted safe ·{" "}
                    {history.summary?.uncertain ?? 0} uncertain
                  </div>
                  {!!history.summary?.total && (
                    <div style={{ height: 220 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[
                            ...categories.map((c) => ({
                              name: c.name.replace(
                                "Cross-Site Scripting",
                                "XSS",
                              ),
                              count: history.summary?.categories[c.id] ?? 0,
                            })),
                            {
                              name: "Uncertain",
                              count: history.summary.uncertain,
                            },
                          ]}
                          margin={{ left: 10, right: 20, bottom: 10 }}
                        >
                          <XAxis
                            dataKey="name"
                            tick={{ fill: "#93a7bf", fontSize: 10 }}
                          />
                          <YAxis
                            allowDecimals={false}
                            tick={{ fill: "#93a7bf", fontSize: 10 }}
                          />
                          <Tooltip
                            contentStyle={{
                              background: "#151e2e",
                              border: "1px solid #2c3b50",
                            }}
                          />
                          <Bar
                            dataKey="count"
                            fill="#29b7c4"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                  {history.scans.length === 0 ? (
                    <p className="muted">No scans saved yet.</p>
                  ) : (
                    history.scans.map((scan) => (
                      <div className="history-row" key={scan.id}>
                        <span>
                          {scan.predicted_category}
                          <small>
                            {new Date(scan.created_at).toLocaleString()} ·{" "}
                            {scan.language}
                          </small>
                        </span>
                        <span>{percent(scan.confidence)}</span>
                        <button
                          className="icon-button"
                          aria-label={`Delete scan ${scan.id}`}
                          onClick={() =>
                            api
                              .deleteScan(scan.id)
                              .then(refreshHistory)
                              .catch((e) => setError(errorMessage(e)))
                          }
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))
                  )}
                </section>
              )}
            </>
          )}
          <footer>
            CodeGuard AI{" "}
            <span>Built for review. Never a guarantee of security.</span>
            <span>LOCAL / RESEARCH EDITION</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
function CodeGlyph({ index }: { index: number }) {
  return index === 0 ? (
    <Database size={20} />
  ) : index === 1 ? (
    <ScanLine size={20} />
  ) : index === 2 ? (
    <CodeIcon />
  ) : (
    <Activity size={20} />
  );
}
function CodeIcon() {
  return (
    <span style={{ fontFamily: "monospace", fontSize: 20 }}>&lt;/&gt;</span>
  );
}
function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}
function Performance({ info }: { info: ModelInfo | null }) {
  if (!info)
    return (
      <p className="notice">
        Evaluation unavailable until a trained model is loaded.
      </p>
    );
  const m = info.evaluation;
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">MODEL / EVALUATION</p>
          <h1>Performance, with context.</h1>
          <p className="muted">
            Saved results from the grouped held-out test split. {info.name}.
          </p>
        </div>
      </div>
      <div className="stats-grid">
        <Stat
          label="Accuracy"
          value={percent(m.accuracy)}
          note="All held-out predictions"
        />
        <Stat
          label="Macro precision"
          value={percent(m.macro_precision)}
          note="Class-balanced precision"
        />
        <Stat
          label="Macro recall"
          value={percent(m.macro_recall)}
          note="Class-balanced detection rate"
        />
        <Stat
          label="Macro F1"
          value={percent(m.macro_f1)}
          note={`Weighted F1: ${percent(m.weighted_f1)}`}
        />
      </div>
      <div className="performance-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Confusion matrix</h2>
            <span className="caption">Actual rows / predicted columns</span>
          </div>
          <div className="table-scroll">
            <table className="matrix">
              <thead>
                <tr>
                  <th>Actual ↓</th>
                  {info.categories.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {m.confusion_matrix.map((row, i) => (
                  <tr key={i}>
                    <th>{info.categories[i]}</th>
                    {row.map((v, j) => (
                      <td
                        key={j}
                        style={{
                          background: `rgba(37, 166, 173, ${0.04 + (0.75 * v) / Math.max(1, ...m.confusion_matrix.flat())})`,
                        }}
                      >
                        {v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Prepared dataset</h2>
            <span className="caption">All splits</span>
          </div>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={info.categories.map((name, id) => ({
                  name: name.replace("Cross-Site Scripting", "XSS"),
                  count: info.dataset.class_distribution[id] || 0,
                }))}
                layout="vertical"
                margin={{ left: 8, right: 25 }}
              >
                <XAxis type="number" tick={{ fill: "#8995ab", fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={115}
                  tick={{ fill: "#aab6c9", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    background: "#151e2e",
                    border: "1px solid #2c3b50",
                  }}
                />
                <Bar dataKey="count" fill="#29b7c4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Per-class report</h2>
          <span className="caption">Test data only</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1</th>
                <th>Support</th>
              </tr>
            </thead>
            <tbody>
              {info.categories.map((c) => {
                const r = m.classification_report[c];
                return (
                  <tr key={c}>
                    <td>{c}</td>
                    <td>{percent(r.precision)}</td>
                    <td>{percent(r.recall)}</td>
                    <td>{percent(r["f1-score"])}</td>
                    <td>{r.support}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <div className="notice">
        <strong>How to read these results</strong>
        <p>
          Macro F1 gives each class equal weight. Per-class recall reveals
          missed vulnerabilities that overall accuracy can hide. These results
          measure synthetic Juliet functions, not real-world detection
          reliability.
        </p>
        <p>
          Splits:{" "}
          {Object.entries(info.split_sizes)
            .map(([name, count]) => `${name}: ${count}`)
            .join(" · ")}
          . Related families and exact duplicates do not cross splits.
        </p>
      </div>
    </>
  );
}
function About({ info }: { info: ModelInfo | null }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ABOUT / CODEGUARD AI</p>
          <h1>Evidence before confidence.</h1>
          <p className="muted">
            An academic machine learning project for source code security
            review.
          </p>
        </div>
      </div>
      <div className="about-grid">
        <section className="panel prose">
          <h2>From code to insight</h2>
          <p>
            CodeGuard normalizes source code and represents it with TF-IDF
            character n-grams. Logistic regression and a linear SVM are compared
            on a validation split. The selected classifier is calibrated
            separately before final test evaluation.
          </p>
          <p>
            Inference returns five class probability estimates. Low confidence,
            limited context, and unfamiliar features can trigger manual review.
            Exact vulnerable lines are not inferred from a function-level
            prediction.
          </p>
          <h2>Data provenance</h2>
          <p>
            Training uses public-domain NIST Juliet 1.3 C/C++ and Java examples.
            Only baseline flow-01 functions are included. Good and bad functions
            provide explicit target-weakness labels. This release evaluates C
            memory and integer issues, C++ memory issues, and Java SQL injection
            and XSS.
          </p>
          <p>
            <a
              href="https://samate.nist.gov/SARD/test-suites/112"
              target="_blank"
              rel="noreferrer"
            >
              C/C++ source ↗
            </a>{" "}
            ·{" "}
            <a
              href="https://samate.nist.gov/SARD/test-suites/111"
              target="_blank"
              rel="noreferrer"
            >
              Java source ↗
            </a>
          </p>
          <h2>Technology</h2>
          <p>
            React · Vite · Tailwind CSS · Monaco · Recharts · FastAPI ·
            scikit-learn · NumPy · Pandas · optional SQLite history.
          </p>
        </section>
        <section className="panel prose">
          <h2>Known limitations</h2>
          <ul>
            {(
              info?.limitations || [
                "Model metadata is unavailable. Start the API to view this model’s limitations.",
              ]
            ).map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
          <p>
            Python and JavaScript are not supported by this trained release.
            Multi-function files, indirect data flow, dependencies, and
            vulnerabilities outside the four target families require other
            analysis.
          </p>
          <h2>Privacy & deployment</h2>
          <p>
            Source is sent only to the configured API. Submitted code is never
            executed, logged, or saved to history. History is off by default and
            stores only result metadata when enabled.
          </p>
          <p>
            This local research application has no multi-user authentication.
            Keep it on localhost or add authentication, TLS, and request
            controls before exposing it to a network.
          </p>
        </section>
      </div>
    </>
  );
}
