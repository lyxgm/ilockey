document.addEventListener("DOMContentLoaded", () => {
  // Load settings data
  loadSettingsData()

  // Set up event listeners
  setupEventListeners()

  // Setup password toggles
  setupPasswordToggles()
})

// Load settings data
function loadSettingsData() {
  fetch("/api/settings")
    .then((response) => response.json())
    .then((data) => {
      const settings = data.settings || {}

      document.getElementById("system_passcode").value = settings.system_passcode || ""
      document.getElementById("max_trials").value = settings.max_trials || 3
      document.getElementById("lockout_passcode").value = settings.lockout_passcode || ""
      document.getElementById("auto_lock_delay").value = settings.auto_lock_delay || 5
      document.getElementById("keypad_enabled").checked = settings.keypad_enabled !== false
      document.getElementById("keypad_timeout").value = settings.keypad_timeout || 30
      document.getElementById("camera_enabled").checked = settings.camera_enabled !== false
    })
    .catch((error) => console.error("Error loading settings data:", error))
}

// Setup password visibility toggles
function setupPasswordToggles() {
  const toggleButtons = document.querySelectorAll(".password-toggle")

  toggleButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target")
      const targetInput = document.getElementById(targetId)
      const icon = this.querySelector("i")

      if (targetInput.type === "password") {
        targetInput.type = "text"
        icon.className = "fas fa-eye-slash"
      } else {
        targetInput.type = "password"
        icon.className = "fas fa-eye"
      }
    })
  })
}

// Set up event listeners
function setupEventListeners() {
  // Settings form
  const settingsForm = document.getElementById("settingsForm")
  if (settingsForm) {
    settingsForm.addEventListener("submit", (e) => {
      e.preventDefault()

      const systemPasscode = document.getElementById("system_passcode").value.trim()
      const maxTrials = document.getElementById("max_trials").value
      const lockoutPasscode = document.getElementById("lockout_passcode").value.trim()
      const autoLockDelay = document.getElementById("auto_lock_delay").value
      const keypadEnabled = document.getElementById("keypad_enabled").checked
      const keypadTimeout = document.getElementById("keypad_timeout").value
      const cameraEnabled = document.getElementById("camera_enabled").checked

      // Validate required fields
      if (!systemPasscode) {
        showPopupNotification("System passcode is required", "error")
        return
      }

      if (!lockoutPasscode) {
        showPopupNotification("Lockout passcode is required", "error")
        return
      }

      if (systemPasscode === lockoutPasscode) {
        showPopupNotification("System and lockout passcodes must be different", "error")
        return
      }

      const settingsData = {
        system_passcode: systemPasscode,
        max_trials: Number.parseInt(maxTrials),
        lockout_passcode: lockoutPasscode,
        auto_lock_delay: Number.parseInt(autoLockDelay),
        keypad_enabled: keypadEnabled,
        keypad_timeout: Number.parseInt(keypadTimeout),
        camera_enabled: cameraEnabled,
      }

      // Show loading state
      const submitBtn = settingsForm.querySelector('button[type="submit"]')
      const originalText = submitBtn.innerHTML
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...'
      submitBtn.disabled = true

      fetch("/api/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settingsData),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showPopupNotification("Settings updated successfully", "success")

            // Show additional info about changes that require restart
            if (!keypadEnabled) {
              showPopupNotification("Keypad has been disabled", "info")
            } else if (keypadEnabled) {
              showPopupNotification("Keypad settings updated", "info")
            }

            if (!cameraEnabled) {
              showPopupNotification("Camera has been disabled", "info")
            }

            // Reload settings to confirm changes
            setTimeout(() => {
              loadSettingsData()
            }, 1000)
          } else {
            showPopupNotification(data.message || "Failed to update settings", "error")
          }
        })
        .catch((error) => {
          console.error("Error updating settings:", error)
          showPopupNotification("Failed to update settings", "error")
        })
        .finally(() => {
          // Restore button state
          submitBtn.innerHTML = originalText
          submitBtn.disabled = false
        })
    })
  }
}

function showPopupNotification(message, type) {
  // Create the notification element
  const notification = document.createElement("div")
  notification.classList.add("popup-notification")
  notification.classList.add(type) // "success", "error", "info", "warning"

  // Add the message with icon
  const iconClass = getNotificationIcon(type)
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas ${iconClass}"></i>
      <span>${message}</span>
    </div>
  `

  // Add to the document
  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => {
    notification.classList.add("show")
  }, 10)

  // Automatically remove the notification after a delay
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 3000)
}

function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "fa-check-circle"
    case "error":
      return "fa-exclamation-circle"
    case "warning":
      return "fa-exclamation-triangle"
    case "info":
    default:
      return "fa-info-circle"
  }
}
// Add popup notification styles if not already added
;(() => {
  if (!document.getElementById("popup-notification-styles")) {
    const style = document.createElement("style")
    style.id = "popup-notification-styles"
    style.textContent = `
      .popup-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background-color: white;
        border-radius: 4px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        z-index: 1100;
        transform: translateX(120%);
        transition: transform 0.3s ease;
        max-width: 300px;
      }
      
      .popup-notification.show {
        transform: translateX(0);
      }
      
      .popup-notification .notification-content {
        display: flex;
        align-items: center;
      }
      
      .popup-notification i {
        margin-right: 10px;
        font-size: 1.2rem;
      }
      
      .popup-notification.info i {
        color: #3498db;
      }
      
      .popup-notification.success i {
        color: #2ecc71;
      }
      
      .popup-notification.warning i {
        color: #f39c12;
      }
      
      .popup-notification.error i {
        color: #e74c3c;
      }
    `
    document.head.appendChild(style)
  }
})()
