import streamlit as st

def inject_custom_css():
    """Inject custom CSS for styling and dark mode support."""
    st.markdown(
        """
        <style>
        /* Global Styles - Dark Blue Theme */
        .stApp {
            background-color: #001F3F; /* Dark Blue */
            color: #FFFFFF;
        }
        
        /* Title Style - Bright White */
        .custom-title {
            font-size: 1.8rem !important;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            color: #FFFFFF !important; /* Force White */
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }

        /* Widget Labels (Date Input, Text Area, etc.) */
        .stDateInput label, .stTextArea label, .stSelectbox label, .stTextInput label {
            color: #FFFFFF !important;
            font-weight: bold;
            font-size: 1.2rem !important; /* Increased font size */
        }
        
        /* Buttons */
        .stButton button {
            color: #000000 !important; /* Black text for visibility */
            background-color: #FFFFFF !important; /* White background */
            border: none;
            font-weight: bold;
            font-size: 1.2rem !important; /* Increased font size */
        }
        .stButton button:hover {
            background-color: #E0E0E0 !important;
            color: #000000 !important;
        }

        /* Card/Container Style */
        .news-card {
            padding: 1.5rem;
            border-radius: 10px;
            background-color: #003366; /* Slightly lighter blue for cards */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
            border: 1px solid #004080;
        }
        
        /* Text Colors in Card */
        .news-card h3 {
            color: #FFFFFF !important;
        }
        .news-card p {
            color: #E0E0E0 !important;
        }

        /* Mobile Optimization */
        @media (max-width: 768px) {
            .stButton button {
                width: 100%;
            }
        }
        
        /* Status Message Area (Normal Flow) */
        .status-area {
            margin-top: 10px;
            margin-bottom: 20px;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            text-align: center;
            color: #FFFFFF;
            font-size: 1.2rem !important; /* Increased font size */
            font-weight: bold;
        }
        
        /* Adjust Update Button Alignment */
        div[data-testid="column"] button {
            margin-top: 0px; 
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def inject_swipe_detection():
    """
    Inject JavaScript to detect swipe gestures and trigger keyboard events.
    Also listens for Arrow keys for Desktop navigation.
    Includes logic to HIDE the navigation buttons.
    """
    st.components.v1.html(
        """
        <script>
        // === Swipe & Keyboard Logic ===
        document.addEventListener('touchstart', handleTouchStart, false);
        document.addEventListener('touchmove', handleTouchMove, false);
        document.addEventListener('keydown', handleKeyDown, false);

        var xDown = null;                                                        
        var yDown = null;

        function handleTouchStart(evt) {
            const firstTouch = evt.touches[0];                                      
            xDown = firstTouch.clientX;                                      
            yDown = firstTouch.clientY;                                      
        };                                                

        function handleTouchMove(evt) {
            if ( ! xDown || ! yDown ) {
                return;
            }

            var xUp = evt.touches[0].clientX;                                    
            var yUp = evt.touches[0].clientY;

            var xDiff = xDown - xUp;
            var yDiff = yDown - yUp;

            if ( Math.abs( xDiff ) > Math.abs( yDiff ) ) {/*most significant*/
                if ( xDiff > 0 ) {
                    /* right swipe -> next */
                    sendMessageToStreamlit('next');
                } else {
                    /* left swipe -> prev */
                    sendMessageToStreamlit('prev');
                }                       
            }
            /* reset values */
            xDown = null;
            yDown = null;                                             
        };
        
        function handleKeyDown(e) {
            if (e.key === "ArrowRight") {
                sendMessageToStreamlit('next');
            } else if (e.key === "ArrowLeft") {
                sendMessageToStreamlit('prev');
            }
        }

        function sendMessageToStreamlit(action) {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (action === 'next' && (btn.innerText.includes("NextHidden") || btn.innerText.includes("下一則"))) {
                    btn.click();
                }
                if (action === 'prev' && (btn.innerText.includes("PrevHidden") || btn.innerText.includes("上一則"))) {
                    btn.click();
                }
            });
        }
        
        // === Hide Buttons Logic (Robust) ===
        function hideButtons() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText.includes("NextHidden") || btn.innerText.includes("PrevHidden")) {
                    // Hide the button container (usually the parent div of the button)
                    // or just the button itself.
                    btn.style.display = 'none';
                    // Also try to hide the parent column if it's the only thing there? 
                    // No, that might be risky. Just hiding the button is enough.
                }
            });
        }
        
        // Run immediately and periodically to catch re-renders
        hideButtons();
        setInterval(hideButtons, 500);
        </script>
        """,
        height=0,
    )

def inject_pwa_html():
    """Inject PWA manifest link and service worker registration."""
    st.components.v1.html(
        """
        <script>
        // Register service worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                // Try different paths for SW
                navigator.serviceWorker.register('/app/static/sw.js')
                    .then(function(registration) {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    })
                    .catch(function(err) {
                        console.log('ServiceWorker registration failed:', err);
                        // Fallback for older streamlit or different config
                        navigator.serviceWorker.register('/static/sw.js');
                    });
            });
        }
        
        // Inject manifest link into window.parent.document.head
        // This is necessary because st.components runs in an iframe
        const manifestLink = window.parent.document.createElement('link');
        manifestLink.rel = 'manifest';
        // Streamlit Cloud serves static files at /app/static/
        manifestLink.href = '/app/static/manifest.json';
        window.parent.document.head.appendChild(manifestLink);
        
        // Also inject meta tags for mobile
        const metaTheme = window.parent.document.createElement('meta');
        metaTheme.name = 'theme-color';
        metaTheme.content = '#001F3F';
        window.parent.document.head.appendChild(metaTheme);
        
        const metaApple = window.parent.document.createElement('meta');
        metaApple.name = 'apple-mobile-web-app-capable';
        metaApple.content = 'yes';
        window.parent.document.head.appendChild(metaApple);
        </script>
        """,
        height=0,
    )

def inject_pwa_detection():
    """
    Inject JavaScript to detect PWA/standalone mode and communicate back to Streamlit.
    Uses URL parameter manipulation to signal PWA mode to Streamlit.
    """
    st.components.v1.html(
        """
        <script>
        (function() {
            // Detect if running in PWA/standalone mode
            function isPWA() {
                // Method 1: Check display-mode media query (works for most browsers)
                const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
                
                // Method 2: iOS Safari fallback
                const isIOSStandalone = ('standalone' in window.navigator) && window.navigator.standalone;
                
                return isStandalone || isIOSStandalone;
            }
            
            const pwaMode = isPWA();
            console.log('PWA Detection - Is PWA mode:', pwaMode);
            
            // Store in localStorage for persistence
            localStorage.setItem('isPWA', pwaMode.toString());
            
            // If PWA mode detected and URL doesn't have the parameter yet, add it
            if (pwaMode) {
                const url = new URL(window.parent.location.href);
                if (!url.searchParams.has('pwa_mode')) {
                    console.log('Adding pwa_mode parameter to URL');
                    url.searchParams.set('pwa_mode', 'true');
                    window.parent.history.replaceState({}, '', url);
                }
            }
        })();
        </script>
        """,
        height=0,
    )
    
    # Check for PWA mode from URL parameter
    if "is_pwa" not in st.session_state:
        try:
            # Use st.query_params (new API)
            if hasattr(st, 'query_params'):
                params = st.query_params
                st.session_state.is_pwa = params.get('pwa_mode', 'false') == 'true'
            else:
                # Fallback to False if API not available
                st.session_state.is_pwa = False
        except Exception as e:
            # If any error, default to browser mode
            st.session_state.is_pwa = False

def is_pwa():
    """
    Check if the app is running in PWA/standalone mode.
    Returns True if in App/PWA mode, False if in Web browser mode.
    """
    return st.session_state.get("is_pwa", False)

def log_to_console(message):
    """
    Log a message to the browser console using JavaScript.
    """
    # Escape quotes to prevent JS errors
    safe_message = message.replace('"', '\\"').replace("'", "\\'")
    js_code = f"""
    <script>
    console.log("{safe_message}");
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

