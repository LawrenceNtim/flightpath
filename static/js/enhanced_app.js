// Enhanced FlightPath Web Application JavaScript
// Features: Natural Language Processing, Voice Input, Context Awareness

// Global variables
let currentFlightData = null;
let chatHistory = [];
let recognition;
let isListening = false;
let parsedQuery = null;
let contextData = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeEnhancedApp();
});

function initializeEnhancedApp() {
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize chat
    initializeChat();
    
    // Initialize speech recognition
    initializeSpeechRecognition();
    
    // Initialize natural language processing
    initializeNLP();
    
    // Check system health
    checkSystemHealth();
    
    // Set up date constraints
    setupDateConstraints();
    
    console.log('Enhanced FlightPath App initialized successfully');
}

function initializeFormHandlers() {
    const form = document.getElementById('flightSearchForm');
    if (form) {
        form.addEventListener('submit', handleFlightSearch);
    }
}

function initializeChat() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', handleChatKeyPress);
    }
}

function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            isListening = true;
            document.getElementById('voiceStatus').style.display = 'block';
            document.getElementById('voiceButton').innerHTML = '<i class="fas fa-stop text-danger"></i>';
            document.getElementById('voiceButton').classList.add('active');
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('naturalSearchInput').value = transcript;
            processNaturalSearch();
        };
        
        recognition.onend = function() {
            isListening = false;
            document.getElementById('voiceStatus').style.display = 'none';
            document.getElementById('voiceButton').innerHTML = '<i class="fas fa-microphone"></i>';
            document.getElementById('voiceButton').classList.remove('active');
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            showError('Voice recognition error: ' + event.error);
            isListening = false;
            document.getElementById('voiceStatus').style.display = 'none';
            document.getElementById('voiceButton').innerHTML = '<i class="fas fa-microphone"></i>';
            document.getElementById('voiceButton').classList.remove('active');
        };
        
        // Add voice support indicator
        addVoiceSupportIndicator(true);
    } else {
        console.log('Speech recognition not supported');
        document.getElementById('voiceButton').style.display = 'none';
        addVoiceSupportIndicator(false);
    }
}

function initializeNLP() {
    // Set up natural language search input
    const nlpInput = document.getElementById('naturalSearchInput');
    if (nlpInput) {
        nlpInput.addEventListener('keypress', handleNaturalSearchKeyPress);
        nlpInput.addEventListener('input', handleNaturalSearchInput);
    }
}

function setupDateConstraints() {
    const today = new Date().toISOString().split('T')[0];
    const departureDate = document.getElementById('departure_date');
    const returnDate = document.getElementById('return_date');
    
    if (departureDate) {
        departureDate.min = today;
        departureDate.addEventListener('change', function() {
            if (returnDate) {
                returnDate.min = this.value;
            }
        });
    }
    
    if (returnDate) {
        returnDate.min = today;
    }
}

