import streamlit as st
import requests
import json
import google.generativeai as genai
from typing import Dict, Any
import time

# Page configuration
st.set_page_config(
    page_title="API Consumer & Gemini Interface",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🚀 API Consumer & Gemini Interface</h1>', unsafe_allow_html=True)

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# Initialize session state
if 'api_responses' not in st.session_state:
    st.session_state.api_responses = []
if 'gemini_conversations' not in st.session_state:
    st.session_state.gemini_conversations = []

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🌐 REST API Consumer", "🤖 Gemini AI", "📊 Response History"])

# Tab 1: REST API Consumer
with tab1:
    st.markdown('<h2 class="section-header">REST API Consumer</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 API Configuration")
        
        # API endpoint input
        api_url = st.text_input(
            "API Endpoint URL",
            value="https://jsonplaceholder.typicode.com/posts",
            help="Enter the API endpoint you want to consume"
        )
        
        # Method selection
        method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
        
        # Headers configuration
        st.subheader("Headers")
        headers_json = st.text_area(
            "Request Headers (JSON format)",
            value='{"Content-Type": "application/json"}',
            height=100,
            help="Enter headers in JSON format"
        )
        
        # Request body for POST/PUT/DELETE
        if method in ["POST", "PUT", "DELETE"]:
            st.subheader("Request Body")
            request_body = st.text_area(
                "Request Body (JSON format)",
                value='{\n  "title": "Sample Post",\n  "body": "This is a sample post body",\n  "userId": 1\n}',
                height=150,
                help="Enter request body in JSON format"
            )
        else:
            request_body = None
        
        # Query parameters for GET
        if method == "GET":
            st.subheader("Query Parameters")
            query_params = st.text_area(
                "Query Parameters (JSON format)",
                value='{"_limit": "5"}',
                height=100,
                help="Enter query parameters in JSON format"
            )
        else:
            query_params = None
    
    with col2:
        st.subheader("🚀 API Response")
        
        if st.button(f"Send {method} Request", type="primary"):
            try:
                # Parse headers
                headers = json.loads(headers_json) if headers_json else {}
                
                # Parse query parameters
                params = json.loads(query_params) if query_params else None
                
                # Parse request body
                data = json.loads(request_body) if request_body else None
                
                # Make the API request
                with st.spinner("Making API request..."):
                    if method == "GET":
                        response = requests.get(api_url, headers=headers, params=params)
                    elif method == "POST":
                        response = requests.post(api_url, headers=headers, json=data)
                    elif method == "PUT":
                        response = requests.put(api_url, headers=headers, json=data)
                    elif method == "DELETE":
                        response = requests.delete(api_url, headers=headers)
                
                # Display response
                if response.status_code == 200 or response.status_code == 201:
                    st.success(f"✅ Success! Status Code: {response.status_code}")
                    
                    # Try to parse JSON response
                    try:
                        response_json = response.json()
                        st.json(response_json)
                        
                        # Save to session state
                        st.session_state.api_responses.append({
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "method": method,
                            "url": api_url,
                            "status_code": response.status_code,
                            "response": response_json
                        })
                    except json.JSONDecodeError:
                        st.text("Response (not JSON):")
                        st.code(response.text)
                else:
                    st.error(f"❌ Error! Status Code: {response.status_code}")
                    st.code(response.text)
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON parsing error: {str(e)}")
            except requests.RequestException as e:
                st.error(f"❌ Request error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

# Tab 2: Gemini AI Integration
with tab2:
    st.markdown('<h2 class="section-header">Gemini AI Integration</h2>', unsafe_allow_html=True)
    
    # Gemini API key configuration
    gemini_api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key"
    )
    
    if gemini_api_key:
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🤖 Chat with Gemini")
            
            # Model selection
            model_name = st.selectbox(
                "Select Gemini Model",
                ["gemini-pro", "gemini-pro-vision"],
                help="Choose the Gemini model to use"
            )
            
            # Temperature setting
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Controls randomness in responses"
            )
            
            # Max tokens
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=1,
                max_value=8192,
                value=1000,
                help="Maximum number of tokens in response"
            )
            
            # User input
            user_prompt = st.text_area(
                "Your Message",
                height=150,
                placeholder="Ask Gemini anything..."
            )
            
            # File upload for vision model
            uploaded_file = None
            if model_name == "gemini-pro-vision":
                uploaded_file = st.file_uploader(
                    "Upload an image (for vision model)",
                    type=['png', 'jpg', 'jpeg']
                )
        
        with col2:
            st.subheader("🗨️ Gemini Response")
            
            if st.button("Send to Gemini", type="primary"):
                if user_prompt:
                    try:
                        # Initialize the model
                        model = genai.GenerativeModel(model_name)
                        
                        # Generate response
                        with st.spinner("Generating response..."):
                            if model_name == "gemini-pro-vision" and uploaded_file:
                                # Handle vision model with image
                                import PIL.Image
                                image = PIL.Image.open(uploaded_file)
                                response = model.generate_content([user_prompt, image])
                            else:
                                # Handle text-only model
                                response = model.generate_content(
                                    user_prompt,
                                    generation_config=genai.types.GenerationConfig(
                                        temperature=temperature,
                                        max_output_tokens=max_tokens
                                    )
                                )
                        
                        # Display response
                        if response.text:
                            st.success("✅ Response generated successfully!")
                            st.markdown(response.text)
                            
                            # Save to session state
                            st.session_state.gemini_conversations.append({
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "model": model_name,
                                "prompt": user_prompt,
                                "response": response.text,
                                "temperature": temperature,
                                "max_tokens": max_tokens
                            })
                        else:
                            st.warning("⚠️ No response generated. Try adjusting your prompt.")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating response: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a message to send to Gemini.")
    else:
        st.info("🔑 Please enter your Gemini API key in the sidebar to start using Gemini AI.")
        st.markdown("""
        ### How to get a Gemini API key:
        1. Visit [Google AI Studio](https://aistudio.google.com/)
        2. Sign in with your Google account
        3. Navigate to API keys section
        4. Create a new API key
        5. Copy and paste it in the sidebar
        """)

