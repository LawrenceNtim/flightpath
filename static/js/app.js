// FlightPath Web Application JavaScript

// Global variables
let currentFlightData = null;
let chatHistory = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize chat
    initializeChat();
    
    // Check system health
    checkSystemHealth();
    
    console.log('FlightPath Web App initialized successfully');
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

// Flight Search Functions
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
            displayResults(result.recommendation, result.flight_data);
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

function displayResults(recommendation, flightData) {
    const resultsContent = document.getElementById('resultsContent');
    
    const html = `
        <div class="row">
            <div class="col-lg-8">
                <div class="recommendation-card">
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

function getScoreClass(score) {
    if (score >= 0.8) return 'score-excellent';
    if (score >= 0.6) return 'score-good';
    if (score >= 0.4) return 'score-average';
    return 'score-poor';
}

function formatAIInsights(insights) {
    // Convert line breaks to HTML and add basic formatting
    return insights.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
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

// Chat Functions
function toggleChat() {
    const chatWidget = document.getElementById('chatWidget');
    const toggleBtn = document.querySelector('.chat-toggle-btn');
    
    if (chatWidget.style.display === 'none' || chatWidget.style.display === '') {
        chatWidget.style.display = 'flex';
        toggleBtn.style.display = 'none';
    } else {
        chatWidget.style.display = 'none';
        toggleBtn.style.display = 'block';
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

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
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        }
    } catch (error) {
        removeTypingIndicator();
        addChatMessage('Network error. Please check your connection and try again.', 'ai');
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
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
    
    // Add to history
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

// Utility Functions
function showResults() {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    
    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function showNewSearch() {
    // Reset form
    document.getElementById('flightSearchForm').reset();
    
    // Hide results
    document.getElementById('resultsSection').style.display = 'none';
    
    // Clear current flight data
    currentFlightData = null;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'none';
}

function showError(message) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.className = 'toast-notification error';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 5000);
}

function showSuccess(message) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.className = 'toast-notification success';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const result = await response.json();
        
        if (!result.success) {
            console.warn('System health check failed:', result.error);
        }
    } catch (error) {
        console.error('Health check failed:', error);
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

// Inject toast styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);