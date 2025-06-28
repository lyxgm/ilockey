document.addEventListener("DOMContentLoaded", () => {
  // Initialize the application
  initApp()
})

// Global variables
let doorLocked = true
let cameraOn = false
let currentUser = null
let userPermissions = []
let notificationsData = []
const loadMetricsData = null
const loadLogsData = null
const loadUsersData = null
const loadSettingsData = null
let loadFingerprintStatusVar = null // Declare the variable here

// Initialize the application
function initApp() {
  console.log("Initializing Smart Door Lock App")

  // Load current user information
  loadCurrentUser()

  // Set up navigation
  setupNavigation()

  // Set up notifications
  setupNotifications()

  // Initialize dashboard
  initDashboard()

  // Set up event listeners for all sections
  setupEventListeners()

  // Load initial data
  loadRecentActivity()

  // Refresh data periodically
  setInterval(refreshData, 30000) // Every 30 seconds
}

// Load current user information
function loadCurrentUser() {
  fetch("/api/user/current")
    .then((response) => response.json())
    .then((data) => {
      if (data.user) {
        currentUser = data.user
        userPermissions = currentUser.permissions || []

        // Update username display
        const usernameElement = document.getElementById("username")
        if (usernameElement) {
          usernameElement.textContent = currentUser.username
        }

        updateUIBasedOnPermissions()
      }
    })
    .catch((error) => console.error("Error loading user data:", error))
}

// Update UI based on user permissions
function updateUIBasedOnPermissions() {
  if (!currentUser) return

  // Hide elements based on permissions
  const navItems = [
    { section: "people", permission: "manage_users" },
    { section: "settings", permission: "change_settings" },
    { section: "logs", permission: "view_logs" },
  ]

  navItems.forEach(({ section, permission }) => {
    const navElement = document.querySelector(`a[data-section="${section}"]`)
    if (navElement) {
      const hasPermission =
        userPermissions.includes(permission) || currentUser.role === "admin" || currentUser.role === "administrator"

      if (!hasPermission) {
        navElement.parentElement.style.display = "none"
      }
    }
  })

  // Disable door control if no unlock permission
  if (!userPermissions.includes("unlock") && currentUser.role !== "admin") {
    const doorBtn = document.getElementById("toggle-door-btn")
    if (doorBtn) {
      doorBtn.disabled = true
      doorBtn.title = "You don't have permission to control the door"
    }
  }

  // Update permissions display in profile
  updatePermissionsDisplay()
}

// Update permissions display
function updatePermissionsDisplay() {
  const permissionsContainer = document.getElementById("user-permissions")
  if (!permissionsContainer) return

  permissionsContainer.innerHTML = ""

  if (userPermissions.length === 0) {
    permissionsContainer.innerHTML = "<p>You have no special permissions.</p>"
    return
  }

  const permissionLabels = {
    unlock: { icon: "fa-door-open", label: "Door Unlock" },
    view_logs: { icon: "fa-list", label: "View Logs" },
    manage_users: { icon: "fa-users", label: "Manage Users" },
    change_settings: { icon: "fa-cog", label: "Change Settings" },
  }

  userPermissions.forEach((permission) => {
    const permItem = document.createElement("div")
    permItem.className = "permission-item"

    const config = permissionLabels[permission] || { icon: "fa-check", label: permission }
    permItem.innerHTML = `<i class="fas ${config.icon}"></i> ${config.label}`

    permissionsContainer.appendChild(permItem)
  })
}

// Set up navigation
function setupNavigation() {
  const navLinks = document.querySelectorAll(".main-nav a")

  navLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault()

      // Remove active class from all links and sections
      navLinks.forEach((l) => l.classList.remove("active"))
      document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"))

      // Add active class to clicked link
      this.classList.add("active")

      // Show the selected section
      const sectionId = this.getAttribute("data-section")
      const section = document.getElementById(sectionId)
      if (section) {
        section.classList.add("active")

        // Load section-specific data
        loadSectionData(sectionId)
      }
    })
  })
}

