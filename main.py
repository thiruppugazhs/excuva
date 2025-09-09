# app.py (Python Backend with Local Model Fallback)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI # Using Google Gemini API
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
import os
import json # Import json for parsing tool input

# Import for local models (if you choose to use the fallback)
from langchain_community.llms import CTransformers

# Configure Flask to serve static files from the current directory
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- Configure your Gemini API Key ---
# For local development, you can uncomment the line below and replace "YOUR_GEMINI_API_KEY"
# with your actual Google API Key.
# It is highly recommended to use environment variables for production deployments
# (e.g., export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY" in your terminal).
# If you set it here, make sure to remove it before committing to public repositories.
os.environ["GOOGLE_API_KEY"] = "" # Uncomment and replace for local testing

if not os.getenv("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY environment variable not set.")
    print("Please set it (e.g., 'export GOOGLE_API_KEY=\"YOUR_API_KEY\"') for AI functionality.")
    print("Alternatively, for local testing, uncomment the 'os.environ[\"GOOGLE_API_KEY\"]' line in app.py and provide your key.")


# --- LLM Initialization (Google API with Fallback to Local Model) ---
llm_gemini = None
llm_local = None
active_llm = None
model_source = "none" # To track which model is active: "google", "local", "none"

print("\n--- Attempting to initialize AI models ---")

# 1. Try to initialize Google Gemini API
try:
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if gemini_api_key:
        # Changed model from "gemini-pro" to "gemini-2.5-flash"
        llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        # Test if the Google LLM can actually make a call
        llm_gemini.invoke("Hello, check connection.") # Simple test call
        active_llm = llm_gemini
        model_source = "google"
        print("Google Gemini-2.5-Flash model initialized successfully and connection verified.")
    else:
        print("Google API Key not found. Skipping Google Gemini initialization.")
except Exception as e:
    print(f"Error initializing Google Gemini-2.5-Flash or connecting: {e}.")
    print("Falling back to local model.")

# 2. Fallback to local model if Google Gemini failed or was not configured
if active_llm is None:
    print("Attempting to initialize local model...")
    try:
        # --- LOCAL MODEL CONFIGURATION ---
        local_model_path = "llama-2-7b-chat.Q4_K_M.gguf" # <--- VERIFY THIS PATH

        # !!! YOU MUST DETERMINE THE CORRECT model_type FOR YOUR .gguf MODEL !!!
        # If it's a Llama-based model, use "llama"
        # If it's a Mistral-based model, use "mistral"
        # If it's a Gemma-based model, use "gemma"
        # Check the model's Hugging Face page or documentation for its type.
        local_model_type = "llama" # <--- VERIFY THIS MODEL TYPE

        if os.path.exists(local_model_path):
            llm_local = CTransformers(
                model=local_model_path,
                model_type=local_model_type,
                # Adjust config parameters as needed for your model and system resources
                config={'max_new_tokens': 500, 'temperature': 0.7, 'context_length': 2048}
            )
            # You might want to do a small test inference here for the local model too
            llm_local.invoke("Hello.")
            active_llm = llm_local
            model_source = "local"
            print(f"Local model '{local_model_path}' initialized successfully and ready.")
        else:
            
            print(f"Local model file '{local_model_path}' not found. Please ensure the path is correct.")
            print("Local model fallback failed.")

    except Exception as e:
        print(f"Error initializing local model: {e}.")
        print("No AI model (Google or local) could be initialized. AI generation will not work.")

print(f"--- Active AI Model Source: {model_source.upper()} ---\n")

# --- Core Excuse Generation Logic (New Function) ---
# This function handles the actual LLM call with the given parameters
def _generate_excuse_core(scenario: str, urgency: str, details: str) -> str:
    """
    Core logic for generating an excuse using the currently active LLM instance.
    This function is called by both the LangChain tool and the direct Flask route.
    """
    if active_llm is None:
        return "Error: No AI model initialized for excuse generation. Check backend logs."

    excuse_prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are an expert at generating highly believable, context-aware, and natural-sounding excuses. Your goal is to provide a reason for a specific situation that is difficult to question. The excuse should be creative, detailed, and sound natural. Do not include any conversational text, just the excuse itself."),
        HumanMessage(content="Generate an excuse for the following situation:\n\nScenario: {scenario}\nUrgency: {urgency}\nAdditional details/desired tone: {details}\n")
    ])
    excuse_chain = excuse_prompt_template | active_llm
    try:
        response = excuse_chain.invoke({"scenario": scenario, "urgency": urgency, "details": details})
        return response.content
    except Exception as e:
        # Log the error for debugging on the server side
        print(f"Error during LLM call in _generate_excuse_core: {e}")
        return f"Error during excuse generation (LLM call): {e}. Check backend logs."


# --- Define Tools for the Agent ---
# The tool now expects a single JSON string input from the agent
@tool
def generate_excuse_tool(input_json: str) -> str:
    """
    Generates a believable and context-aware excuse for a given scenario.
    The input should be a JSON string with 'scenario', 'urgency' (optional), and 'details' (optional) keys.
    Example: {"scenario": "late for work", "urgency": "high", "details": "traffic jam"}
    """
    try:
        parsed_input = json.loads(input_json)
        scenario = parsed_input.get('scenario', '')
        urgency = parsed_input.get('urgency', 'medium')
        details = parsed_input.get('details', 'None specified.')

        if not scenario:
            return "Error: 'scenario' is required for excuse generation."

        # Call the core logic function
        return _generate_excuse_core(scenario=scenario, urgency=urgency, details=details)
    except json.JSONDecodeError:
        return "Error: Invalid JSON input for generate_excuse_tool. Input must be a valid JSON string."
    except Exception as e:
        return f"Error processing tool input: {e}"


