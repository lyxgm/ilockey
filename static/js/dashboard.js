console.log("Dashboard JavaScript file loaded")

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM Content Loaded - Initializing dashboard")

  // Initialize dashboard
  initDashboard()

  // Load recent activity
  loadRecentActivity()

  // Refresh data periodically
  setInterval(() => {
    loadRecentActivity()
  }, 30000) // Every 30 seconds
})

// Global variables
let doorLocked = true
let cameraOn = false
let streamRetryCount = 0
const MAX_STREAM_RETRIES = 3
// Add these global variables at the top of the file with the other global variables
const galleryModal = null

// Initialize dashboard
function initDashboard() {
  console.log("Initializing dashboard components")

  // Door control
  const toggleDoorBtn = document.getElementById("toggle-door-btn")
  const doorStatusIcon = document.getElementById("door-status-icon")
  const doorStatusText = document.getElementById("door-status-text")

  console.log("Door elements found:", {
    toggleDoorBtn: !!toggleDoorBtn,
    doorStatusIcon: !!doorStatusIcon,
    doorStatusText: !!doorStatusText,
  })

  if (toggleDoorBtn) {
    toggleDoorBtn.addEventListener("click", () => {
      console.log("Door toggle button clicked")
      const action = doorLocked ? "unlock" : "lock"

      fetch("/api/door/toggle", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Door toggle response:", data)
          if (data.success) {
            doorLocked = !doorLocked
            updateDoorUI()

            // Show notification
            showPopupNotification(`Door ${action}ed successfully`, "success")

            // If door was unlocked, set up auto-lock timer
            if (action === "unlock" && data.auto_lock) {
              // Get settings to determine auto-lock delay
              fetch("/api/settings")
                .then((response) => response.json())
                .then((settingsData) => {
                  const autoLockDelay = settingsData.settings?.auto_lock_delay || 5

                  // Show notification about auto-lock
                  showPopupNotification(`Door will auto-lock in ${autoLockDelay} seconds`, "info")

                  // Set timer for auto-lock
                  setTimeout(() => {
                    if (!doorLocked) {
                      // Auto-lock the door
                      fetch("/api/door/toggle", {
                        method: "POST",
                        headers: {
                          "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ action: "lock" }),
                      })
                        .then((response) => response.json())
                        .then((lockData) => {
                          if (lockData.success) {
                            doorLocked = true
                            updateDoorUI()
                            showPopupNotification("Door auto-locked", "info")

                            // Refresh recent activity
                            loadRecentActivity()
                          }
                        })
                        .catch((error) => {
                          console.error("Error auto-locking door:", error)
                        })
                    }
                  }, autoLockDelay * 1000)
                })
                .catch((error) => {
                  console.error("Error fetching settings:", error)
                })
            }

            // Refresh recent activity
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

  // Camera control
  const toggleCameraBtn = document.getElementById("toggle-camera-btn")
  const captureBtn = document.getElementById("capture-btn")
  const cameraPlaceholder = document.getElementById("camera-placeholder")
  const cameraFeed = document.getElementById("camera-feed")

  console.log("Camera elements found:", {
    toggleCameraBtn: !!toggleCameraBtn,
    captureBtn: !!captureBtn,
    cameraPlaceholder: !!cameraPlaceholder,
    cameraFeed: !!cameraFeed,
  })

  if (toggleCameraBtn) {
    toggleCameraBtn.addEventListener("click", () => {
      const action = cameraOn ? "off" : "on"
      console.log(`Toggling camera: ${action}`)

      fetch("/api/camera/toggle", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Camera toggle response:", data)
          if (data.success) {
            cameraOn = !cameraOn
            streamRetryCount = 0 // Reset retry count when toggling
            updateCameraUI()

            // Show notification
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

      showPopupNotification("Capturing image from stream...", "info")

      fetch("/api/camera/capture", {
        method: "POST",
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Camera capture response:", data)
          if (data.success) {
            showPopupNotification("Image captured successfully", "success")

            // Add the captured image to the gallery
            if (data.filename) {
              addImageToGallery(data.filename)
            }

            // Refresh recent activity
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

  // Add this to the initDashboard function after the camera control section
  // Gallery button
  const galleryBtn = document.getElementById("gallery-btn")
  if (galleryBtn) {
    galleryBtn.addEventListener("click", () => {
      openGalleryModal()
    })
  }

  // Check initial door and camera state
  console.log("Fetching initial door status")
  fetch("/api/door/status")
    .then((response) => response.json())
    .then((data) => {
      console.log("Door status response:", data)
      if (data.success) {
        doorLocked = data.locked
        updateDoorUI()
      }
    })
    .catch((error) => {
      console.error("Error getting door status:", error)
    })

  console.log("Fetching initial camera status")
  fetch("/api/camera/status")
    .then((response) => response.json())
    .then((data) => {
      console.log("Camera status response:", data)
      if (data.success) {
        cameraOn = data.enabled
        console.log(`Camera status: ${cameraOn ? "enabled" : "disabled"}`)
        updateCameraUI()

        // If camera is enabled, make sure the stream is working
        if (cameraOn) {
          console.log("Camera is enabled, initializing stream...")
          // Give the camera a moment to initialize before showing the stream
          setTimeout(() => {
            updateCameraUI()
          }, 1000)
        }
      }
    })
    .catch((error) => {
      console.error("Error getting camera status:", error)
    })

  // Load keypad status
  fetch("/api/keypad/status")
    .then((response) => response.json())
    .then((data) => {
      console.log("Keypad status response:", data)
      if (data.success) {
        updateKeypadUI(data)
      }
    })
    .catch((error) => console.error("Error getting keypad status:", error))

  // Load gallery images
  loadGalleryImages()
}

// Update door UI
function updateDoorUI() {
  console.log("Updating door UI, locked:", doorLocked)
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

// Replace the updateCameraUI function with this updated version
function updateCameraUI() {
  console.log(`Updating camera UI, camera is ${cameraOn ? "on" : "off"}`)

  const toggleCameraBtn = document.getElementById("toggle-camera-btn")
  const captureBtn = document.getElementById("capture-btn")
  const cameraPlaceholder = document.getElementById("camera-placeholder")
  const cameraFeed = document.getElementById("camera-feed")

  if (toggleCameraBtn) {
    toggleCameraBtn.innerHTML = cameraOn
      ? '<i class="fas fa-video-slash"></i> <span>Turn Off Camera</span>'
      : '<i class="fas fa-video"></i> <span>Turn On Camera</span>'
  }

  if (captureBtn) {
    captureBtn.disabled = !cameraOn
    captureBtn.style.opacity = cameraOn ? "1" : "0.5"
  }

  if (cameraPlaceholder && cameraFeed) {
    if (cameraOn) {
      console.log("Camera is on, showing feed")
      cameraPlaceholder.classList.add("hidden")
      cameraFeed.classList.remove("hidden")

      // Use MJPEG streaming with error handling
      const streamUrl = `/api/camera/stream?t=${new Date().getTime()}`
      console.log(`Setting camera feed src to: ${streamUrl}`)

      cameraFeed.src = streamUrl
      cameraFeed.onerror = (e) => {
        console.error("Error loading camera feed", e)
        // If stream fails, fall back to placeholder
        if (cameraPlaceholder && cameraFeed) {
          cameraPlaceholder.classList.remove("hidden")
          cameraFeed.classList.add("hidden")
          showPopupNotification("Camera stream unavailable", "warning")
        }
      }

      cameraFeed.onload = () => {
        console.log("Camera feed loaded successfully")
      }
    } else {
      console.log("Camera is off, showing placeholder")
      cameraPlaceholder.classList.remove("hidden")
      cameraFeed.classList.add("hidden")
      cameraFeed.removeAttribute("src")
    }
  }
}

// Update keypad UI
function updateKeypadUI(status) {
  const keypadStatusIcon = document.getElementById("keypad-status-icon")
  const keypadStatusText = document.getElementById("keypad-status-text")
  const keypadInputLength = document.getElementById("keypad-input-length")
  const keypadFailedAttempts = document.getElementById("keypad-failed-attempts")
  const keypadLockStatus = document.getElementById("keypad-lock-status")
  const resetKeypadBtn = document.getElementById("reset-keypad-btn")

  if (keypadStatusIcon && keypadStatusText) {
    if (status.available && status.running) {
      keypadStatusIcon.className = "fas fa-keyboard"
      keypadStatusText.textContent = "Active"
      keypadStatusText.style.color = "#2ecc71"
    } else if (status.available && !status.running) {
      keypadStatusIcon.className = "fas fa-keyboard"
      keypadStatusText.textContent = "Stopped"
      keypadStatusText.style.color = "#f39c12"
    } else {
      keypadStatusIcon.className = "fas fa-keyboard"
      keypadStatusText.textContent = "Simulation Mode"
      keypadStatusText.style.color = "#3498db"
    }
  }

  if (keypadInputLength) {
    keypadInputLength.textContent = status.current_input_length || 0
  }

  if (keypadFailedAttempts) {
    keypadFailedAttempts.textContent = status.failed_attempts || 0
    keypadFailedAttempts.style.color = status.failed_attempts > 0 ? "#e74c3c" : "#333"
  }

  if (keypadLockStatus) {
    if (status.is_locked_out) {
      keypadLockStatus.textContent = "LOCKED OUT"
      keypadLockStatus.style.color = "#e74c3c"
      keypadLockStatus.style.fontWeight = "bold"
    } else {
      keypadLockStatus.textContent = "Ready"
      keypadLockStatus.style.color = "#2ecc71"
      keypadLockStatus.style.fontWeight = "normal"
    }
  }

  // Show reset button if there are failed attempts or locked out
  if (resetKeypadBtn) {
    if (status.failed_attempts > 0 || status.is_locked_out) {
      resetKeypadBtn.style.display = "block"
      resetKeypadBtn.onclick = resetKeypad
    } else {
      resetKeypadBtn.style.display = "none"
    }
  }
}

// Reset keypad function
function resetKeypad() {
  if (!confirm("Reset keypad state? This will clear failed attempts and unlock the keypad.")) {
    return
  }

  fetch("/api/keypad/reset", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showPopupNotification("Keypad reset successfully", "success")
        // Refresh keypad status
        setTimeout(() => {
          fetch("/api/keypad/status")
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                updateKeypadUI(data)
              }
            })
        }, 500)
      } else {
        showPopupNotification(data.message || "Failed to reset keypad", "error")
      }
    })
    .catch((error) => {
      console.error("Error resetting keypad:", error)
      showPopupNotification("Failed to reset keypad", "error")
    })
}

// Remove the refreshCameraImage function as it's no longer needed with MJPEG streaming

// Load gallery images
function loadGalleryImages() {
  console.log("Loading gallery images")
  const galleryItems = document.getElementById("gallery-items")
  if (!galleryItems) {
    console.warn("Gallery items element not found")
    return
  }

  fetch("/api/camera/gallery")
    .then((response) => response.json())
    .then((data) => {
      console.log("Gallery response:", data)
      if (data.success && data.images && data.images.length > 0) {
        galleryItems.innerHTML = ""

        // Display the most recent 5 images
        data.images.slice(0, 5).forEach((image) => {
          addImageToGallery(image)
        })
      } else {
        galleryItems.innerHTML = '<p class="text-muted">No images captured yet</p>'
      }
    })
    .catch((error) => {
      console.error("Error loading gallery images:", error)
      galleryItems.innerHTML = '<p class="text-danger">Error loading gallery</p>'
    })
}

// Add these new functions after the loadGalleryImages function

// Open gallery modal
function openGalleryModal() {
  console.log("Opening gallery modal")

  let galleryModal = document.getElementById("gallery-modal")

  // Create modal if it doesn't exist
  if (!galleryModal) {
    galleryModal = document.createElement("div")
    galleryModal.id = "gallery-modal"
    galleryModal.className = "modal"
    galleryModal.innerHTML = `
      <div class="modal-content gallery-modal-content">
        <div class="modal-header">
          <h3>Image Gallery</h3>
          <span class="close" id="gallery-close-btn">&times;</span>
        </div>
        <div class="modal-body">
          <div id="gallery-grid" class="gallery-grid">
            <div class="loading">Loading images...</div>
          </div>
        </div>
      </div>
    `
    document.body.appendChild(galleryModal)
  }

  // Always re-attach event listeners to ensure they work
  const closeBtn = galleryModal.querySelector("#gallery-close-btn")
  if (closeBtn) {
    // Remove any existing listeners first
    closeBtn.removeEventListener("click", closeGalleryModal)
    // Add the event listener
    closeBtn.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      console.log("Close button clicked")
      closeGalleryModal()
    })
  }

  // Close modal when clicking on backdrop
  galleryModal.removeEventListener("click", handleBackdropClick)
  galleryModal.addEventListener("click", handleBackdropClick)

  // Prevent modal content clicks from closing modal
  const modalContent = galleryModal.querySelector(".modal-content")
  if (modalContent) {
    modalContent.removeEventListener("click", handleContentClick)
    modalContent.addEventListener("click", handleContentClick)
  }

  // Load all gallery images
  loadAllGalleryImages()

  // Show modal
  galleryModal.classList.add("active")
  galleryModal.style.display = "flex"

  // Add escape key listener
  document.addEventListener("keydown", handleGalleryEscapeKey)
}

// Handle backdrop click
function handleBackdropClick(e) {
  if (e.target.id === "gallery-modal") {
    console.log("Backdrop clicked")
    closeGalleryModal()
  }
}

// Handle content click (prevent closing)
function handleContentClick(e) {
  e.stopPropagation()
}

// Close gallery modal
function closeGalleryModal() {
  console.log("Closing gallery modal")
  const galleryModal = document.getElementById("gallery-modal")
  if (galleryModal) {
    galleryModal.classList.remove("active")
    galleryModal.style.display = "none"
  }

  // Remove escape key listener
  document.removeEventListener("keydown", handleGalleryEscapeKey)
}

// Handle escape key for gallery modal
function handleGalleryEscapeKey(e) {
  if (e.key === "Escape") {
    closeGalleryModal()
  }
}

// Load all gallery images for the modal
function loadAllGalleryImages() {
  console.log("Loading all gallery images")
  const galleryGrid = document.getElementById("gallery-grid")
  if (!galleryGrid) {
    console.warn("Gallery grid element not found")
    return
  }

  // Clear existing content
  galleryGrid.innerHTML = '<div class="loading">Loading images...</div>'

  fetch("/api/camera/gallery?limit=100")
    .then((response) => response.json())
    .then((data) => {
      console.log("Gallery response:", data)
      galleryGrid.innerHTML = ""

      if (data.success && data.images && data.images.length > 0) {
        data.images.forEach((image) => {
          addImageToGalleryGrid(image, galleryGrid)
        })
      } else {
        galleryGrid.innerHTML = '<p class="text-muted">No images captured yet</p>'
      }
    })
    .catch((error) => {
      console.error("Error loading gallery images:", error)
      galleryGrid.innerHTML = '<p class="text-danger">Error loading gallery</p>'
    })
}

// Add image to gallery grid
function addImageToGalleryGrid(filename, galleryGrid) {
  const gridItem = document.createElement("div")
  gridItem.className = "gallery-grid-item"
  gridItem.dataset.filename = filename

  // Extract timestamp from filename (format: capture_YYYYMMDD_HHMMSS.jpg)
  let timestamp = ""
  const timestampMatch = filename.match(/capture_(\d{8})_(\d{6})/)
  if (timestampMatch) {
    const dateStr = timestampMatch[1]
    const timeStr = timestampMatch[2]

    const year = dateStr.substring(0, 4)
    const month = dateStr.substring(4, 6)
    const day = dateStr.substring(6, 8)

    const hour = timeStr.substring(0, 2)
    const minute = timeStr.substring(2, 4)

    timestamp = `${year}-${month}-${day} ${hour}:${minute}`
  }

  gridItem.innerHTML = `
    <img src="/static/captures/${filename}" alt="Captured image" loading="lazy">
    <div class="gallery-item-overlay">
      <div class="actions">
        <button class="btn-action btn-view" title="View Full Size">
          <i class="fas fa-eye"></i>
        </button>
        <button class="btn-action btn-delete" title="Delete Image">
          <i class="fas fa-trash"></i>
        </button>
      </div>
      <div class="timestamp">${timestamp}</div>
    </div>
  `

  // Add event listeners
  const viewBtn = gridItem.querySelector(".btn-view")
  if (viewBtn) {
    viewBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      showImageModal(filename)
    })
  }

  const deleteBtn = gridItem.querySelector(".btn-delete")
  if (deleteBtn) {
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      confirmDeleteImage(filename)
    })
  }

  // Click on image to view
  gridItem.addEventListener("click", () => {
    showImageModal(filename)
  })

  galleryGrid.appendChild(gridItem)
}

// Confirm delete image
function confirmDeleteImage(filename) {
  console.log("Confirming delete for:", filename)

  // Create confirmation dialog
  const backdrop = document.createElement("div")
  backdrop.className = "confirm-dialog-backdrop"

  const dialog = document.createElement("div")
  dialog.className = "confirm-dialog"
  dialog.innerHTML = `
    <h4>Delete Image</h4>
    <p>Are you sure you want to delete this image?</p>
    <div class="confirm-dialog-buttons">
      <button class="btn" id="cancel-delete">Cancel</button>
      <button class="btn btn-danger" id="confirm-delete">Delete</button>
    </div>
  `

  document.body.appendChild(backdrop)
  document.body.appendChild(dialog)

  // Add event listeners
  document.getElementById("cancel-delete").addEventListener("click", () => {
    document.body.removeChild(backdrop)
    document.body.removeChild(dialog)
  })

  document.getElementById("confirm-delete").addEventListener("click", () => {
    deleteImage(filename)
    document.body.removeChild(backdrop)
    document.body.removeChild(dialog)
  })
}

// Delete image
function deleteImage(filename) {
  console.log("Deleting image:", filename)

  fetch("/api/camera/delete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ filename }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Delete response:", data)
      if (data.success) {
        // Remove from gallery grid
        const gridItem = document.querySelector(`.gallery-grid-item[data-filename="${filename}"]`)
        if (gridItem && gridItem.parentNode) {
          gridItem.parentNode.removeChild(gridItem)
        }

        // Remove from gallery preview
        const galleryItems = document.getElementById("gallery-items")
        if (galleryItems) {
          const items = galleryItems.querySelectorAll(".gallery-item")
          items.forEach((item) => {
            const img = item.querySelector("img")
            if (img && img.src.includes(filename)) {
              item.parentNode.removeChild(item)
            }
          })
        }

        showPopupNotification("Image deleted successfully", "success")
      } else {
        showPopupNotification(data.message || "Failed to delete image", "error")
      }
    })
    .catch((error) => {
      console.error("Error deleting image:", error)
      showPopupNotification("Failed to delete image", "error")
    })
}

// Update the addImageToGallery function to include delete button
function addImageToGallery(filename) {
  const galleryItems = document.getElementById("gallery-items")
  if (!galleryItems) return

  const galleryItem = document.createElement("div")
  galleryItem.className = "gallery-item"
  galleryItem.dataset.filename = filename

  const img = document.createElement("img")
  img.src = `/static/captures/${filename}`
  img.alt = "Captured image"
  img.addEventListener("click", () => {
    // Show image in a modal or lightbox
    showImageModal(filename)
  })

  galleryItem.appendChild(img)
  galleryItems.prepend(galleryItem) // Add to the beginning (most recent first)

  // Limit to 5 images
  if (galleryItems.children.length > 5) {
    galleryItems.removeChild(galleryItems.lastChild)
  }
}

// Show image modal
function showImageModal(filename) {
  console.log("Opening image modal for:", filename)

  // Create modal if it doesn't exist
  let modal = document.getElementById("image-modal")
  if (!modal) {
    modal = document.createElement("div")
    modal.id = "image-modal"
    modal.className = "modal"

    const modalContent = document.createElement("div")
    modalContent.className = "modal-content image-modal-content"

    const closeBtn = document.createElement("span")
    closeBtn.className = "close"
    closeBtn.id = "image-close-btn"
    closeBtn.innerHTML = "&times;"

    const img = document.createElement("img")
    img.id = "modal-image"

    const caption = document.createElement("div")
    caption.className = "image-caption"
    caption.id = "modal-caption"

    modalContent.appendChild(closeBtn)
    modalContent.appendChild(img)
    modalContent.appendChild(caption)
    modal.appendChild(modalContent)
    document.body.appendChild(modal)
  }

  // Always re-attach event listeners
  const closeBtn = modal.querySelector("#image-close-btn")
  if (closeBtn) {
    closeBtn.removeEventListener("click", closeImageModal)
    closeBtn.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      console.log("Image modal close button clicked")
      closeImageModal()
    })
  }

  // Close modal when clicking outside the image
  modal.removeEventListener("click", handleImageBackdropClick)
  modal.addEventListener("click", handleImageBackdropClick)

  // Prevent modal content clicks from closing modal
  const modalContent = modal.querySelector(".modal-content")
  if (modalContent) {
    modalContent.removeEventListener("click", handleContentClick)
    modalContent.addEventListener("click", handleContentClick)
  }

  // Update modal content
  const modalImage = document.getElementById("modal-image")
  const modalCaption = document.getElementById("modal-caption")

  modalImage.src = `/static/captures/${filename}`

  // Extract timestamp from filename (format: capture_YYYYMMDD_HHMMSS.jpg)
  const timestampMatch = filename.match(/capture_(\d{8})_(\d{6})/)
  if (timestampMatch) {
    const dateStr = timestampMatch[1]
    const timeStr = timestampMatch[2]

    const year = dateStr.substring(0, 4)
    const month = dateStr.substring(4, 6)
    const day = dateStr.substring(6, 8)

    const hour = timeStr.substring(0, 2)
    const minute = timeStr.substring(2, 4)
    const second = timeStr.substring(4, 6)

    const formattedDate = `${year}-${month}-${day} ${hour}:${minute}:${second}`
    modalCaption.textContent = `Captured on: ${formattedDate}`
  } else {
    modalCaption.textContent = filename
  }

  // Show modal
  modal.classList.add("active")
  modal.style.display = "flex"

  // Add escape key listener for image modal
  document.addEventListener("keydown", handleImageEscapeKey)
}