// Load section-specific data
function loadSectionData(sectionId) {
  switch (sectionId) {
    case "dashboard":
      loadRecentActivity()
      break
    case "metrics":
      if (typeof loadMetricsData === "function") loadMetricsData()
      break
    case "logs":
      if (typeof loadLogsData === "function") loadLogsData()
      break
    case "people":
      if (typeof loadUsersData === "function") loadUsersData()
      break
    case "settings":
      if (typeof loadSettingsData === "function") loadSettingsData()
      break
    case "profile":
      loadProfileData()
      break
  }
}

// Load profile data
function loadProfileData() {
  console.log("Loading profile data...")

  // Load profile information
  fetch("/api/profile")
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.profile) {
        const profile = data.profile
        console.log("Profile loaded:", profile)

        // Update form fields
        const usernameField = document.getElementById("profile-username")
        const nameField = document.getElementById("profile-name")
        const emailField = document.getElementById("profile-email")
        const roleField = document.getElementById("profile-role")

        if (usernameField) usernameField.value = profile.username || ""
        if (nameField) nameField.value = profile.name || ""
        if (emailField) emailField.value = profile.email || ""
        if (roleField) roleField.value = profile.role || ""

        // Set current username for fingerprint operations
        window.currentUsername = profile.username || "unknown"

        // Load fingerprint status
        loadFingerprintStatusVar()

        // Load user activity
        loadProfileActivity(profile.username)

        // Update permissions display
        updatePermissionsDisplay()
      }
    })
    .catch((error) => {
      console.error("Error loading profile:", error)
      showPopupNotification("Failed to load profile data", "error")
    })
}

// Load fingerprint status
function loadFingerprintStatus() {
  const username = window.currentUsername || currentUser?.username
  if (!username) {
    console.error("No username available for fingerprint status")
    return
  }

  console.log("Loading fingerprint status for:", username)

  fetch(`/api/fingerprint/status/${username}`)
    .then((response) => response.json())
    .then((data) => {
      console.log("Fingerprint status:", data)
      updateProfileFingerprintStatus(data)
    })
    .catch((error) => {
      console.error("Error loading fingerprint status:", error)
      updateProfileFingerprintStatus({ success: false, enrolled: false })
    })
}

// Update fingerprint status display
function updateProfileFingerprintStatus(data) {
  const statusElement = document.getElementById("profile-fingerprint-status")
  const enrollBtn = document.getElementById("profile-enroll-fingerprint-btn")
  const deleteBtn = document.getElementById("profile-delete-fingerprint-btn")
  const enrollmentDetails = document.getElementById("enrollment-details")
  const enrollmentDate = document.getElementById("enrollment-date")

  if (!statusElement) {
    console.error("Profile fingerprint status element not found")
    return
  }

  if (data.success && data.enrolled) {
    statusElement.textContent = "Enrolled"
    statusElement.className = "status-badge enrolled"

    if (enrollBtn) enrollBtn.style.display = "none"
    if (deleteBtn) deleteBtn.style.display = "inline-block"

    if (data.enrolled_date && enrollmentDate) {
      enrollmentDate.textContent = new Date(data.enrolled_date).toLocaleDateString()
      if (enrollmentDetails) enrollmentDetails.style.display = "block"
    }
  } else {
    statusElement.textContent = "Not Enrolled"
    statusElement.className = "status-badge not-enrolled"

    if (enrollBtn) enrollBtn.style.display = "inline-block"
    if (deleteBtn) deleteBtn.style.display = "none"
    if (enrollmentDetails) enrollmentDetails.style.display = "none"
  }

  // Set up event listeners
  setupFingerprintEventListeners()
}

