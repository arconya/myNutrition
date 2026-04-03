import os
import gradio as gr
from langchain.chat_models import init_chat_model
from nutritionAdvisor import NutritionAdvisor
from langchain_core.rate_limiters import InMemoryRateLimiter

U_ID = "1"

# ------------------------------------------------------------------
# Initialize LLM model
# ------------------------------------------------------------------
models = {}
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if os.environ.get("OPENAI_API_KEY"):
    models["OpenAI GPT 5.2"] = "gpt-5.2"
    models["OpenAI GPT Mini"] = "gpt-5-mini"
    models["OpenAI GPT Nano"] = "gpt-5-nano"
    models["OpenAI GPT 4.1 Nano"] = "gpt-4.1-nano"
    models["OpenAI GPT-4o Mini"] = "gpt-4o-mini"
    models["OpenAI GPT-3.5 Turbo"] = "gpt-3.5-turbo"


if os.environ.get("GOOGLE_API_KEY"):
    models["Google Gemini"] = "gemini-3.1-flash-lite-preview"

if not models:
    raise EnvironmentError(
        "Keine API-Schlüssel gefunden!\n"
        "Bitte setzen Sie mindestens eine der folgenden Umgebungsvariablen:\n"
        "  OPENAI_API_KEY\n"
        "  GOOGLE_API_KEY"
    )

# Create a limiter: 1 request every 2 seconds
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    max_bucket_size=10  # Allows a small "burst" of 10 requests at once
)

# Default model selection
default_model_name = "OpenAI GPT 5.2"
model_id = models[default_model_name]
model = init_chat_model(
    model_id,
    rate_limiter=rate_limiter
)

# Initialize NutritionAdvisor
myNutrition = NutritionAdvisor(model, U_ID)


def change_model(model_name):
    global myNutrition, model, model_id
    model_id = models[model_name]
    model = init_chat_model(model_id, rate_limiter=rate_limiter)
    myNutrition = NutritionAdvisor(model, U_ID)
    return f"Switched to {model_name}"

css = """.green {background-color: #3EBF41;}
h1 {
  text-align: center;
  color: #3EBF41;
}"""

# ------------------------------------------------------------------
# Gradio Chat Interface with Streaming using Blocks
# ------------------------------------------------------------------

def user(user_message, history):
    # Add user message to history with proper role/content structure
    return "", history + [{"role": "user", "content": user_message}]

def bot(history):
    user_message = history[-1]["content"]   # Get the last user message
    ai_message = myNutrition.get_response(user_message)

    history.append({"role": "assistant", "content": ai_message})

    return history

with gr.Blocks() as demo:
    gr.Markdown(value="# myNutrition Advisor", elem_classes="greenFont")
    gr.Markdown("Ask me anything about nutrition, diet, and healthy eating! You may also ask for recipy suggestions based on your eating preferences and daily nutrition goals.")

    model_dropdown = gr.Dropdown(
        choices=models.keys(),
        value=default_model_name,
        label="Select LLM Model",
        interactive=True
    )

    model_dropdown.change(change_model, model_dropdown, None)

    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(
        label="",
        placeholder="Ask your nutrition questions.",
        container=False
    )

    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary", elem_classes="green")
        clear_btn = gr.Button("Clear")

    # Example questions
    gr.Examples(
        examples=[
            "What are the benefits of a balanced diet?",
            "Why do I need to drink enough water?",
            "What vitamins are important for bone health?",
            "How much protein should I consume daily?",
            "Is iron stored in my body for long term?",
            "Please suggest a recipe."
        ],
        inputs=msg
    )

    def clear():
        myNutrition.clear_history()
        return None

    # Event handlers
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    submit_btn.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear_btn.click(clear, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(share=True, css=css)

