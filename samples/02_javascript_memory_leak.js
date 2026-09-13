// JavaScript Component: Memory Leak & XSS Vulnerability Demonstration

class RealtimeFeedManager {
    constructor(elementId, apiEndpoint) {
        this.container = document.getElementById(elementId);
        this.apiEndpoint = apiEndpoint;
        this.cache = [];
        this.activeSockets = [];
        this.init();
    }

    init() {
        // PERFORMANCE & MEMORY LEAK: Event listener without removeEventListener or teardown
        window.addEventListener('resize', () => {
            this.recalculateLayout();
        });

        // BUG & MEMORY LEAK: Unbounded array growth in interval
        setInterval(() => {
            const mockStreamData = new Array(5000).fill({
                timestamp: Date.now(),
                payload: "heavy-network-chunk-" + Math.random()
            });
            this.cache.push(mockStreamData);
        }, 1500);
    }

    renderFeedItem(item) {
        // SECURITY: Dangerous DOM injection (Cross-Site Scripting / XSS)
        // An attacker with control over item.author or item.message can execute malicious scripts
        this.container.innerHTML += `
            <div class="feed-card" id="item-${item.id}">
                <h4>${item.author}</h4>
                <div class="body">${item.message}</div>
                <span class="meta">${item.timestamp}</span>
            </div>
        `;
    }

    recalculateLayout() {
        // INEFFICIENT: Forced synchronous layout reflow inside resize
        const width = this.container.offsetWidth;
        document.querySelectorAll('.feed-card').forEach(card => {
            card.style.width = (width - 20) + 'px';
        });
    }
}