// Set up fingerprint event listeners
function setupFingerprintEventListeners() {
  const enrollBtn = document.getElementById("profile-enroll-fingerprint-btn")
  const deleteBtn = document.getElementById("profile-delete-fingerprint-btn")

  if (enrollBtn) {
    // Remove existing listeners
    enrollBtn.replaceWith(enrollBtn.cloneNode(true))
    const newEnrollBtn = document.getElementById("profile-enroll-fingerprint-btn")

    newEnrollBtn.addEventListener("click", () => {
      const username = window.currentUsername || currentUser?.username
      if (username) {
        showFingerprintEnrollmentModal(username)
      } else {
        showPopupNotification("Username not available", "error")
      }
    })
  }

  if (deleteBtn) {
    // Remove existing listeners
    deleteBtn.replaceWith(deleteBtn.cloneNode(true))
    const newDeleteBtn = document.getElementById("profile-delete-fingerprint-btn")

    newDeleteBtn.addEventListener("click", () => {
      if (confirm("Are you sure you want to remove your fingerprint data?")) {
        const username = window.currentUsername || currentUser?.username
        if (username) {
          deleteFingerprintData(username)
        } else {
          showPopupNotification("Username not available", "error")
        }
      }
    })
  }
}

// Delete fingerprint data
function deleteFingerprintData(username) {
  fetch("/api/fingerprint/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("Fingerprint data removed successfully", "success")
        loadFingerprintStatus() // Reload status
      } else {
        showPopupNotification(data.message || "Failed to remove fingerprint data", "error")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showPopupNotification("An error occurred", "error")
    })
}

// Show fingerprint enrollment modal
function showFingerprintEnrollmentModal(username) {
  console.log("Starting fingerprint enrollment for:", username)

  // Create modal if it doesn't exist
  let modal = document.getElementById("fingerprint-modal")
  if (!modal) {
    modal = document.createElement("div")
    modal.id = "fingerprint-modal"
    modal.className = "modal"

    const modalContent = document.createElement("div")
    modalContent.className = "modal-content"

    const modalHeader = document.createElement("div")
    modalHeader.className = "modal-header"

    const modalTitle = document.createElement("h3")
    modalTitle.id = "fingerprint-modal-title"
    modalTitle.textContent = "Fingerprint Enrollment"

    const closeBtn = document.createElement("span")
    closeBtn.className = "close"
    closeBtn.innerHTML = "&times;"
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("active")
    })

    modalHeader.appendChild(modalTitle)
    modalHeader.appendChild(closeBtn)

    const modalBody = document.createElement("div")
    modalBody.className = "modal-body"
    modalBody.innerHTML = `
      <div class="fingerprint-enrollment">
        <div class="fingerprint-scanner">
          <i class="fas fa-fingerprint"></i>
          <div class="scanner-status" id="scanner-status">Ready</div>
        </div>
        <div class="enrollment-instructions">
          <p>Please place your finger on the scanner.</p>
          <p>You will need to scan your finger 3 times to complete enrollment.</p>
          <div class="enrollment-progress">
            <div class="progress-step" id="step-1">1</div>
            <div class="progress-step" id="step-2">2</div>
            <div class="progress-step" id="step-3">3</div>
          </div>
        </div>
        <div class="enrollment-status" id="enrollment-status"></div>
      </div>
    `

    modalContent.appendChild(modalHeader)
    modalContent.appendChild(modalBody)
    modal.appendChild(modalContent)
    document.body.appendChild(modal)
  }

  // Reset enrollment state
  document.getElementById("scanner-status").textContent = "Ready"
  document.getElementById("enrollment-status").textContent = ""
  document.getElementById("step-1").className = "progress-step"
  document.getElementById("step-2").className = "progress-step"
  document.getElementById("step-3").className = "progress-step"

  const fingerprintScanner = document.querySelector(".fingerprint-scanner")
  fingerprintScanner.className = "fingerprint-scanner"

  // Show modal
  modal.classList.add("active")

  // Start enrollment process
  startProfileFingerprintEnrollment(username)
}