@tool
def generate_proof_tool(excuse_text: str, proof_type: str = "generic") -> str:
    """
    Generates a placeholder message for proof. In a real application, this would create a convincing document or image.
    Use this when the user asks for 'proof', 'document', 'screenshot', or 'location log'.
    Args:
        excuse_text (str): The excuse for which proof is needed.
        proof_type (str, optional): The type of proof to generate (e.g., "chat screenshot", "doctor's note", "location log"). Defaults to "generic".
    Returns:
        str: A message indicating proof generation.
    """
    return f"Proof generation for '{proof_type}' is a placeholder. Would generate a convincing text/image proof for: '{excuse_text}'."

@tool
def trigger_emergency_tool(emergency_type: str = "call", contact: str = "emergency_contact") -> str:
    """
    Triggers a placeholder emergency message or call. In a real application, this would integrate with a messaging/calling service.
    Use this when the user asks to 'trigger an emergency', 'fake call', or 'fake text'.
    Args:
        emergency_type (str, optional): The type of emergency (e.g., "call", "text"). Defaults to "call".
        contact (str, optional): The person or group to contact. Defaults to "emergency_contact".
    Returns:
        str: A message indicating emergency trigger.
    """
    return f"Emergency system is a placeholder. Would trigger a fake {emergency_type} to {contact}."

@tool
def generate_apology_tool(situation: str, tone: str = "professional") -> str:
    """
    Generates a placeholder message for an apology. In a real application, this would generate a detailed apology.
    Use this when the user asks for an 'apology'.
    Args:
        situation (str): The situation for which the apology is needed.
        tone (str, optional): The desired tone of the apology (e.g., "professional", "emotional", "guilt-tripping"). Defaults to "professional".
    Returns:
        str: A message indicating apology generation.
    """
    return f"Apology generation is a placeholder. Would generate a {tone} apology for: '{situation}'."

tools = [generate_excuse_tool, generate_proof_tool, trigger_emergency_tool, generate_apology_tool]

# --- LangChain Agent Setup ---
# The agent will now use the 'active_llm'
agent_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a helpful AI assistant. Your primary goal is to assist users with generating excuses, proof, emergency triggers, and apologies. Use the available tools to fulfill the user's requests. If you need more information to use a tool, ask clarifying questions. When using the 'generate_excuse_tool', provide the 'scenario', 'urgency', and 'details' as a JSON string. Be concise and direct."),
    HumanMessage(content="{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = None
agent_executor = None
if active_llm: # Use active_llm here
    try:
        agent = create_tool_calling_agent(active_llm, tools, agent_prompt) # Use active_llm here
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        print("LangChain Agent initialized successfully.")
    except Exception as e:
        print(f"Error initializing LangChain Agent: {e}.")
        agent_executor = None
else:
    print("Warning: Agent could not be initialized as no active LLM is available.")


# --- API Endpoints ---

# Route to serve the main HTML file
@app.route('/')
def serve_index():
    # Flask will automatically look for index.html in the static_folder (which is '.' here)
    # when static_url_path is set to ''
    return send_from_directory('.', 'index.html')

@app.route('/agent_interact', methods=['POST'])
def agent_interact():
    if agent_executor is None:
        return jsonify({"error": "AI Agent not initialized. Check backend logs for LLM or agent setup errors."}), 500

    data = request.json
    user_query = data.get('query', '').strip()

    if not user_query:
        return jsonify({"error": "Query is required."}), 400

    try:
        result = agent_executor.invoke({"input": user_query})
        return jsonify({"response": result.get('output', 'No specific output from agent.')})

    except Exception as e:
        print(f"Error during agent interaction: {e}")
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 500

@app.route('/generate_excuse_direct', methods=['POST'])
def generate_excuse_direct():
    data = request.json
    scenario = data.get('scenario', '').strip()
    urgency = data.get('urgency', 'medium')
    details = data.get('details', 'None specified.').strip()
    if not scenario:
        return jsonify({"error": "Scenario is required."}), 400
    try:
        # THIS IS THE CRUCIAL CHANGE: Directly call the _generate_excuse_core function
        # with the extracted arguments from the frontend.
        excuse = _generate_excuse_core(scenario=scenario, urgency=urgency, details=details)
        return jsonify({"excuse": excuse})
    except Exception as e:
        print(f"Error direct excuse generation: {e}")
        return jsonify({"error": f"Failed to generate excuse directly: {str(e)}"}), 500

@app.route('/generate_proof_direct', methods=['POST'])
def generate_proof_direct():
    data = request.json
    excuse_text = data.get('excuse', 'No excuse provided.')
    proof_type = data.get('proof_type', 'generic')
    message = generate_proof_tool(excuse_text=excuse_text, proof_type=proof_type)
    return jsonify({"message": message})

@app.route('/trigger_emergency_direct', methods=['POST'])
def trigger_emergency_direct():
    data = request.json
    emergency_type = data.get('type', 'call')
    contact = data.get('contact', 'emergency_contact')
    message = trigger_emergency_tool(emergency_type=emergency_type, contact=contact)
    return jsonify({"message": message})

@app.route('/generate_apology_direct', methods=['POST'])
def generate_apology_direct():
    data = request.json
    situation = data.get('situation', 'a general situation')
    tone = data.get('tone', 'professional')
    message = generate_apology_tool(situation=situation, tone=tone)
    return jsonify({"message": message})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
