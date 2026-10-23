// RoboCode RAG Frontend Controller
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const tabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const statusBadge = document.getElementById("system-status-badge");
  const statusDot = statusBadge.querySelector(".status-dot");
  const statusText = document.getElementById("status-text");

  // Stats elements
  const statFiles = document.getElementById("stat-files");
  const statChunks = document.getElementById("stat-chunks");
  const statNodes = document.getElementById("stat-nodes");
  const btnRefreshStats = document.getElementById("btn-refresh-stats");

  // Query elements
  const queryInput = document.getElementById("query-input");
  const topKSelect = document.getElementById("top-k-select");
  const btnSubmitQuery = document.getElementById("btn-submit-query");
  const queryLoader = document.getElementById("query-loader");
  const resultsView = document.getElementById("results-view");
  const answerContent = document.getElementById("answer-content");
  const citationsList = document.getElementById("citations-list");
  const resLatency = document.getElementById("res-latency");
  const resCount = document.getElementById("res-count");
  const btnCopyAnswer = document.getElementById("btn-copy-answer");

  // Indexer elements
  const dropZone = document.getElementById("drop-zone");
  const fileUploadInput = document.getElementById("file-upload-input");
  const indexerPathInput = document.getElementById("indexer-path-input");
  const btnIndexServer = document.getElementById("btn-index-server");
  const indexProgress = document.getElementById("index-progress");
  const btnClearDb = document.getElementById("btn-clear-db");

  // Audit elements
  const auditCodeInput = document.getElementById("audit-code-input");
  const auditLangSelect = document.getElementById("audit-lang-select");
  const btnRunAudit = document.getElementById("btn-run-audit");
  const btnLoadSampleAudit = document.getElementById("btn-load-sample-audit");
  const auditResults = document.getElementById("audit-results");
  const auditSummaryCards = document.getElementById("audit-summary-cards");
  const auditIssuesList = document.getElementById("audit-issues-list");

  // 1. Tab Navigation
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // 2. Health & Status Polling
  async function fetchStatus() {
    try {
      const res = await fetch("/health");
      if (res.ok) {
        const data = await res.json();
        statusDot.classList.add("healthy");
        statusText.textContent = "Render Cloud Active";

        if (data.database) {
          statFiles.textContent = data.database.files_indexed;
          statChunks.textContent = data.database.chunks_indexed;
        }
      } else {
        throw new Error("Offline");
      }
    } catch (e) {
      statusDot.classList.remove("healthy");
      statusText.textContent = "API Disconnected";
    }

    try {
      const statsRes = await fetch("/api/status");
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        statFiles.textContent = statsData.stats.total_files;
        statChunks.textContent = statsData.stats.total_chunks;
        statNodes.textContent = statsData.stats.total_robotics_nodes;
      }
    } catch (_) {}
  }

  btnRefreshStats.addEventListener("click", fetchStatus);
  fetchStatus();

  // 3. Query & RAG Execution
  async function executeQuery() {
    const query = queryInput.value.trim();
    if (!query) {
      queryInput.focus();
      return;
    }

    const topK = parseInt(topKSelect.value, 10);
    queryLoader.classList.remove("hidden");
    resultsView.classList.add("hidden");

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, top_k: topK })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Query failed");
      }

      const data = await res.json();
      renderResults(data);
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      queryLoader.classList.add("hidden");
    }
  }

  function renderResults(data) {
    resLatency.textContent = `${data.latency_ms} ms`;
    resCount.textContent = `${data.total_found} Citations`;

    // Format Markdown simple parser for bold and code
    let formattedAnswer = data.answer
      .replace(/### (.*?)\n/g, '<h3>$1</h3>')
      .replace(/#### (.*?)\n/g, '<h4>$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/\n\n/g, '<br><br>');

    answerContent.innerHTML = formattedAnswer;

    // Render Citations
    citationsList.innerHTML = "";
    data.citations.forEach((c, idx) => {
      const card = document.createElement("div");
      card.className = "citation-card";
      card.innerHTML = `
        <div class="citation-header">
          <span class="citation-path">${c.file_path}:${c.start_line}-${c.end_line} ${c.symbol_name ? `(${c.symbol_name})` : ''}</span>
          <span class="citation-score">Relevance: ${c.relevance_score}%</span>
        </div>
        <pre class="code-snippet"><code>${escapeHtml(c.snippet)}</code></pre>
      `;
      citationsList.appendChild(card);
    });

    resultsView.classList.remove("hidden");
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
  }

  btnSubmitQuery.addEventListener("click", executeQuery);
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      executeQuery();
    }
  });

  // Example Chips
  document.querySelectorAll(".example-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      queryInput.value = chip.dataset.q;
      executeQuery();
    });
  });

  // Copy Answer
  btnCopyAnswer.addEventListener("click", () => {
    navigator.clipboard.writeText(answerContent.innerText).then(() => {
      btnCopyAnswer.textContent = "Copied!";
      setTimeout(() => btnCopyAnswer.textContent = "Copy Answer", 2000);
    });
  });

  // 4. Indexer - Server Directory
  btnIndexServer.addEventListener("click", async () => {
    const path = indexerPathInput.value.trim();
    if (!path) return;

    btnIndexServer.disabled = true;
    btnIndexServer.textContent = "Indexing...";
    indexProgress.classList.remove("hidden");
    indexProgress.textContent = "Scanning directory and building hybrid vector store...";

    try {
      const res = await fetch("/api/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_path: path })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Indexing failed");

      indexProgress.textContent = data.message;
      fetchStatus();
    } catch (err) {
      indexProgress.textContent = "Error: " + err.message;
    } finally {
      btnIndexServer.disabled = false;
      btnIndexServer.textContent = "Index Path";
    }
  });

  // 5. Indexer - File Upload (Drag & Drop or File Select)
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileUploadInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    indexProgress.classList.remove("hidden");
    indexProgress.textContent = `Uploading ${file.name} to Render container and indexing...`;

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      indexProgress.textContent = `Upload complete! Indexed ${data.index_result.files_indexed} files.`;
      fetchStatus();
    } catch (err) {
      indexProgress.textContent = "Upload failed: " + err.message;
    }
  }

  // Clear Database
  btnClearDb.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear all indexed files?")) return;
    try {
      await fetch("/api/clear", { method: "POST" });
      fetchStatus();
      alert("Index cleared.");
    } catch (e) {
      alert("Error: " + e.message);
    }
  });

  // 6. Robotics Static Audit
  btnLoadSampleAudit.addEventListener("click", () => {
    auditCodeInput.value = `#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64.hpp>
#include <thread>
#include <chrono>

class MotorPIDNode : public rclcpp::Node {
public:
  MotorPIDNode() : Node("motor_pid_node") {
    // ROS2 Publisher for motor torque
    publisher_ = this->create_publisher<std_msgs::msg::Float64>("motor/torque_cmd", 10);
    
    // ROS2 Subscriber for encoder position feedback
    subscription_ = this->create_subscription<std_msgs::msg::Float64>(
      "encoder/position", 10, std::bind(&MotorPIDNode::feedback_callback, this, std::placeholders::_1));
      
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(10), std::bind(&MotorPIDNode::control_loop, this));
  }

private:
  void control_loop() {
    // CRITICAL RT VIOLATION: Blocking delay inside control loop!
    delay(5); 

    // DYNAMIC ALLOCATION VIOLATION inside real-time control loop
    double* dynamic_buf = new double[100];
    delete[] dynamic_buf;

    std_msgs::msg::Float64 msg;
    msg.data = 12.5;
    publisher_->publish(msg);
  }

  void feedback_callback(const std_msgs::msg::Float64::SharedPtr msg) {
    RCLCPP_INFO(this->get_logger(), "Current pos: %f", msg->data);
  }

  rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr publisher_;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr subscription_;
  rclcpp::TimerBase::SharedPtr timer_;
};`;
  });

  btnRunAudit.addEventListener("click", async () => {
    const code = auditCodeInput.value.trim();
    if (!code) return;

    btnRunAudit.disabled = true;
    btnRunAudit.textContent = "Auditing...";

    try {
      const res = await fetch("/api/analyze-robotics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          language: auditLangSelect.value,
          file_name: "sample_node." + (auditLangSelect.value === "python" ? "py" : "cpp")
        })
      });

      const data = await res.json();
      renderAuditResults(data.analysis);
    } catch (err) {
      alert("Audit error: " + err.message);
    } finally {
      btnRunAudit.disabled = false;
      btnRunAudit.textContent = "Run Static Audit";
    }
  });

  function renderAuditResults(analysis) {
    auditResults.classList.remove("hidden");
    
    auditSummaryCards.innerHTML = `
      <div class="metric-card">
        <span class="stat-title">Framework</span>
        <div class="metric-val" style="color: var(--accent-cyan)">${analysis.framework.toUpperCase()}</div>
      </div>
      <div class="metric-card">
        <span class="stat-title">Publishers</span>
        <div class="metric-val" style="color: var(--accent-emerald)">${analysis.publishers.length}</div>
      </div>
      <div class="metric-card">
        <span class="stat-title">Subscribers</span>
        <div class="metric-val" style="color: var(--accent-emerald)">${analysis.subscribers.length}</div>
      </div>
      <div class="metric-card">
        <span class="stat-title">Real-Time Violations</span>
        <div class="metric-val" style="color: ${analysis.realtime_issues.length > 0 ? 'var(--accent-crimson)' : 'var(--accent-emerald)'}">
          ${analysis.realtime_issues.length}
        </div>
      </div>
    `;

    auditIssuesList.innerHTML = "";
    if (analysis.realtime_issues.length === 0) {
      auditIssuesList.innerHTML = `<div class="index-feedback">✅ No real-time or memory safety issues detected. Deterministic loop compliant!</div>`;
    } else {
      analysis.realtime_issues.forEach(issue => {
        const item = document.createElement("div");
        item.className = `issue-item ${issue.severity}`;
        item.innerHTML = `
          <strong>[Line ${issue.line}] ${issue.severity}: ${issue.type}</strong>
          <code>${escapeHtml(issue.code)}</code>
          <span>${issue.issue}</span>
        `;
        auditIssuesList.appendChild(item);
      });
    }
  }
});