# Tab 3: Response History
with tab3:
    st.markdown('<h2 class="section-header">Response History</h2>', unsafe_allow_html=True)
    
    # API Responses History
    if st.session_state.api_responses:
        st.subheader("🌐 API Responses History")
        for i, response in enumerate(reversed(st.session_state.api_responses)):
            with st.expander(f"{response['method']} - {response['timestamp']} - Status: {response['status_code']}"):
                st.write(f"**URL:** {response['url']}")
                st.write(f"**Method:** {response['method']}")
                st.write(f"**Status Code:** {response['status_code']}")
                st.write("**Response:**")
                st.json(response['response'])
    else:
        st.info("No API responses yet. Make some API calls in the REST API Consumer tab!")
    
    st.divider()
    
    # Gemini Conversations History
    if st.session_state.gemini_conversations:
        st.subheader("🤖 Gemini Conversations History")
        for i, conversation in enumerate(reversed(st.session_state.gemini_conversations)):
            with st.expander(f"Conversation - {conversation['timestamp']} - Model: {conversation['model']}"):
                st.write(f"**Model:** {conversation['model']}")
                st.write(f"**Temperature:** {conversation['temperature']}")
                st.write(f"**Max Tokens:** {conversation['max_tokens']}")
                st.write("**Your Prompt:**")
                st.write(conversation['prompt'])
                st.write("**Gemini's Response:**")
                st.markdown(conversation['response'])
    else:
        st.info("No Gemini conversations yet. Start chatting in the Gemini AI tab!")
    
    # Clear history buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear API History"):
            st.session_state.api_responses = []
            st.success("API history cleared!")
    
    with col2:
        if st.button("🗑️ Clear Gemini History"):
            st.session_state.gemini_conversations = []
            st.success("Gemini history cleared!")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🚀 Built with Streamlit | 🌐 REST API Consumer | 🤖 Powered by Gemini AI</p>
</div>
""", unsafe_allow_html=True)    