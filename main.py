import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Create Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Create or load assistant
assistant_id = functions.create_assistant(
    client)  # this function comes from "functions.py"

#route handler (not understood)
@app.route('/')
def home():
    return jsonify({"message": "Willkommen zur Chatbot-API. Verwende /start, um eine Konversation zu beginnen, und /chat, um Nachrichten zu senden."})

# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
  print("Starting a new conversation...")
  thread = client.beta.threads.create()
  print(f"New thread created with ID: {thread.id}")
  return jsonify({"thread_id": thread.id})

# Generate response
@app.route('/chat', methods=['POST'])
def chat():
  data = request.json
  #debug
  print(f"Incoming request to /chat: {json.dumps(data, indent=2)}")
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')

  if not thread_id:
    print("Error: Missing thread_id")
    return jsonify({"error": "Missing thread_id"}), 400

  print(f"Received message: {user_input} for thread ID: {thread_id}")

  #debug
  print(f"Sending to OpenAI (Thread Message): {json.dumps({'thread_id': thread_id, 'role': 'user', 'content': user_input}, indent=2)}")

  # Add the user's message to the thread
  client.beta.threads.messages.create(thread_id=thread_id,
                                      role="user",
                                      content=user_input)

  #debug
  print(f"Sending to OpenAI (Run Action): {json.dumps({'thread_id': thread_id, 'assistant_id': assistant_id}, indent=2)}")


  # Run the Assistant
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                        assistant_id=assistant_id)

  # Check if the Run requires action (function call)
  while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                   run_id=run.id)
    if run_status.status == 'completed':
      break
    elif run_status.status == 'requires_action':
      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
          if tool_call.function.name == "book_appointment":
            arguments = json.loads(tool_call.function.arguments)
            output = functions.book_appointment(arguments["name"], arguments["email"], arguments["date"], arguments["time"], arguments["company"])
            # Debugging: Protokollierung der gesendeten Ausgabe
            print(f"[DEBUG] Output sent for 'book_appointment': {output}")
            client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                         run_id=run.id,
                                                         tool_outputs=[{
                                                              "tool_call_id": tool_call.id,
                                                               "output": json.dumps(output)
                                                         }])
          elif tool_call.function.name == "delete_appointmentk":
            arguments = json.loads(tool_call.function.arguments)
            output = functions.delete_appointment(arguments["name"], arguments["email"], arguments["date"], arguments["time"], arguments["company"])
            # Debugging: Protokollierung der gesendeten Ausgabe
            print(f"[DEBUG] Output sent for 'delete_appointment': {output}")
            client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                         run_id=run.id,
                                                         tool_outputs=[{
                                                             "tool_call_id": tool_call.id,
                                                             "output": json.dumps(output)
                                                         }])
          elif tool_call.function.name == "reschedule_appointment":
            arguments = json.loads(tool_call.function.arguments)
            output = functions.reschedule_appointment(arguments["name"], arguments["email"], arguments["company"], arguments["date"], arguments["time"], arguments["date_new"], arguments["time_new"])
            # Debugging: Protokollierung der gesendeten Ausgabe
            print(f"[DEBUG] Output sent for 'reschedule_appointment': {output}")
            client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                         run_id=run.id,
                                                         tool_outputs=[{
                                                             "tool_call_id": tool_call.id,
                                                             "output": json.dumps(output)
                                                         }])
            time.sleep(1)  # Wait for a second before checking again

  # Retrieve and return the latest message from the assistant
  messages = client.beta.threads.messages.list(thread_id=thread_id)
  print(f"Debug: Retrieved messages: {messages.data}")  
  # Debug
  response = messages.data[0].content[0].text.value
  # Debug
  print(f"Debug: Sending response: {response}")  
  print(f"Assistant response: {response}")
  return jsonify({"response": response})

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=False)