// Handle image modal backdrop click
function handleImageBackdropClick(e) {
  if (e.target.id === "image-modal") {
    console.log("Image modal backdrop clicked")
    closeImageModal()
  }
}

// Close image modal
function closeImageModal() {
  console.log("Closing image modal")
  const modal = document.getElementById("image-modal")
  if (modal) {
    modal.classList.remove("active")
    modal.style.display = "none"
  }

  // Remove escape key listener
  document.removeEventListener("keydown", handleImageEscapeKey)
}

// Handle escape key for image modal
function handleImageEscapeKey(e) {
  if (e.key === "Escape") {
    closeImageModal()
  }
}

// Load recent activity
function loadRecentActivity() {
  console.log("Loading recent activity")
  const recentActivity = document.getElementById("recent-activity")

  if (recentActivity) {
    fetch("/api/logs")
      .then((response) => response.json())
      .then((data) => {
        console.log("Logs response:", data)
        const logs = data.logs || []
        recentActivity.innerHTML = ""

        if (logs.length === 0) {
          recentActivity.innerHTML = '<div class="activity-item">No recent activity</div>'
        } else {
          // Show only the 10 most recent logs
          logs.slice(0, 10).forEach((log) => {
            const activityItem = document.createElement("div")
            activityItem.className = "activity-item"

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
                if (log.status === "capture") {
                  icon = "fa-camera"
                  action = `Image captured`
                } else {
                  icon = "fa-video"
                  action = `Camera turned ${log.status}`
                }
                break
              case "fingerprint":
                icon = "fa-fingerprint"
                action = `Fingerprint ${log.status}`
                break
              default:
                icon = "fa-info-circle"
                action = `${log.action}: ${log.status}`
            }

            activityItem.innerHTML = `
              <div><i class="fas ${icon}"></i> ${action}</div>
              <div class="time">${log.timestamp}</div>
            `
            recentActivity.appendChild(activityItem)
          })
        }
      })
      .catch((error) => {
        console.error("Error loading recent activity:", error)
        recentActivity.innerHTML = '<div class="activity-item text-danger">Error loading activity</div>'
      })
  }

  // Also refresh keypad status
  fetch("/api/keypad/status")
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        updateKeypadUI(data)
      }
    })
    .catch((error) => console.error("Error refreshing keypad status:", error))
}

// Show popup notification
function showPopupNotification(message, type = "info") {
  console.log("Showing notification:", message, type)
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
  setTimeout(() => {
    notification.classList.add("show")
  }, 10)

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
      
      /* Image modal styles */
      .image-modal-content {
        max-width: 80%;
        max-height: 80%;
      }
      
      .image-modal-content img {
        width: 100%;
        max-height: 70vh;
        object-fit: contain;
      }
      
      .image-caption {
        padding: 10px;
        text-align: center;
        color: #333;
      }
    `
    document.head.appendChild(style)
  }
})()

console.log("Dashboard JavaScript file fully loaded")
