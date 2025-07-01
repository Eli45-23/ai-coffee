import vertexai
from vertexai.language_models import ChatModel

# initialize with your real project and region
vertexai.init(project="ai-coffee-464212", location="us-central1")

# list all the pretrained chat models
models = ChatModel.list_pretrained()
print("Available models:")
for m in models:
    print("  ", m)