// Start fingerprint enrollment for profile
function startProfileFingerprintEnrollment(username) {
  const scannerStatus = document.getElementById("scanner-status")
  const enrollmentStatus = document.getElementById("enrollment-status")
  const fingerprintScanner = document.querySelector(".fingerprint-scanner")

  let currentStep = 1

  simulateEnrollmentStep()

  function simulateEnrollmentStep() {
    document.getElementById(`step-${currentStep}`).className = "progress-step active"
    scannerStatus.textContent = "Scanning..."
    fingerprintScanner.className = "fingerprint-scanner scanning"

    setTimeout(() => {
      document.getElementById(`step-${currentStep}`).className = "progress-step completed"

      if (currentStep < 3) {
        currentStep++
        enrollmentStatus.textContent = `Scan ${currentStep} of 3`
        scannerStatus.textContent = "Place finger again"
        fingerprintScanner.className = "fingerprint-scanner"
        setTimeout(simulateEnrollmentStep, 1500)
      } else {
        completeProfileEnrollment(username)
      }
    }, 2000)
  }

  function completeProfileEnrollment(username) {
    scannerStatus.textContent = "Processing..."

    fetch("/api/fingerprint/enroll", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          enrollmentStatus.textContent = "Enrollment successful!"
          scannerStatus.textContent = "Complete"
          fingerprintScanner.className = "fingerprint-scanner success"

          showPopupNotification("Fingerprint enrolled successfully!", "success")

          setTimeout(() => {
            document.getElementById("fingerprint-modal").classList.remove("active")
            loadFingerprintStatus() // Reload status
          }, 2000)
        } else {
          enrollmentStatus.textContent = data.message || "Enrollment failed"
          scannerStatus.textContent = "Error"
          fingerprintScanner.className = "fingerprint-scanner error"
          showPopupNotification(data.message || "Fingerprint enrollment failed", "error")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        enrollmentStatus.textContent = "An error occurred"
        scannerStatus.textContent = "Error"
        fingerprintScanner.className = "fingerprint-scanner error"
        showPopupNotification("An error occurred during enrollment", "error")
      })
  }
}

// Load profile activity
function loadProfileActivity(username) {
  const activityContainer = document.getElementById("profile-activity")
  if (!activityContainer) return

  fetch(`/api/logs?user=${username}&limit=10`)
    .then((response) => response.json())
    .then((data) => {
      const logs = data.logs || []
      activityContainer.innerHTML = ""

      if (logs.length === 0) {
        activityContainer.innerHTML = '<div class="activity-item">No recent activity</div>'
        return
      }

      logs.forEach((log) => {
        const activityItem = document.createElement("div")
        activityItem.className = "activity-item"

        const { icon, action } = getLogDisplayInfo(log)

        activityItem.innerHTML = `
          <div><i class="fas ${icon}"></i> ${action}</div>
          <div class="time">${log.timestamp}</div>
        `
        activityContainer.appendChild(activityItem)
      })
    })
    .catch((error) => {
      console.error("Error loading profile activity:", error)
      activityContainer.innerHTML = '<div class="activity-item text-danger">Error loading activity</div>'
    })
}

// Set up notifications
function setupNotifications() {
  const notificationsToggle = document.getElementById("notifications-toggle")
  const notificationsPanel = document.getElementById("notifications-panel")
  const clearNotificationsBtn = document.getElementById("clear-notifications")

  if (notificationsToggle && notificationsPanel) {
    // Toggle notifications panel
    notificationsToggle.addEventListener("click", (e) => {
      e.stopPropagation()
      notificationsPanel.classList.toggle("active")
      if (notificationsPanel.classList.contains("active")) {
        loadNotifications()
      }
    })

    // Close notifications panel when clicking outside
    document.addEventListener("click", (e) => {
      if (!notificationsPanel.contains(e.target) && e.target !== notificationsToggle) {
        notificationsPanel.classList.remove("active")
      }
    })
  }

  if (clearNotificationsBtn) {
    clearNotificationsBtn.addEventListener("click", () => {
      const notificationsList = document.getElementById("notifications-list")
      if (notificationsList) {
        notificationsList.innerHTML = '<div class="notification-item">No notifications</div>'
      }

      const badge = document.getElementById("notifications-badge")
      if (badge) {
        badge.textContent = "0"
      }

      notificationsData = []
    })
  }

  // Load initial notifications
  loadNotifications()
}

// Load notifications
function loadNotifications() {
  fetch("/api/notifications")
    .then((response) => response.json())
    .then((data) => {
      notificationsData = data.notifications || []
      updateNotificationsUI()
    })
    .catch((error) => {
      console.error("Error loading notifications:", error)
      // Set empty notifications on error
      notificationsData = []
      updateNotificationsUI()
    })
}

