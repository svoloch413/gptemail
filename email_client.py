import sys
import getpass
import imaplib
import openai
import email
from email.header import decode_header

def main():
    # Parse command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python email_client.py <email_server_uri>")
        sys.exit(1)

    email_server_uri = sys.argv[1]

    # Get email address, password, and email server URI from the user
    email_address = input("Please enter your email address: ")
    password = getpass.getpass("Please enter your password: ")

    # Connect to the email server (this function will be implemented later)
    email_client = connect_to_email_server(email_address, password, email_server_uri)

    api_key_filename = "api_key"
    try:
        api_key = read_api_key_from_file(api_key_filename)
    except FileNotFoundError:
        print(f"Error: Could not find the API key file '{api_key_filename}'. Make sure it exists in the same directory as the script.")
        sys.exit(1)

    email_text_list = fetch_last_10_unread_emails(email_client)
    response = summarize_emails(api_key, email_text_list)

    # Hardcoded output for now
    print("Sample email summary:")

    print(response)

def connect_to_email_server(email_address, password, email_server_uri):
    try:
        email_client = imaplib.IMAP4_SSL(email_server_uri)
        email_client.login(email_address, password)
        print("Successfully connected to the email server.")
    except Exception as e:
        print("Error connecting to the email server:", e)
        sys.exit(1)

    return email_client

def read_api_key_from_file(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

def talk_to_openai(api_key, prompt, response_length):
    print("Setting up the OpenAI API client...")
    # Set up the OpenAI API client
    openai.api_key = api_key

    print("Creating a prompt for the GPT model...")
    # Create a prompt for the GPT model
    prompt = f"{prompt}"

    print("Sending a request to the OpenAI API...")
    # Send a request to the OpenAI API
    response = openai.Completion.create(
        engine="text-davinci-001",
        prompt=prompt,
        max_tokens=response_length,
        n=1,
        stop=None,
        temperature=0.5,
    )

    print("Extracting the generated text from the response...")
    # Extract the generated text from the response
    generated_text = response.choices[0].text.strip()

    print("Returning the generated text...")
    return generated_text

def summarize_emails(api_key, email_text_list):
    summaries = []
    for index, email_text in enumerate(email_text_list, 1):
        summary = talk_to_openai(api_key, f"Please summarize this email in 100 words:\n{email_text}", 200)
        summaries.append(f"Summary {index}: {summary}\n\n")

    summaries_text = ''.join(summaries)
    print(summaries_text)
    final_summary = talk_to_openai(api_key, f"Please provide a single morning brief-like message that would tell me overall content of my last 10 emails based on short summary descriptions of emails provided here:\n{summaries_text}", 1000)

    return final_summary


def fetch_last_10_unread_emails(email_client):
    email_client.select("inbox")

    status, response = email_client.search(None, "UNSEEN")
    unread_emails = response[0].split()

    last_10_unread_emails = unread_emails[-10:]
    email_texts = []

    for index, email_id in enumerate(last_10_unread_emails, 1):
        status, response = email_client.fetch(email_id, "(RFC822)")
        email_message = email.message_from_bytes(response[0][1])

        sender = email_message["From"]
        decoded_sender, charset = decode_header(sender)[0]
        sender = decoded_sender.decode(charset) if charset else decoded_sender

        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        truncated = False
        tokens = body.split()
        if len(tokens) > 1950:
            body = " ".join(tokens[:1950])
            truncated = True

        email_label = f"Truncated Email {index}" if truncated else f"Email {index}"
        email_text = f"{email_label}:\nFrom: {sender}\nMessage Body:\n{body}\n\n"
        email_texts.append(email_text)

    return email_texts

if __name__ == "__main__":
    main()

