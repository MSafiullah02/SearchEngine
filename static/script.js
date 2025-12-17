const searchForm = document.getElementById("searchForm")
const searchInput = document.getElementById("searchInput")
const loadingIndicator = document.getElementById("loadingIndicator")
const resultsInfo = document.getElementById("resultsInfo")
const resultsContainer = document.getElementById("results")
const errorMessage = document.getElementById("errorMessage")
const resultCount = document.getElementById("resultCount")
const searchQuery = document.getElementById("searchQuery")
const themeToggle = document.getElementById("themeToggle")
const pagination = document.getElementById("pagination")
const autocompleteDropdown = document.getElementById("autocompleteDropdown")

// Load saved theme preference
const savedTheme = localStorage.getItem("theme")
if (savedTheme === "dark") {
  document.body.classList.add("dark-mode")
}

themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode")
  const isDark = document.body.classList.contains("dark-mode")
  localStorage.setItem("theme", isDark ? "dark" : "light")
})

let allResults = []
let currentPage = 1
const resultsPerPage = 20

let autocompleteTimeout = null
let selectedSuggestionIndex = -1

function getSearchHistory() {
  const history = localStorage.getItem("searchHistory")
  return history ? JSON.parse(history) : []
}

function saveToHistory(query) {
  let history = getSearchHistory()
  // Remove duplicate if exists
  history = history.filter((item) => item !== query)
  // Add to beginning
  history.unshift(query)
  // Keep only last 10 searches
  history = history.slice(0, 10)
  localStorage.setItem("searchHistory", JSON.stringify(history))
}