// Update notifications UI
function updateNotificationsUI() {
  const notificationsList = document.getElementById("notifications-list")
  const badge = document.getElementById("notifications-badge")

  if (notificationsList) {
    notificationsList.innerHTML = ""

    if (notificationsData.length === 0) {
      notificationsList.innerHTML = '<div class="notification-item">No notifications</div>'
    } else {
      notificationsData.forEach((notification) => {
        const notificationItem = document.createElement("div")
        notificationItem.className = `notification-item ${notification.type || "info"}`
        notificationItem.innerHTML = `
          <div>${notification.message}</div>
          <div class="time">${notification.timestamp}</div>
        `
        notificationsList.appendChild(notificationItem)
      })
    }
  }

  if (badge) {
    badge.textContent = notificationsData.length.toString()
  }
}

// Initialize dashboard
function initDashboard() {
  // Door control
  setupDoorControl()

  // Camera control
  setupCameraControl()

  // Load initial states
  loadInitialStates()
}

// Setup door control
function setupDoorControl() {
  const toggleDoorBtn = document.getElementById("toggle-door-btn")

  if (toggleDoorBtn) {
    toggleDoorBtn.addEventListener("click", () => {
      if (!userPermissions.includes("unlock") && currentUser?.role !== "admin") {
        showPopupNotification("You don't have permission to control the door", "error")
        return
      }

      const action = doorLocked ? "unlock" : "lock"

      fetch("/api/door/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            doorLocked = !doorLocked
            updateDoorUI()
            showPopupNotification(`Door ${action}ed successfully`, "success")
            loadRecentActivity()
          } else {
            showPopupNotification(data.message || "Failed to control door", "error")
          }
        })
        .catch((error) => {
          console.error("Error toggling door:", error)
          showPopupNotification("Failed to control door", "error")
        })
    })
  }
}

// Setup camera control
function setupCameraControl() {
  const toggleCameraBtn = document.getElementById("toggle-camera-btn")
  const captureBtn = document.getElementById("capture-btn")

  if (toggleCameraBtn) {
    toggleCameraBtn.addEventListener("click", () => {
      const action = cameraOn ? "off" : "on"

      fetch("/api/camera/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            cameraOn = !cameraOn
            updateCameraUI()
            showPopupNotification(`Camera turned ${action}`, "info")
          } else {
            showPopupNotification(data.message || "Failed to control camera", "error")
          }
        })
        .catch((error) => {
          console.error("Error toggling camera:", error)
          showPopupNotification("Failed to control camera", "error")
        })
    })
  }

  if (captureBtn) {
    captureBtn.addEventListener("click", () => {
      if (!cameraOn) {
        showPopupNotification("Please turn on the camera first", "warning")
        return
      }

      fetch("/api/camera/capture", { method: "POST" })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showPopupNotification("Image captured successfully", "success")
            loadRecentActivity()
          } else {
            showPopupNotification(data.message || "Failed to capture image", "error")
          }
        })
        .catch((error) => {
          console.error("Error capturing image:", error)
          showPopupNotification("Failed to capture image", "error")
        })
    })
  }
}

// Load initial states
function loadInitialStates() {
  // Load door status
  fetch("/api/door/status")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        doorLocked = data.locked
        updateDoorUI()
      }
    })
    .catch((error) => console.error("Error getting door status:", error))

  // Load camera status
  fetch("/api/camera/status")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        cameraOn = data.enabled
        updateCameraUI()
      }
    })
    .catch((error) => console.error("Error getting camera status:", error))
}

// Update door UI
function updateDoorUI() {
  const toggleDoorBtn = document.getElementById("toggle-door-btn")
  const doorStatusIcon = document.getElementById("door-status-icon")
  const doorStatusText = document.getElementById("door-status-text")

  if (doorStatusIcon) {
    doorStatusIcon.className = doorLocked ? "fas fa-lock" : "fas fa-unlock"
  }

  if (doorStatusText) {
    doorStatusText.textContent = doorLocked ? "Locked" : "Unlocked"
  }

  if (toggleDoorBtn) {
    toggleDoorBtn.innerHTML = doorLocked
      ? '<i class="fas fa-unlock"></i> Unlock Door'
      : '<i class="fas fa-lock"></i> Lock Door'
  }
}

