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
        /* Hide Streamlit default elements */
        .stApp > header {visibility: hidden;}
        .stApp > div > div > div > div > section > div {padding-top: 0rem;}
        .stApp {background-color: #f8f9fa;}
        
        /* Hide all default streamlit content */
        .main .block-container {
            padding: 0;
            max-width: none;
        }
        
        /* Main container */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background: #ffffff;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
        }
        
        /* Header section */
        .header-section {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
            border-bottom: 4px solid #3498db;
        }
        
        /* Logo */
        .logo {
            width: 80px;
            height: 80px;
            background: #ffffff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 2rem auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .logo-icon {
            font-size: 2.5rem;
            color: #2c3e50;
        }
        
        /* Typography */
        .main-title {
            font-size: 2.8rem;
            font-weight: 300;
            margin: 0 0 1rem 0;
            letter-spacing: -1px;
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 300;
            margin: 0;
        }
        
        /* Content section */
        .content-section {
            flex: 1;
            padding: 4rem 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #ffffff;
        }
        
        /* Login card */
        .login-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 3rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
            text-align: center;
            max-width: 500px;
            width: 100%;
        }
        
        .login-card h3 {
            color: #2c3e50;
            font-size: 1.5rem;
            font-weight: 400;
            margin: 0 0 1.5rem 0;
        }
        
        .login-card p {
            color: #6c757d;
            font-size: 1rem;
            line-height: 1.6;
            margin: 0 0 2rem 0;
        }
        
        /* Login button */
        .login-button {
            background: #3498db;
            color: white;
            padding: 1rem 2.5rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
            width: 100%;
            max-width: 280px;
        }
        
        .login-button:hover {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.3);
            color: white;
            text-decoration: none;
        }
        
        .login-button:active {
            transform: translateY(0);
        }
        
        /* Microsoft icon */
        .ms-icon {
            margin-right: 0.5rem;
            font-size: 1.1rem;
        }
        
        /* Security badge */
        .security-badge {
            display: inline-flex;
            align-items: center;
            background: #f8f9fa;
            color: #6c757d;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 1.5rem;
            border: 1px solid #e9ecef;
        }
        
        .security-badge::before {
            content: "🔒";
            margin-right: 0.5rem;
        }
        
        /* Message cards */
        .message-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            border: 1px solid #e9ecef;
            margin: 2rem 0;
            max-width: 600px;
            width: 100%;
        }
        
        /* Error styling */
        .error-message {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-left: 4px solid #e53e3e;
            border-radius: 8px;
            padding: 1.5rem;
            color: #c53030;
        }
        
        .error-message h3 {
            margin: 0 0 1rem 0;
            color: #c53030;
        }
        
        /* Success styling */
        .success-message {
            background: #f0fff4;
            border: 1px solid #c6f6d5;
            border-left: 4px solid #38a169;
            border-radius: 8px;
            padding: 1.5rem;
            color: #2f855a;
        }
        
        .success-message h3 {
            margin: 0 0 1rem 0;
            color: #2f855a;
        }
        
        /* Footer */
        .footer {
            background: #f8f9fa;
            color: #6c757d;
            text-align: center;
            padding: 2rem;
            border-top: 1px solid #e9ecef;
            font-size: 0.9rem;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .header-section {
                padding: 2rem 1rem;
            }
            
            .main-title {
                font-size: 2.2rem;
            }
            
            .content-section {
                padding: 2rem 1rem;
            }
            
            .login-card {
                padding: 2rem 1.5rem;
                margin: 0 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the main container structure
    st.markdown("""
    <div class="main-container">
        <div class="header-section">
            <div class="logo">
                <div class="logo-icon">🎯</div>
            </div>
            <h1 class="main-title">Key Talent Solutions</h1>
            <p class="subtitle">AI-Powered HR Candidate Management System</p>
        </div>
        <div class="content-section">
    """, unsafe_allow_html=True)
    
    # Check for authentication callback
    query_params = st.query_params
    
    # Handle different states
    if 'code' in query_params:
        handle_auth_callback(query_params['code'])
    elif 'error' in query_params:
        show_auth_error(query_params.get('error', 'Unknown error'))
    else:
        show_login_options()
    
    # Close the container
    st.markdown("""
        </div>
        <div class="footer">
            © 2024 Key Talent Solutions - Secure Enterprise HR Management
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_login_options():
    """Show login options within the main container"""
    auth_manager = st.session_state.auth_manager
    
    if not auth_manager.is_configured():
        st.markdown("""
        <div class="message-card">
            <div class="error-message">
                <h3>Configuration Required</h3>
                <p>Microsoft Entra authentication is not properly configured. Please contact your administrator.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get the auth URL
    auth_url = auth_manager.get_auth_url()
    
    if auth_url:
        # Show the login card with the button
        st.markdown(f"""
        <div class="login-card">
            <h3>Welcome</h3>
            <p>Sign in with your organization account to access the HR Candidate Management System.</p>
            <a href="{auth_url}" class="login-button" target="_self">
                <span class="ms-icon">⊞</span>
                Sign in with Microsoft
            </a>
            <div class="security-badge">
                Secured by Microsoft Entra ID
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="message-card">
            <div class="error-message">
                <h3>Configuration Error</h3>
                <p>Unable to generate authentication URL. Please check the application configuration.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def handle_auth_callback(auth_code: str):
    """Handle authentication callback from Microsoft"""
    auth_manager = st.session_state.auth_manager
    
    # Show processing message
    st.markdown("""
    <div class="message-card">
        <div class="info-message">
            <h3>Processing Authentication...</h3>
            <p>Please wait while we verify your credentials.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Process authentication
    user_info = auth_manager.handle_auth_callback(auth_code)
    
    if user_info:
        if user_info.get("is_authorized", False):
            # User is authorized
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            
            # Clear query parameters
            st.query_params.clear()
            
            # Show success message
            st.markdown(f"""
            <div class="message-card">
                <div class="success-message">
                    <h3>Authentication Successful</h3>
                    <p>Welcome, {user_info.get("name", "User")}! Redirecting to the application...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Force rerun to load main app
            st.rerun()
            
        else:
            # User is not authorized
            show_unauthorized_access(user_info)
    else:
        show_auth_error("Authentication failed. Please try again.")

def show_unauthorized_access(user_info: Dict):
    """Show unauthorized access message"""
    logout_url = st.session_state.auth_manager.get_logout_url()
    
    st.markdown(f"""
    <div class="message-card">
        <div class="error-message">
            <h3>Access Denied</h3>
            <p>Hello <strong>{user_info.get("name", "User")}</strong>,</p>
            <p>You are not authorized to access this application. Please contact your administrator to request access to the HR Candidate Management System.</p>
            <p><strong>Your email:</strong> {user_info.get("email", "N/A")}</p>
            <p><strong>Reason:</strong> User is not a member of the authorized security group.</p>
        </div>
        <a href="{logout_url}" class="login-button" style="background: #e74c3c; margin-top: 1.5rem; text-decoration: none;">
            Sign Out
        </a>
    </div>
    """, unsafe_allow_html=True)

def show_auth_error(error_message: str):
    """Show authentication error"""
    redirect_uri = st.session_state.auth_manager.redirect_uri
    
    st.markdown(f"""
    <div class="message-card">
        <div class="error-message">
            <h3>Authentication Error</h3>
            <p>{error_message}</p>
            <p>Please try again or contact your system administrator if the problem persists.</p>
        </div>
        <a href="{redirect_uri}" class="login-button" style="margin-top: 1.5rem; text-decoration: none;">
            Try Again
        </a>
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
                st.rerun()