searchInput.addEventListener("input", async (e) => {
  const query = e.target.value.trim()

  // Clear previous timeout
  if (autocompleteTimeout) {
    clearTimeout(autocompleteTimeout)
  }

  // Hide dropdown if query is empty
  if (!query) {
    hideAutocomplete()
    return
  }

  const historyMatches = getSearchHistory()
    .filter((item) => item.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 3) // Max 3 history items

  // Debounce API calls - wait 200ms after user stops typing
  autocompleteTimeout = setTimeout(async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/autocomplete?query=${encodeURIComponent(query)}`)

      if (!response.ok) {
        throw new Error("Autocomplete failed")
      }

      const data = await response.json()

      const lexiconSuggestions = data.suggestions || []
      const combinedSuggestions = {
        history: historyMatches,
        lexicon: lexiconSuggestions.slice(0, 5), // Max 5 lexicon items
      }

      if (historyMatches.length > 0 || lexiconSuggestions.length > 0) {
        displayAutocomplete(combinedSuggestions, query)
      } else {
        hideAutocomplete()
      }
    } catch (error) {
      console.error("[v0] Autocomplete error:", error)
      if (historyMatches.length > 0) {
        displayAutocomplete({ history: historyMatches, lexicon: [] }, query)
      } else {
        hideAutocomplete()
      }
    }
  }, 200)
})

searchInput.addEventListener("keydown", (e) => {
  const items = autocompleteDropdown.querySelectorAll(".autocomplete-item")

  if (!items.length) return

  if (e.key === "ArrowDown") {
    e.preventDefault()
    selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, items.length - 1)
    updateSelectedSuggestion(items)
  } else if (e.key === "ArrowUp") {
    e.preventDefault()
    selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1)
    updateSelectedSuggestion(items)
  } else if (e.key === "Enter" && selectedSuggestionIndex >= 0) {
    e.preventDefault()
    items[selectedSuggestionIndex].click()
  } else if (e.key === "Escape") {
    hideAutocomplete()
  }
})

document.addEventListener("click", (e) => {
  if (!searchInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
    hideAutocomplete()
  }
})

function displayAutocomplete(suggestions, query) {
  selectedSuggestionIndex = -1
  const queryLower = query.toLowerCase()
  let html = ""

  // Display history suggestions
  if (suggestions.history && suggestions.history.length > 0) {
    html += '<div class="autocomplete-section-title">Recent Searches</div>'
    suggestions.history.forEach((suggestion) => {
      const index = suggestion.toLowerCase().indexOf(queryLower)
      let displayText = suggestion

      if (index !== -1) {
        const before = suggestion.slice(0, index)
        const match = suggestion.slice(index, index + query.length)
        const after = suggestion.slice(index + query.length)
        displayText = `${escapeHtml(before)}<strong>${escapeHtml(match)}</strong>${escapeHtml(after)}`
      } else {
        displayText = escapeHtml(suggestion)
      }

      html += `<div class="autocomplete-item history-item" data-suggestion="${escapeHtml(suggestion)}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        ${displayText}
      </div>`
    })
  }

  // Display lexicon suggestions
  if (suggestions.lexicon && suggestions.lexicon.length > 0) {
    if (html) html += '<div class="autocomplete-section-title">Suggestions</div>'

    suggestions.lexicon.forEach((suggestion) => {
      const index = suggestion.toLowerCase().indexOf(queryLower)
      let displayText = suggestion

      if (index !== -1) {
        const before = suggestion.slice(0, index)
        const match = suggestion.slice(index, index + query.length)
        const after = suggestion.slice(index + query.length)
        displayText = `${escapeHtml(before)}<strong>${escapeHtml(match)}</strong>${escapeHtml(after)}`
      } else {
        displayText = escapeHtml(suggestion)
      }

      html += `<div class="autocomplete-item" data-suggestion="${escapeHtml(suggestion)}">${displayText}</div>`
    })
  }

  autocompleteDropdown.innerHTML = html

  // Add click handlers to suggestions
  autocompleteDropdown.querySelectorAll(".autocomplete-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()

      const suggestion = item.getAttribute("data-suggestion")
      searchInput.value = suggestion
      hideAutocomplete()

      performSearch(suggestion)
    })
  })

  autocompleteDropdown.classList.add("active")
}

function hideAutocomplete() {
  autocompleteDropdown.classList.remove("active")
  autocompleteDropdown.innerHTML = ""
  selectedSuggestionIndex = -1
}

function updateSelectedSuggestion(items) {
  items.forEach((item, index) => {
    if (index === selectedSuggestionIndex) {
      item.classList.add("selected")
      item.scrollIntoView({ block: "nearest" })
    } else {
      item.classList.remove("selected")
    }
  })

  // Update input with selected suggestion
  if (selectedSuggestionIndex >= 0) {
    const selectedText = items[selectedSuggestionIndex].getAttribute("data-suggestion")
    searchInput.value = selectedText
  }
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault()
  const query = searchInput.value.trim()

  if (!query) return

  performSearch(query)
})

async function performSearch(query) {
  saveToHistory(query)
  hideAutocomplete()

  // Show loading, hide results
  loadingIndicator.style.display = "block"
  resultsInfo.style.display = "none"
  resultsContainer.innerHTML = ""
  errorMessage.style.display = "none"
  pagination.style.display = "none"

  try {
    console.log("[v0] Sending search request for query:", query)

    const response = await fetch("http://localhost:5000/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    })

    console.log("[v0] Response status:", response.status)

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      console.log("[v0] Error response:", errorData)
      throw new Error(errorData?.error || "Search failed")
    }

    const data = await response.json()
    console.log("[v0] Search results:", data)

    // Hide loading
    loadingIndicator.style.display = "none"

    if (data.results && data.results.length > 0) {
      allResults = data.results
      currentPage = 1

      // Show results info
      resultsInfo.style.display = "block"
      resultCount.textContent = data.total
      searchQuery.textContent = data.query

      // Display paginated results
      displayPaginatedResults()
    } else {
      resultsContainer.innerHTML = `
                <div style="text-align: center; padding: 3rem; background: white; border-radius: 12px;">
                    <h3 style="color: #666; margin-bottom: 0.5rem;">No results found</h3>
                    <p style="color: #999;">Try different keywords or check your spelling</p>
                </div>
            `
    }
  } catch (error) {
    console.error("[v0] Search error:", error)
    loadingIndicator.style.display = "none"
    errorMessage.textContent = `An error occurred while searching: ${error.message}. Please check the console for details.`
    errorMessage.style.display = "block"
  }
}

function displayPaginatedResults() {
  const totalPages = Math.ceil(allResults.length / resultsPerPage)
  const startIndex = (currentPage - 1) * resultsPerPage
  const endIndex = startIndex + resultsPerPage
  const currentResults = allResults.slice(startIndex, endIndex)

  displayResults(currentResults)

  if (totalPages > 1) {
    renderPagination(totalPages)
    pagination.style.display = "flex"
  } else {
    pagination.style.display = "none"
  }

  // Scroll to top of results
  resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" })
}

function renderPagination(totalPages) {
  const maxButtons = 7
  const buttons = []

  // Previous button
  buttons.push(`
    <button class="pagination-button" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? "disabled" : ""}>
      ← Previous
    </button>
  `)

  // Page buttons
  if (totalPages <= maxButtons) {
    // Show all pages
    for (let i = 1; i <= totalPages; i++) {
      buttons.push(`
        <button class="pagination-button ${i === currentPage ? "active" : ""}" onclick="goToPage(${i})">
          ${i}
        </button>
      `)
    }
  } else {
    // Show first page
    buttons.push(`
      <button class="pagination-button ${1 === currentPage ? "active" : ""}" onclick="goToPage(1)">
        1
      </button>
    `)

    // Show ellipsis or nearby pages
    if (currentPage > 3) {
      buttons.push(`<span class="pagination-info">...</span>`)
    }

    // Show current page and neighbors
    const start = Math.max(2, currentPage - 1)
    const end = Math.min(totalPages - 1, currentPage + 1)

    for (let i = start; i <= end; i++) {
      buttons.push(`
        <button class="pagination-button ${i === currentPage ? "active" : ""}" onclick="goToPage(${i})">
          ${i}
        </button>
      `)
    }

    // Show ellipsis or nearby pages
    if (currentPage < totalPages - 2) {
      buttons.push(`<span class="pagination-info">...</span>`)
    }

    // Show last page
    buttons.push(`
      <button class="pagination-button ${totalPages === currentPage ? "active" : ""}" onclick="goToPage(${totalPages})">
        ${totalPages}
      </button>
    `)
  }

  // Next button
  buttons.push(`
    <button class="pagination-button" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? "disabled" : ""}>
      Next →
    </button>
  `)

  pagination.innerHTML = buttons.join("")
}

function goToPage(page) {
  currentPage = page
  displayPaginatedResults()
}

function displayResults(results) {
  resultsContainer.innerHTML = results
    .map(
      (result) => `
        <a href="${result.url}" target="_blank" class="result-card">
            <div class="result-header">
                <div style="flex: 1;">
                    <h2 class="result-title">${escapeHtml(result.title)}</h2>
                    <p class="result-authors">${escapeHtml(result.authors)}</p>
                </div>
                <span class="result-score">Score: ${Number.parseFloat(result.score).toFixed(2)}</span>
            </div>
            ${result.abstract ? `<p class="result-abstract">${escapeHtml(result.abstract)}</p>` : ""}
            <div class="result-footer">
                <span class="result-id">${escapeHtml(result.id)}</span>
                <span class="open-link">
                    Open document
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </span>
            </div>
        </a>
    `,
    )
    .join("")
}

function escapeHtml(text) {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}