// Update camera UI
function updateCameraUI() {
  const toggleCameraBtn = document.getElementById("toggle-camera-btn")
  const captureBtn = document.getElementById("capture-btn")
  const cameraPlaceholder = document.getElementById("camera-placeholder")
  const cameraFeed = document.getElementById("camera-feed")

  if (toggleCameraBtn) {
    toggleCameraBtn.innerHTML = cameraOn
      ? '<i class="fas fa-video-slash"></i> Turn Off Camera'
      : '<i class="fas fa-video"></i> Turn On Camera'
  }

  if (captureBtn) {
    captureBtn.disabled = !cameraOn
  }

  if (cameraPlaceholder && cameraFeed) {
    if (cameraOn) {
      cameraPlaceholder.classList.add("hidden")
      cameraFeed.classList.remove("hidden")
      cameraFeed.src = `/api/camera/stream?t=${Date.now()}`
    } else {
      cameraPlaceholder.classList.remove("hidden")
      cameraFeed.classList.add("hidden")
      cameraFeed.removeAttribute("src")
    }
  }
}

// Load recent activity
function loadRecentActivity() {
  const recentActivity = document.getElementById("recent-activity")
  if (!recentActivity) return

  fetch("/api/logs")
    .then((response) => response.json())
    .then((data) => {
      const logs = data.logs || []
      recentActivity.innerHTML = ""

      if (logs.length === 0) {
        recentActivity.innerHTML = '<div class="activity-item">No recent activity</div>'
        return
      }

      // Show only the 10 most recent logs
      logs.slice(0, 10).forEach((log) => {
        const activityItem = document.createElement("div")
        activityItem.className = "activity-item"

        const { icon, action } = getLogDisplayInfo(log)

        activityItem.innerHTML = `
          <div><i class="fas ${icon}"></i> ${action}</div>
          <div class="time">${log.timestamp}</div>
        `
        recentActivity.appendChild(activityItem)
      })
    })
    .catch((error) => {
      console.error("Error loading recent activity:", error)
      recentActivity.innerHTML = '<div class="activity-item text-danger">Error loading activity</div>'
    })
}

// Get log display information
function getLogDisplayInfo(log) {
  let icon, action

  switch (log.action) {
    case "door":
      icon = log.status === "unlock" ? "fa-door-open" : "fa-lock"
      action = `Door ${log.status}ed`
      break
    case "login":
      icon = "fa-sign-in-alt"
      action = `User ${log.user} logged in`
      break
    case "logout":
      icon = "fa-sign-out-alt"
      action = `User ${log.user} logged out`
      break
    case "camera":
      icon = log.status === "capture" ? "fa-camera" : "fa-video"
      action = log.status === "capture" ? "Image captured" : `Camera turned ${log.status}`
      break
    case "fingerprint":
      icon = "fa-fingerprint"
      action = `Fingerprint ${log.status}`
      break
    default:
      icon = "fa-info-circle"
      action = `${log.action}: ${log.status}`
  }

  return { icon, action }
}

// Set up event listeners for all sections
function setupEventListeners() {
  // Settings form
  const settingsForm = document.getElementById("settings-form")
  if (settingsForm) {
    settingsForm.addEventListener("submit", handleSettingsSubmit)
  }

  // Profile form
  const profileForm = document.getElementById("profile-form")
  if (profileForm) {
    profileForm.addEventListener("submit", handleProfileSubmit)
  }

  // User management
  setupUserManagement()

  // Log management
  setupLogManagement()
}

// Handle settings form submission
function handleSettingsSubmit(e) {
  e.preventDefault()

  const formData = {
    system_passcode: document.getElementById("system-passcode")?.value,
    max_trials: Number.parseInt(document.getElementById("max-trials")?.value) || 3,
    lockout_passcode: document.getElementById("lockout-passcode")?.value,
    auto_lock_delay: Number.parseInt(document.getElementById("auto-lock-delay")?.value) || 5,
  }

  fetch("/api/settings/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("Settings updated successfully", "success")
      } else {
        showPopupNotification(data.message || "Failed to update settings", "error")
      }
    })
    .catch((error) => {
      console.error("Error updating settings:", error)
      showPopupNotification("Failed to update settings", "error")
    })
}

