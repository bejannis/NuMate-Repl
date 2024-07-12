import json
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

#error handling 
def handle_external_request_error(e):
  """Generische Fehlerbehandlung für externe Anfragen."""
  print(f"Ein Fehler ist aufgetreten: {e}")
  return {"error": "Der Chatbot hat momentan Probleme mit dem Verarbeiten von Anfragen. Bitte wendem Sie sich per Mail an einen menschlichen Mitarbeiter. Die Adresse lautet: info@numate.ch"}

#book a call
def book_appointment(name, email, date, time, company):
  url = "https://hook.eu2.make.com/rmrrl6tzvwd87faubhhssq7w7rcx461f"
  headers = {"Content-Type": "application/json"}
  data = {
      "name": name,
      "email": email,
      "date": date, 
      "time": time,
      "company": compa
    }
  #debug
  print(data) 
  print(f"[DEBUG] Daten für book_appointment: {json.dumps(data, indent=2)}")
  
  try:
      response = requests.post(url, headers=headers, json=data)
      print(f"[DEBUG] Antwortstatus von book_appointment: {response.status_code}")
      if response.status_code == 200:
          print("Call booking successful.")
          return {"result": "Call booked successfully"}
      elif response.status_code == 409:
          print("Failed to book call: The time slot is already booked.")
          return {"error": "Failed to book call: The time slot is already booked."}
      elif response.status_code == 422:
          print("Appointments on weekends are not possible.")
          return {"error": "Appointments on weekends are not possible."}
      elif response.status_code == 400:
          print("Failed to book call: Please add the year to the date.")
          return {"error": "Failed to book call: Please add the year to the date."}
      elif response.status_code == 500: 
          print("There was a problem processing your request. Please contact NuMate via email.")
          return {"error": "There was a problem processing your request. Please contact NuMate via email."}
      else:
          print(f"Unknown error occurred: {response.text}")
          return {"error": f"Unknown error occurred: {response.text}"}
  except Exception as e:
    return handle_external_request_error(e)

#delete call 
def delete_appointment(name, email, date, time, company):
  webhook_url = "https://hook.eu2.make.com/9fppn0tub89ixvs0tidepi2c8x6sgmw7"  
  headers = {"Content-Type": "application/json"}
  data = {
      "name": name,
      "email": email,
      "date": date,
      "time": time,
      "company": company
  }

  #debug
  print(data) 
  
  try:
    response = requests.post(webhook_url, json=data, headers=headers)
    if response.status_code == 200:
        print("Appointment deletion successful.")
        return {"result": "Appointment deleted successfully"}
    elif response.status_code == 400:  
        print("Please add the year to the date.")
        return {"error": "Please add the year to the date."}
    elif response.status_code == 404:  
        print("Event not found.")
        return {"error": "Event not found."}
    elif response.status_code == 500:
        print("There was a problem processing your request. Please contact NuMate via email.")
        return {"error": "There was a problem processing your request. Please contact NuMate via email."}
    else:
        print(f"Unknown error occurred: {response.text}")
        return {"error": f"Unknown error occurred: {response.text}"}
  except Exception as e:
    return handle_external_request_error(e)

#reschedule call
def reschedule_appointment(name, email, company, date, time, date_new, time_new):
  url = "https://hook.eu2.make.com/qj38ywkvodq3d1l97vgn9p4186awntwi"
  headers = {"Content-Type": "application/json"}
  data = {
      "name": name,
      "email": email,
      "company": company,
      "date": date,
      "time": time,
      "date_new": date_new,
      "time_new": time_new
  }

  #debug
  print(data) 
  
  try:
      response = requests.post(url, headers=headers, json=data)

      if response.status_code == 200:
          print("Termin erfolgreich verschoben.")
          return {"result": "Appointment rescheduled successfully"}
      elif response.status_code == 409:
          print("Failed to reschedule: The new time slot is already booked.")
          return {"error": "Failed to reschedule: The new time slot is already booked."}
      elif response.status_code == 422:
          print("Appointments on weekends are not possible.")
          return {"error": "Appointments on weekends are not possible."}
      elif response.status_code == 404: 
          print("Termin nicht gefunden.")
          return {"error": "Appointment not found."}
      elif response.status_code == 400:
          print("Failed to reschedule: Please add the year to the date.")
          return {"error": "Please add the year to the date."}
      elif response.status_code == 500:  
          print("There was a problem processing your request. Please contact NuMate via email.")
          return {"error": "There was a problem processing your request. Please contact NuMate via email."}
      else:
              print(f"Unknown error occurred: {response.text}")
              return {"error": f"Unknown error occurred: {response.text}"}
  except Exception as e:
    return handle_external_request_error(e)

# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'
  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications
    file = client.files.create(file=open("knowledge.docx", "rb"),
                               purpose='assistants')
    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
          instructions=assistant_instructions,
          model="gpt-4-turbo-preview",
          tools=[
              {
                  "type": "retrieval"  # This adds the knowledge base as a tool
              },
                {
                    "type": "function", #adding function to assistant on OpenAI
                    "function": {
                        "name": "book_appointment",
                        "description": "Book a call and send details to Make.com.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the person booking the call."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "Email of the person booking the call."
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Desired date for the call."
                                },
                                "time": {
                                    "type": "string",
                                    "description": "Desired time for the call between 4pm and 8pm."
                                },
                                "company": {
                                    "type": "string",
                                    "description": "Company name of the person booking the call."
                                }
                            },
                            "required": ["name", "email", "date", "time", "company"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "reschedule_appointment",
                        "description": "Verschiebt einen Termin zu einem neuen Datum und Uhrzeit basierend auf den angegebenen Details.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name der Person, für die der Termin verschoben werden soll."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "E-Mail-Adresse der Person, für die der Termin verschoben werden soll."
                                },
                                "company": {
                                    "type": "string",
                                    "description": "Unternehmen der Person, für die der Termin verschoben werden soll."
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Ursprüngliches Datum des Termins."
                                },
                                "time": {
                                    "type": "string",
                                    "description": "Ursprüngliche Uhrzeit des Termins."
                                },
                                "date_new": {
                                    "type": "string",
                                    "description": "Neues Datum für den verschobenen Termin."
                                },
                                "time_new": {
                                    "type": "string",
                                    "description": "Neue Uhrzeit für den verschobenen Termin."
                                }
                            },
                            "required": ["name", "email", "company", "date", "time", "date_new", "time_new"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delete_appointment",
                        "description": "Sendet einen Webhook an Make.com, um einen Termin zu löschen.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name der Person, deren Termin gelöscht werden soll."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "E-Mail der Person, deren Termin gelöscht werden soll."
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Datum des zu löschenden Termins."
                                },
                                "time": {
                                    "type": "string",
                                    "description": "Uhrzeit des zu löschenden Termins."
                                },
                                "company": {
                                    "type": "string",
                                    "description": "Unternehmen der Person, deren Termin gelöscht werden soll."
                                }
                            },
                            "required": ["name", "email", "date", "time", "company"]
                        }
                    }
                }
              ],
              file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
