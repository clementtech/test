
# Gemma AI Chatbot Application

This project is a fast, private, and offline chatbot that leverages the Gemma 3 AI model via Ollama for personal assistance such as reminders, meeting scheduling, homework help, and more. Our data is stored locally in TXT, **CSV, and **PDF formats, ensuring privacy and security without using any cloud-based services.

## Features

- Offline & Privacay/Secure: No need for cloud services; everything is stored locally on your device.
- Gemma 3 Model: Powered by the advanced **Gemma 3 language model for natural conversations.
- Task Management: Supports personal tasks like reminders, to-dos, meeting scheduling, homework help, etc.
- File Storage: Store and retrieve data in **TXT, **CSV, and **PDF formats.
- Fast & Reliable: Operates entirely on your local machine for faster, reliable performance.

## Setup Instructions

### Installation

#### Step 1: Install Ollama

1. Download Ollama:
   Visit the [official Ollama website](https://ollama.com) and download the installer for your operating system (Windows/macOS/Linux).
2. Install Ollama:
   Follow the installation instructions provided for your system. After installation, you will have the Ollama command-line tool available.

#### Step 2: Run the Gemma 3 Language Model

1. Open the terminal or command prompt.
2. Run the following command to start the Gemma 3 model with Ollama:

   bash
   ollama run gemma3:1b

#### Step 3:Create and Run the code through Visual Studio (VS Code)

Open Visual Studio (or VS Code) and create a new Python file called chatbot.py. This script will allow you to interact with the Gemma 3 model.

#### Step 4: Prepare and Install Project Dependencies

1. Create a requirements.txt file containing all required Python packages.

ollama
flask
requests
numpy
pandas
fpdf

2. Install them using
   bash
   pip install -r requirements.txt

#### Step 5: Run the Chatbot

Run the python script using:
python chatbot.py

2. Run the Chatbot in Visual Studio:

Use the following command to run the script:
 bash
python app.py

#### Step 6 : Access Local Server via Flask

The chatbot will run on a local web interface, open your website and visit:
[https://127.0.0.1:5000](https://127.0.0.1:5000)

## History Chat

The chatbot keeps a record of your conversations so you can **view past chats** anytime.

## Project Structure

local-ai-chatbot/
├──_pycache__
├── static
├── uploads
├── .gitattributes
├──chatbot.py
├── chat_history.json
├── requirements.txt
├── README.md
└── static/
     └── style.css
     └── script.js
└──templates/
      └── index.html

```

## Usage
The chatbot web interface and sample question with an answer:


![Chatbot Web Interface](./screenshots/chat_interface.png)


| Question                     | Answer                                               |
| ---------------------------- | -----------------------------------------------------|
|Calculate 1/3 =               | 1/3 is approximately *0.3333* oe about 33.33%....  |
|Who are you?                  | I am a large language model...    |
```
