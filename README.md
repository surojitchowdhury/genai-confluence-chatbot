# genai-confluence-chatbot
GenAI based chatbot to talk to multiple confluence pages of organizations

`pip install -r requirements.txt`

Chatbot has registration feature with MFA. So that only organisation employees can access.

Update the code with your organization details.

Use `.env` file to keep all environment variables.

Run as simple Flask application and host on any server.

Answers are returned with source page details so that it can be verified.

Use Cases:
 - Access all organisation documentation using simple chatbot.
 - Secured using MFA
 - RAG based application
 - Source can be verified with actual page.