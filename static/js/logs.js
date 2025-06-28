document.addEventListener("DOMContentLoaded", () => {
  // Load logs data
  loadLogsData()

  // Set up event listeners
  setupEventListeners()
})

// Load logs data
function loadLogsData(filter = "all") {
  const logsTableBody = document.getElementById("logs-table-body")

  if (logsTableBody) {
    fetch(`/api/logs?filter=${filter}`)
      .then((response) => response.json())
      .then((data) => {
        const logs = data.logs || []
        logsTableBody.innerHTML = ""

        if (logs.length === 0) {
          logsTableBody.innerHTML = '<tr><td colspan="5">No logs found</td></tr>'
        } else {
          logs.forEach((log) => {
            const row = document.createElement("tr")
            row.innerHTML = `
              <td>${log.timestamp}</td>
              <td>${log.action}</td>
              <td>${log.status}</td>
              <td>${log.user}</td>
              <td>${log.details || ""}</td>
            `
            logsTableBody.appendChild(row)
          })
        }
      })
      .catch((error) => console.error("Error loading logs data:", error))
  }
}

// Set up event listeners
function setupEventListeners() {
  // Log filter
  const logFilter = document.getElementById("log-filter")
  if (logFilter) {
    logFilter.addEventListener("change", function () {
      loadLogsData(this.value)
    })
  }

  // Download logs
  const downloadLogsBtn = document.getElementById("download-logs-btn")
  if (downloadLogsBtn) {
    downloadLogsBtn.addEventListener("click", () => {
      fetch("/api/logs")
        .then((response) => response.json())
        .then((data) => {
          const logs = data.logs || []
          if (logs.length === 0) {
            showPopupNotification("No logs to download", "info")
            return
          }

          // Convert logs to CSV
          const headers = ["Timestamp", "Action", "Status", "User", "Details"]
          const csvContent = [
            headers.join(","),
            ...logs.map((log) => [log.timestamp, log.action, log.status, log.user, log.details].join(",")),
          ].join("\n")

          // Create download link
          const blob = new Blob([csvContent], { type: "text/csv" })
          const url = URL.createObjectURL(blob)
          const a = document.createElement("a")
          a.href = url
          a.download = `door_logs_${new Date().toISOString().split("T")[0]}.csv`
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        })
        .catch((error) => {
          console.error("Error downloading logs:", error)
          showPopupNotification("Failed to download logs", "error")
        })
    })
  }
}

// Show popup notification
function showPopupNotification(message, type = "info") {
  // Create popup element
  const popup = document.createElement("div")
  popup.classList.add("popup-notification")
  popup.classList.add(type)
  popup.textContent = message

  // Add popup to body
  document.body.appendChild(popup)

  // Remove popup after 3 seconds
  setTimeout(() => {
    popup.remove()
  }, 3000)
}