// Handle profile form submission
function handleProfileSubmit(e) {
  e.preventDefault()

  const formData = {
    username: document.getElementById("profile-username")?.value,
    name: document.getElementById("profile-name")?.value,
    email: document.getElementById("profile-email")?.value,
  }

  const password = document.getElementById("profile-password")?.value
  if (password) {
    formData.password = password
  }

  fetch("/api/users/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("Profile updated successfully", "success")
        document.getElementById("profile-password").value = ""
      } else {
        showPopupNotification(data.message || "Failed to update profile", "error")
      }
    })
    .catch((error) => {
      console.error("Error updating profile:", error)
      showPopupNotification("Failed to update profile", "error")
    })
}

// Setup user management
function setupUserManagement() {
  const addUserBtn = document.getElementById("add-user-btn")
  const closeUserModal = document.getElementById("close-user-modal")
  const userModal = document.getElementById("user-modal")

  if (addUserBtn && userModal) {
    addUserBtn.addEventListener("click", () => {
      // Reset form and show modal
      resetUserForm()
      userModal.classList.add("active")
    })
  }

  if (closeUserModal && userModal) {
    closeUserModal.addEventListener("click", () => {
      userModal.classList.remove("active")
    })
  }
}

// Reset user form
function resetUserForm() {
  const form = document.getElementById("user-form")
  if (form) {
    form.reset()

    // Set default values
    const elements = {
      "user-form-mode": "add",
      "user-modal-title": "Add User",
      "user-role": "guest",
    }

    Object.entries(elements).forEach(([id, value]) => {
      const element = document.getElementById(id)
      if (element) {
        if (element.tagName === "INPUT" || element.tagName === "SELECT") {
          element.value = value
        } else {
          element.textContent = value
        }
      }
    })

    // Reset checkboxes
    const checkboxes = ["perm-unlock", "perm-view-logs", "perm-manage-users", "perm-change-settings"]
    checkboxes.forEach((id) => {
      const checkbox = document.getElementById(id)
      if (checkbox) {
        checkbox.checked = id === "perm-unlock" // Only unlock is checked by default
      }
    })
  }
}

// Setup log management
function setupLogManagement() {
  const downloadLogsBtn = document.getElementById("download-logs-btn")
  if (downloadLogsBtn) {
    downloadLogsBtn.addEventListener("click", downloadLogs)
  }
}

// Download logs
function downloadLogs() {
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
        ...logs.map((log) =>
          [log.timestamp, log.action, log.status, log.user, log.details || ""].map((field) => `"${field}"`).join(","),
        ),
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

      showPopupNotification("Logs downloaded successfully", "success")
    })
    .catch((error) => {
      console.error("Error downloading logs:", error)
      showPopupNotification("Failed to download logs", "error")
    })
}

// Refresh data
function refreshData() {
  // Only refresh if user is logged in
  if (!currentUser) return

  // Refresh notifications
  loadNotifications()

  // Refresh current section data
  const activeSection = document.querySelector(".section.active")
  if (activeSection) {
    loadSectionData(activeSection.id)
  }
}

// Show popup notification
function showPopupNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `popup-notification ${type}`
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas ${getNotificationIcon(type)}"></i>
      <span>${message}</span>
    </div>
  `

  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => notification.classList.add("show"), 10)

  // Hide and remove notification after 3 seconds
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 3000)
}

// Get notification icon based on type
function getNotificationIcon(type) {
  const icons = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
  }
  return icons[type] || icons.info
}
// Add popup notification styles
;(function addNotificationStyles() {
  if (document.getElementById("popup-notification-styles")) return

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
    
    .popup-notification.info i { color: #3498db; }
    .popup-notification.success i { color: #2ecc71; }
    .popup-notification.warning i { color: #f39c12; }
    .popup-notification.error i { color: #e74c3c; }
  `
  document.head.appendChild(style)
})()

// Assign the function to the variable
loadFingerprintStatusVar = loadFingerprintStatus