def inject_visibility_auto_fetch():
    """
    Inject JS to detect visibility and click the hidden 'StartAutoFetch' button.
    This ensures auto-fetch only happens when a user is actually viewing the page.
    """
    st.components.v1.html(
        """
        <script>
        function triggerFetch() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                // Find the specific button by its text content
                if (btn.innerText === "StartAutoFetch") {
                    btn.click();
                }
            });
        }

        function checkAndTrigger() {
            // Only trigger if visible
            if (document.visibilityState === 'visible') {
                triggerFetch();
            }
        }
        
        // Hide the button visuals immediately using JS (safer than CSS selectors)
        // We run this periodically or on load to ensure button is hidden
        function hideFetchButton() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText === "StartAutoFetch") {
                    btn.style.position = 'absolute';
                    btn.style.opacity = '0';
                    btn.style.height = '0';
                    btn.style.width = '0';
                    btn.style.padding = '0';
                    btn.style.margin = '0';
                    btn.style.overflow = 'hidden';
                    btn.setAttribute('tabindex', '-1'); // Remove from tab order
                }
            });
        }

        // Run on load
        window.addEventListener('load', function() {
            hideFetchButton();
            checkAndTrigger();
        });
        
        // Run on visibility change (for background tabs coming into focus)
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                checkAndTrigger();
            }
        });

        // Run immediately in case of race conditions
        hideFetchButton();
        checkAndTrigger();
        
        // Observer to hide button if it appears later (dynamically rendered)
        const observer = new MutationObserver(function(mutations) {
            hideFetchButton();
        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0
    )
