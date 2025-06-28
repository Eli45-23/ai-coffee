import vertexai
from vertexai.preview.language_models import TextGenerationModel

# 1️⃣ Init with your real project and region
vertexai.init(project="ai-coffee-464212", location="us-central1")

# 2️⃣ Load the Gemini foundation model of your choice
#    Options you’ll see under “Foundation models” include:
#      - gemini-2.5-flash-lite
#      - gemini-2.5-pro
#      - gemini-2.5-flash
#    We’ll pick the strongest (“pro”) here:
model = TextGenerationModel.from_pretrained("gemini-2.5-pro")

# 3️⃣ Send a prompt
response = model.predict("Hello from AI Coffee! How’s your day going?")

print("Gemini says:", response.text)
