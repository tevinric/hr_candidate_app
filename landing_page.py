import streamlit as st
from auth import AuthManager, init_auth_session_state
from typing import Dict

def show_landing_page():
    """Display the landing page with Microsoft authentication"""
    # Initialize auth session state
    init_auth_session_state()
    
    # Custom CSS for professional landing page
    st.markdown("""
    <style>
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        /* Hide Streamlit default elements */
        .stApp > header {visibility: hidden;}
        .stApp > div > div > div > div > section > div {padding-top: 0rem;}
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh;
        }
        
        /* Hide all default streamlit content */
        .main .block-container {
            padding: 0;
            max-width: none;
            margin: 0;
            height: 100vh;
        }
        
        /* Main container */
        .landing-container {
            min-height: 100vh;
            display: grid;
            grid-template-columns: 1fr 480px 1fr;
            gap: 2rem;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #f8fafc;
            align-items: center;
        }
        
        /* Side columns (left and right) */
        .side-column {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        
        /* Center column */
        .center-column {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        
        /* Main card */
        .main-card {
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 6px rgba(0,0,0,0.04);
            overflow: hidden;
            width: 100%;
            border: 1px solid #e2e8f0;
            position: relative;
        }
        
        /* Header section */
        .header-section {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            color: #2d3748;
            padding: 3rem 2rem 2.5rem 2rem;
            text-align: center;
            position: relative;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .header-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="%232d3748" opacity="0.02"/><circle cx="75" cy="75" r="1" fill="%232d3748" opacity="0.02"/><circle cx="50" cy="10" r="0.5" fill="%232d3748" opacity="0.01"/><circle cx="90" cy="40" r="0.5" fill="%232d3748" opacity="0.01"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            pointer-events: none;
        }
        
        /* Logo */
        .logo {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #2b6cb0 0%, #3182ce 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem auto;
            box-shadow: 0 4px 16px rgba(43, 108, 176, 0.15);
            position: relative;
            z-index: 1;
        }
        
        .logo-icon {
            font-size: 2rem;
            color: white;
        }
        
        /* Typography */
        .main-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }
        
        .subtitle {
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 400;
            margin: 0;
            position: relative;
            z-index: 1;
        }
        
        /* Content section */
        .content-section {
            padding: 2.5rem 2rem;
            background: #ffffff;
        }
        
        /* Welcome text */
        .welcome-text {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .welcome-title {
            color: #2d3748;
            font-size: 1.4rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
        }
        
        .welcome-description {
            color: #718096;
            font-size: 0.95rem;
            line-height: 1.5;
            margin: 0;
        }
        
        /* Login button */
        .login-button-container {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        .login-button {
            background-color: lightblue;
            color: white;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            transition: background-color 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            width: 100%;
            max-width: 300px;
            position: relative;
            overflow: hidden;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .login-button:hover {
            background-color: darkblue;
            color: white;
        }
        
        .login-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
            transition: left 0.5s;
        }
        
        .login-button:hover::before {
            left: 100%;
        }
        
        .login-button:hover {
            background: linear-gradient(135deg, #153e75 0%, #2a4b7c 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(26, 54, 93, 0.35);
            color: #ffffff;
            text-decoration: none;
        }
        
        .login-button:active {
            transform: translateY(0);
        }
        
        /* Microsoft icon */
        .ms-icon {
            margin-right: 0.75rem;
            font-size: 1.2rem;
            position: relative;
            z-index: 1;
            filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.1));
        }
        
        .button-text {
            position: relative;
            z-index: 1;
            font-weight: 600;
            letter-spacing: 0.025em;
        }
        
        /* Security badge */
        .security-badge {
            display: inline-flex;
            align-items: center;
            background: #f7fafc;
            color: #4a5568;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            border: 1px solid #e2e8f0;
            justify-content: center;
        }
        
        .security-icon {
            margin-right: 0.5rem;
            color: #38a169;
        }
        
        /* Message cards */
        .message-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            margin: 1rem 0;
        }
        
        /* Error styling */
        .error-message {
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            border: 1px solid #fc8181;
            border-left: 4px solid #e53e3e;
            border-radius: 12px;
            padding: 1.5rem;
            color: #c53030;
        }
        
        .error-message h3 {
            margin: 0 0 1rem 0;
            color: #c53030;
            font-weight: 600;
        }
        
        /* Success styling */
        .success-message {
            background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
            border: 1px solid #68d391;
            border-left: 4px solid #38a169;
            border-radius: 12px;
            padding: 1.5rem;
            color: #2f855a;
        }
        
        .success-message h3 {
            margin: 0 0 1rem 0;
            color: #2f855a;
            font-weight: 600;
        }
        
        /* Info styling */
        .info-message {
            background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
            border: 1px solid #63b3ed;
            border-left: 4px solid #3182ce;
            border-radius: 12px;
            padding: 1.5rem;
            color: #2c5282;
        }
        
        .info-message h3 {
            margin: 0 0 1rem 0;
            color: #2c5282;
            font-weight: 600;
        }
        
        /* Footer */
        .footer {
            background: #f8fafc;
            color: #718096;
            text-align: center;
            padding: 1.5rem 2rem;
            font-size: 0.85rem;
            border-top: 1px solid #e2e8f0;
        }
        
        /* Responsive design */
        @media (max-width: 1024px) {
            .landing-container {
                grid-template-columns: 1fr 450px 1fr;
                gap: 1.5rem;
                padding: 1.5rem;
            }
        }
        
        @media (max-width: 768px) {
            .landing-container {
                grid-template-columns: 1fr;
                gap: 0;
                padding: 1rem;
            }
            
            .side-column {
                display: none;
            }
            
            .center-column {
                grid-column: 1;
            }
            
            .header-section {
                padding: 2rem 1.5rem;
            }
            
            .main-title {
                font-size: 1.6rem;
            }
            
            .content-section {
                padding: 2rem 1.5rem;
            }
            
            .main-card {
                margin: 0;
                max-width: 100%;
            }
        }
        
        @media (max-height: 600px) {
            .landing-container {
                align-items: flex-start;
                padding-top: 2rem;
            }
        }
        
        @media (max-width: 480px) {
            .landing-container {
                padding: 0.5rem;
            }
            
            .main-card {
                border-radius: 8px;
            }
            
            .header-section {
                padding: 1.5rem 1rem;
            }
            
            .content-section {
                padding: 1.5rem 1rem;
            }
        }
        
        /* Loading animation */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3182ce;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Check for authentication callback
    query_params = st.query_params
    
    # Create the main container structure
    st.markdown("""
    <div class="landing-container">
        <div class="side-column">
            <!-- Left column - empty for spacing -->
        </div>
        <div class="center-column">
    """, unsafe_allow_html=True)
    
    # Handle different states
    if 'code' in query_params:
        show_processing_card()
        handle_auth_callback(query_params['code'])
    elif 'error' in query_params:
        show_error_card(query_params.get('error', 'Unknown error'))
    else:
        show_main_card()
    
    # Close the container
    st.markdown("""
        </div>
        <div class="side-column">
            <!-- Right column - empty for spacing -->
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_main_card():
    """Show the main login card"""
    auth_manager = st.session_state.auth_manager
    
    if not auth_manager.is_configured():
        st.markdown("""
        <div class="main-card">
            <div class="header-section">
                <div class="logo">
                    <div class="logo-icon">⚙️</div>
                </div>
                <h1 class="main-title">Configuration Required</h1>
                <p class="subtitle">System Setup Needed</p>
            </div>
            <div class="content-section">
                <div class="error-message">
                    <h3>🔧 Configuration Required</h3>
                    <p>Microsoft Entra authentication is not properly configured. Please contact your administrator to complete the system setup.</p>
                </div>
            </div>
            <div class="footer">
                © 2024 Key Talent Solutions - Secure Enterprise HR Management
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get the auth URL
    auth_url = auth_manager.get_auth_url()
    
    if auth_url:
        # Show the main login card
            
            # Load and encode the logo image
            import base64
            import os
            from pathlib import Path
            
            # Get the path to the logo image
            logo_path = Path(os.path.join("static", "kts-logo.png"))
            
            # Check if the logo exists, otherwise fallback to text
            if logo_path.exists():
                with open(logo_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode()
                logo_html = f'<img src="data:image/png;base64,{encoded_image}" alt="Key Talent Solutions Logo" style="width:70px; height:70px; border-radius:50%; object-fit:cover; display:block; margin:0 auto 1.5rem auto;">'
            else:
                logo_html = '<div class="logo-icon">KTS</div>'
                
            st.markdown(f"""
            <div class="main-card">
                <div class="header-section">
                <div class="logo" style="background: none; box-shadow: none;">
                    {logo_html}
                </div>
                <h1 class="main-title">Key Talent Solutions</h1>
                </div>
            <div class="content-section">
            <div class="welcome-text">
                <div class="security-badge">
                <span class="security-icon">🔒</span>
                Secured by Microsoft Entra ID
                </div>
            </div>
            <div class="login-button-container">
                <a href="{auth_url}" class="login-button" target="_self">
                <span class="ms-icon">⊞</span>
                <span class="button-text">Sign in with Microsoft</span>
                </a>
            </div>
            </div>
            <div class="footer">
            © 2025 Key Talent Solutions
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-card">
            <div class="header-section">
                <div class="logo">
                    <div class="logo-icon">⚠️</div>
                </div>
                <h1 class="main-title">Configuration Error</h1>
                <p class="subtitle">Unable to Initialize Authentication</p>
            </div>
            <div class="content-section">
                <div class="error-message">
                    <h3>🔧 Configuration Error</h3>
                    <p>Unable to generate authentication URL. Please check the application configuration and try again.</p>
                </div>
            </div>
            <div class="footer">
                © 2024 Key Talent Solutions - Secure Enterprise HR Management
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_processing_card():
    """Show processing card during authentication"""
    st.markdown("""
    <div class="main-card">
        <div class="header-section">
            <div class="logo">
                <div class="logo-icon">🎯</div>
            </div>
            <h1 class="main-title">Key Talent Solutions</h1>
            <p class="subtitle">Processing Authentication</p>
        </div>
        <div class="content-section">
            <div class="info-message">
                <h3><span class="loading-spinner"></span>Verifying Credentials</h3>
                <p>Please wait while we securely authenticate your account with Microsoft Entra ID...</p>
            </div>
        </div>
        <div class="footer">
            © 2024 Key Talent Solutions - Secure Enterprise HR Management
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_error_card(error_message: str):
    """Show error card"""
    redirect_uri = st.session_state.auth_manager.redirect_uri
    
    st.markdown(f"""
    <div class="main-card">
        <div class="header-section">
            <div class="logo">
                <div class="logo-icon">⚠️</div>
            </div>
            <h1 class="main-title">Authentication Error</h1>
            <p class="subtitle">Sign-in Issue Encountered</p>
        </div>
        <div class="content-section">
            <div class="error-message">
                <h3>🚫 Authentication Failed</h3>
                <p><strong>Error:</strong> {error_message}</p>
                <p>Please try signing in again. If the problem persists, contact your system administrator.</p>
            </div>
            <div class="login-button-container">
                <a href="{redirect_uri}" class="login-button" target="_self">
                    <span class="ms-icon">🔄</span>
                    <span class="button-text">Try Again</span>
                </a>
            </div>
        </div>
        <div class="footer">
            © 2024 Key Talent Solutions - Secure Enterprise HR Management
        </div>
    </div>
    """, unsafe_allow_html=True)

def handle_auth_callback(auth_code: str):
    """Handle authentication callback from Microsoft"""
    auth_manager = st.session_state.auth_manager
    
    # Process authentication
    user_info = auth_manager.handle_auth_callback(auth_code)
    
    if user_info:
        if user_info.get("is_authorized", False):
            # User is authorized
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            
            # Clear query parameters
            st.query_params.clear()
            
            # Show success card
            st.markdown(f"""
            <div class="main-card">
                <div class="header-section">
                    <div class="logo">
                        <div class="logo-icon">✅</div>
                    </div>
                    <p class="subtitle">Authentication Successful</p>
                </div>
                <div class="content-section">
                    <div class="success-message">
                        <h3>🎉 Sign-in Successful</h3>
                        <p>Welcome, <strong>{user_info.get("name", "User")}</strong>!</p>
                        <p>You have been successfully authenticated. Redirecting to the application...</p>
                    </div>
                </div>
                <div class="footer">
                    © 2024 Key Talent Solutions - Secure Enterprise HR Management
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Force rerun to load main app
            st.rerun()
            
        else:
            # User is not authorized
            show_unauthorized_card(user_info)
    else:
        show_error_card("Authentication failed. Please try again.")

def show_unauthorized_card(user_info: Dict):
    """Show unauthorized access card"""
    logout_url = st.session_state.auth_manager.get_logout_url()
    
    st.markdown(f"""
    <div class="main-card">
        <div class="header-section">
            <div class="logo">
                <div class="logo-icon">🚫</div>
            </div>
            <h1 class="main-title">Access Denied</h1>
            <p class="subtitle">Insufficient Permissions</p>
        </div>
        <div class="content-section">
            <div class="error-message">
                <h3>🔒 Access Denied</h3>
                <p>Hello <strong>{user_info.get("name", "User")}</strong>,</p>
                <p>You are not authorized to access this application. Please contact your administrator to request access to the HR Candidate Management System.</p>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(197, 48, 48, 0.2);">
                    <p><strong>Email:</strong> {user_info.get("email", "N/A")}</p>
                    <p><strong>Reason:</strong> User is not a member of the authorized security group.</p>
                </div>
            </div>
            <div class="login-button-container">
                <a href="{logout_url}" class="login-button" style="background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%); box-shadow: 0 4px 20px rgba(229, 62, 62, 0.3);" target="_self">
                    <span class="ms-icon">🚪</span>
                    <span class="button-text">Sign Out</span>
                </a>
            </div>
        </div>
        <div class="footer">
            © 2024 Key Talent Solutions - Secure Enterprise HR Management
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_user_profile():
    """Show user profile information in sidebar"""
    user_info = st.session_state.get('user_info')
    if user_info:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Profile")
            st.markdown(f"**Name:** {user_info.get('name', 'N/A')}")
            st.markdown(f"**Email:** {user_info.get('email', 'N/A')}")
            if user_info.get('job_title'):
                st.markdown(f"**Title:** {user_info.get('job_title')}")
            if user_info.get('department'):
                st.markdown(f"**Department:** {user_info.get('department')}")
            
            st.markdown("---")
            
            # Logout button
            if st.button("🚪 Sign Out", use_container_width=True):
                auth_manager = st.session_state.auth_manager
                auth_manager.logout()
                
                # Reset user session state manually to avoid circular import
                st.session_state.user_session_initialized = False
                st.session_state.db_initialized = False
                
                # Clear database manager to force re-initialization on next login
                if 'db_manager' in st.session_state:
                    del st.session_state['db_manager']
                
                # Clear all cached data
                if 'cached_search_results' in st.session_state:
                    del st.session_state['cached_search_results']
                if 'cached_search_criteria' in st.session_state:
                    del st.session_state['cached_search_criteria']
                if 'search_performed' in st.session_state:
                    st.session_state.search_performed = False
                
                st.rerun()