// Voice Input Functions
function toggleVoiceInput() {
    if (!recognition) {
        showError('Voice recognition not supported in this browser');
        return;
    }
    
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function addVoiceSupportIndicator(supported) {
    const indicator = document.createElement('span');
    indicator.className = `voice-support-indicator ${supported ? '' : 'voice-not-supported'}`;
    indicator.innerHTML = supported ? 
        '<i class="fas fa-check-circle"></i> Voice supported' : 
        '<i class="fas fa-times-circle"></i> Voice not supported';
    
    const voiceButton = document.getElementById('voiceButton');
    if (voiceButton && voiceButton.parentNode) {
        voiceButton.parentNode.appendChild(indicator);
    }
}

// Natural Language Processing Functions
function handleNaturalSearchKeyPress(event) {
    if (event.key === 'Enter') {
        processNaturalSearch();
    }
}

function handleNaturalSearchInput(event) {
    // Clear previous results when user types
    clearParsedResults();
}

async function processNaturalSearch() {
    const query = document.getElementById('naturalSearchInput').value.trim();
    
    if (!query) {
        showError('Please enter a search query');
        return;
    }
    
    // Show parsing status
    document.getElementById('parsingStatus').style.display = 'block';
    document.getElementById('parsedResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/parse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        
        if (result.success) {
            parsedQuery = result.parsed_query;
            displayParsedResults(result.parsed_query);
        } else {
            showError('Failed to parse your request: ' + result.error);
        }
    } catch (error) {
        showError('Error processing your request: ' + error.message);
    } finally {
        document.getElementById('parsingStatus').style.display = 'none';
    }
}

function displayParsedResults(parsed) {
    const content = document.getElementById('parsedContent');
    
    let html = '<div class="row">';
    
    // Origin and destination
    if (parsed.origin || parsed.destination) {
        html += '<div class="col-md-6 mb-2">';
        html += '<strong><i class="fas fa-route me-1"></i>Route:</strong> ';
        html += `${parsed.origin || '?'} → ${parsed.destination || '?'}`;
        html += '</div>';
    }
    
    // Departure date
    if (parsed.departure_date) {
        html += '<div class="col-md-6 mb-2">';
        html += '<strong><i class="fas fa-calendar me-1"></i>Departure:</strong> ';
        html += formatDate(parsed.departure_date);
        html += '</div>';
    }
    
    // Return date
    if (parsed.return_date) {
        html += '<div class="col-md-6 mb-2">';
        html += '<strong><i class="fas fa-calendar me-1"></i>Return:</strong> ';
        html += formatDate(parsed.return_date);
        html += '</div>';
    }
    
    // Passengers and class
    html += '<div class="col-md-6 mb-2">';
    html += '<strong><i class="fas fa-user me-1"></i>Passengers:</strong> ';
    html += parsed.passenger_count;
    html += '</div>';
    
    html += '<div class="col-md-6 mb-2">';
    html += '<strong><i class="fas fa-star me-1"></i>Class:</strong> ';
    html += capitalizeFirst(parsed.class_preference);
    html += '</div>';
    
    // Event type
    if (parsed.event_type) {
        html += '<div class="col-md-6 mb-2">';
        html += '<strong><i class="fas fa-calendar-check me-1"></i>Event:</strong> ';
        html += capitalizeFirst(parsed.event_type);
        html += '</div>';
    }
    
    // Urgency
    if (parsed.urgency && parsed.urgency !== 'low') {
        html += '<div class="col-md-6 mb-2">';
        html += '<strong><i class="fas fa-clock me-1"></i>Urgency:</strong> ';
        html += `<span class="badge bg-${getUrgencyColor(parsed.urgency)}">${parsed.urgency}</span>`;
        html += '</div>';
    }
    
    // Flexibility
    if (parsed.flexibility) {
        html += '<div class="col-12 mb-2">';
        html += '<strong><i class="fas fa-adjust me-1"></i>Flexibility:</strong> ';
        const flexItems = [];
        if (parsed.flexibility.dates_flexible) flexItems.push('Dates');
        if (parsed.flexibility.times_flexible) flexItems.push('Times');
        if (parsed.flexibility.airports_flexible) flexItems.push('Airports');
        if (parsed.flexibility.class_flexible) flexItems.push('Class');
        
        if (flexItems.length > 0) {
            html += `<span class="text-success">${flexItems.join(', ')}</span>`;
        } else {
            html += '<span class="text-muted">None specified</span>';
        }
        html += '</div>';
    }
    
    html += '</div>';
    
    // Time constraints
    if (parsed.time_constraints && Object.keys(parsed.time_constraints).length > 0) {
        html += '<div class="mt-2">';
        html += '<strong><i class="fas fa-clock me-1"></i>Time Constraints:</strong><br>';
        for (const [type, time] of Object.entries(parsed.time_constraints)) {
            html += `<small class="text-info">${capitalizeFirst(type)}: ${time}</small><br>`;
        }
        html += '</div>';
    }
    
    // Budget indicators
    if (parsed.budget_indicators) {
        const budget = parsed.budget_indicators;
        if (budget.budget_conscious || budget.luxury_preferred || budget.points_mentioned) {
            html += '<div class="mt-2">';
            html += '<strong><i class="fas fa-coins me-1"></i>Budget Preferences:</strong><br>';
            if (budget.budget_conscious) {
                html += '<small class="text-success">Budget-conscious</small><br>';
            }
            if (budget.luxury_preferred) {
                html += '<small class="text-warning">Luxury preferred</small><br>';
            }
            if (budget.points_mentioned) {
                html += '<small class="text-info">Points/miles mentioned</small><br>';
            }
            html += '</div>';
        }
    }
    
    // Confidence indicator
    const confidence = parsed.confidence || 0;
    const confidenceClass = getConfidenceClass(confidence);
    html += `<div class="mt-3">`;
    html += `<div class="progress" style="height: 8px;">`;
    html += `<div class="progress-bar bg-${confidenceClass}" style="width: ${confidence * 100}%"></div>`;
    html += `</div>`;
    html += `<small class="text-${confidenceClass}">Parsing confidence: ${(confidence * 100).toFixed(0)}%</small>`;
    html += `</div>`;
    
    content.innerHTML = html;
    document.getElementById('parsedResults').style.display = 'block';
}

// Context Functions
async function getContextInsights(flightData) {
    try {
        const response = await fetch('/api/context', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(flightData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            contextData = result.context;
            displayContextInsights(result.context);
        } else {
            console.error('Failed to get context:', result.error);
        }
    } catch (error) {
        console.error('Error getting context:', error);
    }
}

function displayContextInsights(context) {
    const contextContent = document.getElementById('contextContent');
    
    let html = '';
    
    // Context summary
    html += '<div class="context-summary">';
    html += '<h6><i class="fas fa-info-circle me-2"></i>Context Summary</h6>';
    html += '<div class="row">';
    html += `<div class="col-md-4">`;
    html += `<div class="context-metric">`;
    html += `<span>Insights:</span>`;
    html += `<span class="metric-value">${context.insights.length}</span>`;
    html += `</div>`;
    html += `</div>`;
    html += `<div class="col-md-4">`;
    html += `<div class="context-metric">`;
    html += `<span>Warnings:</span>`;
    html += `<span class="metric-value text-warning">${context.warnings.length}</span>`;
    html += `</div>`;
    html += `</div>`;
    html += `<div class="col-md-4">`;
    html += `<div class="context-metric">`;
    html += `<span>Confidence:</span>`;
    html += `<span class="metric-value">${(context.confidence * 100).toFixed(0)}%</span>`;
    html += `</div>`;
    html += `</div>`;
    html += '</div>';
    html += '</div>';
    
    // Display insights
    if (context.insights && context.insights.length > 0) {
        html += '<div class="row">';
        
        context.insights.forEach(insight => {
            const iconClass = getInsightIcon(insight.type);
            const badgeClass = getInsightBadgeClass(insight.type);
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="insight-card">
                        <div class="insight-header">
                            <i class="${iconClass} me-2"></i>
                            <span class="badge ${badgeClass}">${insight.type}</span>
                            <span class="insight-title">${insight.title}</span>
                        </div>
                        <p class="insight-description">${insight.description}</p>
                        <div class="d-flex justify-content-between">
                            <small class="text-muted">Impact: ${insight.impact}</small>
                            <small class="text-muted">Confidence: ${(insight.relevance_score * 100).toFixed(0)}%</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // Display warnings
    if (context.warnings && context.warnings.length > 0) {
        html += '<div class="alert alert-warning" role="alert">';
        html += '<h6><i class="fas fa-exclamation-triangle me-2"></i>Important Considerations</h6>';
        html += '<ul class="mb-0">';
        context.warnings.forEach(warning => {
            html += `<li>${warning}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Display suggestions
    if (context.suggestions && context.suggestions.length > 0) {
        html += '<div class="smart-suggestions">';
        html += '<h6><i class="fas fa-lightbulb me-2"></i>Smart Suggestions</h6>';
        context.suggestions.forEach(suggestion => {
            html += `<div class="suggestion-item">${suggestion}</div>`;
        });
        html += '</div>';
    }
    
    contextContent.innerHTML = html;
    document.getElementById('contextInsights').style.display = 'block';
}

// Enhanced Flight Search
async function executeSearch() {
    if (!parsedQuery) {
        showError('No parsed query available');
        return;
    }
    
    // Convert parsed query to flight data
    const flightData = {
        origin: parsedQuery.origin || '',
        destination: parsedQuery.destination || '',
        departure_date: parsedQuery.departure_date || '',
        return_date: parsedQuery.return_date || '',
        passenger_count: parsedQuery.passenger_count || 1,
        class_preference: parsedQuery.class_preference || 'economy',
        flexible_dates: parsedQuery.flexibility?.dates_flexible || false,
        budget_limit: null
    };
    
    // Validate essential fields
    if (!flightData.origin || !flightData.destination || !flightData.departure_date) {
        showError('Origin, destination, and departure date are required');
        return;
    }
    
    // Show loading
    showLoading();
    
    // Hide parsed results
    document.getElementById('parsedResults').style.display = 'none';
    
    try {
        // Get context insights first
        await getContextInsights(flightData);
        
        // Then get flight recommendations
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(flightData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentFlightData = result.flight_data;
            displayEnhancedResults(result.recommendation, result.flight_data);
            showResults();
        } else {
            showError('Flight search failed: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayEnhancedResults(recommendation, flightData) {
    const resultsContent = document.getElementById('resultsContent');
    
    const html = `
        <div class="row">
            <div class="col-lg-8">
                <div class="recommendation-card enhanced-results">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0">
                            <i class="fas fa-route me-2"></i>
                            ${recommendation.route}
                        </h5>
                        <span class="score-badge ${getScoreClass(recommendation.combined_score)}">
                            Score: ${recommendation.combined_score}
                        </span>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Points Required:</strong></p>
                            <h4 class="text-primary">${recommendation.points_value.toLocaleString()}</h4>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><strong>AI Confidence:</strong></p>
                            <div class="progress-container">
                                <div class="progress">
                                    <div class="progress-bar bg-success" style="width: ${recommendation.confidence * 100}%"></div>
                                </div>
                                <small class="text-muted">${(recommendation.confidence * 100).toFixed(1)}% confident</small>
                            </div>
                        </div>
                    </div>
                    
                    ${contextData ? `
                    <div class="context-summary">
                        <h6><i class="fas fa-brain me-2"></i>Context Analysis</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="context-metric">
                                    <span>Insights:</span>
                                    <span class="metric-value">${recommendation.context_insights || 0}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="context-metric">
                                    <span>Warnings:</span>
                                    <span class="metric-value text-warning">${recommendation.context_warnings || 0}</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="context-metric">
                                    <span>Context Score:</span>
                                    <span class="metric-value">${(recommendation.context_confidence * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="insight-box">
                        <h6><i class="fas fa-lightbulb me-2"></i>AI Strategic Insights</h6>
                        <div class="ai-insights">${formatAIInsights(recommendation.ai_insights)}</div>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-chart-bar me-2"></i>
                            Score Breakdown
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="score-item mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Rule-based Score</span>
                                <span class="fw-bold">${recommendation.rule_based_score}</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar bg-info" style="width: ${recommendation.rule_based_score * 100}%"></div>
                            </div>
                        </div>
                        
                        <div class="score-item mb-3">
                            <div class="d-flex justify-content-between">
                                <span>AI Score</span>
                                <span class="fw-bold">${recommendation.ai_score}</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar bg-success" style="width: ${recommendation.ai_score * 100}%"></div>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="score-item">
                            <div class="d-flex justify-content-between">
                                <span class="fw-bold">Combined Score</span>
                                <span class="fw-bold text-primary">${recommendation.combined_score}</span>
                            </div>
                            <div class="progress">
                                <div class="progress-bar bg-primary" style="width: ${recommendation.combined_score * 100}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-info-circle me-2"></i>
                            Flight Details
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="detail-item">
                            <strong>Route:</strong> ${flightData.origin} → ${flightData.destination}
                        </div>
                        <div class="detail-item">
                            <strong>Departure:</strong> ${formatDate(flightData.departure_date)}
                        </div>
                        ${flightData.return_date ? `<div class="detail-item"><strong>Return:</strong> ${formatDate(flightData.return_date)}</div>` : ''}
                        <div class="detail-item">
                            <strong>Class:</strong> ${capitalizeFirst(flightData.class_preference)}
                        </div>
                        <div class="detail-item">
                            <strong>Passengers:</strong> ${flightData.passenger_count}
                        </div>
                        ${parsedQuery && parsedQuery.event_type ? `<div class="detail-item"><strong>Event:</strong> ${capitalizeFirst(parsedQuery.event_type)}</div>` : ''}
                        ${parsedQuery && parsedQuery.urgency && parsedQuery.urgency !== 'low' ? `<div class="detail-item"><strong>Urgency:</strong> <span class="badge bg-${getUrgencyColor(parsedQuery.urgency)}">${parsedQuery.urgency}</span></div>` : ''}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="text-center">
                    <button class="btn btn-outline-primary me-2" onclick="showNewSearch()">
                        <i class="fas fa-search me-2"></i>New Search
                    </button>
                    <button class="btn btn-primary" onclick="openChatWithContext()">
                        <i class="fas fa-comments me-2"></i>Ask AI Assistant
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

// Enhanced Chat Functions
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Clear input
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                flight_context: currentFlightData
            })
        });
        
        const result = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (result.success) {
            addChatMessage(result.response, 'ai');
            
            // Show context indicator if context was provided
            if (result.context_provided) {
                addContextIndicator();
            }
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        }
    } catch (error) {
        removeTypingIndicator();
        addChatMessage('Network error. Please check your connection and try again.', 'ai');
    }
}

function addContextIndicator() {
    const chatBody = document.getElementById('chatBody');
    const indicator = document.createElement('div');
    indicator.className = 'chat-context-indicator';
    indicator.innerHTML = '<i class="fas fa-info-circle me-2"></i>Response includes context about your flight search';
    chatBody.appendChild(indicator);
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Utility Functions
function clearParsedResults() {
    document.getElementById('parsedResults').style.display = 'none';
    parsedQuery = null;
}

function useExampleQuery(element) {
    const query = element.textContent.replace(/"/g, '').trim();
    document.getElementById('naturalSearchInput').value = query;
    processNaturalSearch();
}

function getScoreClass(score) {
    if (score >= 0.8) return 'score-excellent';
    if (score >= 0.6) return 'score-good';
    if (score >= 0.4) return 'score-average';
    return 'score-poor';
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.5) return 'warning';
    return 'danger';
}

function getUrgencyColor(urgency) {
    switch (urgency) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        default: return 'info';
    }
}

function getInsightIcon(type) {
    const icons = {
        'warning': 'fas fa-exclamation-triangle text-warning',
        'info': 'fas fa-info-circle text-info',
        'suggestion': 'fas fa-lightbulb text-success',
        'tip': 'fas fa-star text-primary'
    };
    return icons[type] || 'fas fa-info-circle';
}

function getInsightBadgeClass(type) {
    const classes = {
        'warning': 'bg-warning',
        'info': 'bg-info',
        'suggestion': 'bg-success',
        'tip': 'bg-primary'
    };
    return classes[type] || 'bg-secondary';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1).replace('_', ' ');
}

function formatAIInsights(insights) {
    return insights.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Traditional search form handling
async function handleFlightSearch(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const searchData = {
        origin: formData.get('origin'),
        destination: formData.get('destination'),
        departure_date: formData.get('departure_date'),
        return_date: formData.get('return_date'),
        passenger_count: formData.get('passenger_count'),
        class_preference: formData.get('class_preference'),
        budget_limit: formData.get('budget_limit'),
        flexible_dates: formData.get('flexible_dates') === 'on'
    };
    
    // Validate form
    if (!validateSearchForm(searchData)) {
        return;
    }
    
    // Show loading
    showLoading();
    
    try {
        // Get context insights first
        await getContextInsights(searchData);
        
        // Then get flight recommendations
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentFlightData = result.flight_data;
            displayEnhancedResults(result.recommendation, result.flight_data);
            showResults();
        } else {
            showError('Flight search failed: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function validateSearchForm(data) {
    if (!data.origin || !data.destination) {
        showError('Please enter both origin and destination airports');
        return false;
    }
    
    if (!data.departure_date) {
        showError('Please select a departure date');
        return false;
    }
    
    if (data.origin.toUpperCase() === data.destination.toUpperCase()) {
        showError('Origin and destination cannot be the same');
        return false;
    }
    
    return true;
}

// Enhanced system health check
async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const result = await response.json();
        
        if (!result.success) {
            console.warn('System health check failed:', result.health);
            showError('Some system components may not be fully operational');
        } else {
            console.log('System health check passed');
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Existing utility functions (showLoading, hideLoading, showError, etc.)
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'none';
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification error';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 5000);
}

function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification success';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

function showResults() {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function showNewSearch() {
    document.getElementById('flightSearchForm').reset();
    document.getElementById('naturalSearchInput').value = '';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('contextInsights').style.display = 'none';
    clearParsedResults();
    currentFlightData = null;
    contextData = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleChat() {
    const chatWidget = document.getElementById('chatWidget');
    const toggleBtn = document.querySelector('.chat-toggle-btn');
    
    if (chatWidget.style.display === 'none' || chatWidget.style.display === '') {
        chatWidget.style.display = 'flex';
        chatWidget.classList.add('enhanced');
        toggleBtn.style.display = 'none';
    } else {
        chatWidget.style.display = 'none';
        chatWidget.classList.remove('enhanced');
        toggleBtn.style.display = 'block';
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function addChatMessage(message, sender) {
    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
    const content = `
        <div class="message-content">
            <i class="${icon} me-2"></i>
            ${message}
        </div>
    `;
    
    messageDiv.innerHTML = content;
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    
    chatHistory.push({ message, sender, timestamp: new Date() });
}

function showTypingIndicator() {
    const chatBody = document.getElementById('chatBody');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message ai-message typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-robot me-2"></i>
            <span class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </span>
        </div>
    `;
    
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function openChatWithContext() {
    toggleChat();
    
    if (currentFlightData) {
        const contextMessage = `I'm looking at a flight from ${currentFlightData.origin} to ${currentFlightData.destination} on ${currentFlightData.departure_date}. Can you help me optimize this booking?`;
        
        setTimeout(() => {
            document.getElementById('chatInput').value = contextMessage;
            document.getElementById('chatInput').focus();
        }, 500);
    }
}

// Add CSS for toast notifications
const toastStyles = `
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .toast-notification.show {
        transform: translateX(0);
    }
    
    .toast-notification.error {
        background: linear-gradient(135deg, #dc3545, #c82333);
    }
    
    .toast-notification.success {
        background: linear-gradient(135deg, #28a745, #218838);
    }
    
    .typing-dots {
        display: inline-block;
    }
    
    .typing-dots span {
        display: inline-block;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #999;
        margin: 0 1px;
        animation: typing 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);