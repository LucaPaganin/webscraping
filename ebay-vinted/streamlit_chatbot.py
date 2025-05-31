import os
import streamlit as st
import openai
import pandas as pd
from dotenv import load_dotenv
import os  
import base64
from openai import AzureOpenAI  

# Carica le variabili di ambiente dal file .env
load_dotenv()

def ask_gpt(deployment, messages):
    # Generare il completamento
    client = st.session_state.client
    completion = client.chat.completions.create(  
        model=deployment,
        messages=messages,
        temperature=0.7,
        top_p=1
    )
    return completion.choices[0].message.content.strip()
    

# Funzione principale per configurare la pagina del chatbot
def chatbot_page():
    st.title("Chatbot Multimodale")
    st.write("Interagisci con il chatbot e carica file CSV per analisi.")
    
    deployment = st.selectbox(
        label="Seleziona un modello",
        options=["gpt-4o", "gpt-4o-mini"],
        index=0,
        help="Scegli un'opzione dal menu a discesa."
    )
    
    endpoint = 'https://luca-m91hxv95-eastus2.cognitiveservices.azure.com/'
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "REPLACE_WITH_YOUR_KEY_VALUE_HERE")  

    # Inizializzare il client del Servizio OpenAI di Azure con l'autenticazione basata su chiave    
    if "client" not in st.session_state:
        st.session_state.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=subscription_key,
            api_version='2025-01-01-preview'
        )
    
    # Inizializza la cronologia dei messaggi nella sessione
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": "Sei un assistente utile."}]

    # Mostra la cronologia dei messaggi
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("assistant").write(message["content"])

    # Input per il messaggio dell'utente
    user_message = st.chat_input("Scrivi un messaggio:")
    if user_message:
        # Aggiungi il messaggio dell'utente alla cronologia
        st.session_state.messages.append({"role": "user", "content": user_message})
        # Mostra il messaggio dell'utente
        st.chat_message("user").write(user_message)
        # Ottieni la risposta dal modello
        response = ask_gpt(deployment, st.session_state.messages)
        # Aggiungi la risposta del modello alla cronologia
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Mostra la risposta
        st.chat_message("assistant").write(response)

    # Area per il caricamento di file CSV
    uploaded_file = st.file_uploader("Carica un file CSV", type=["csv"])
    if uploaded_file is not None:
        if st.button("Analizza CSV"):
            try:
                # Leggi il file CSV
                df = pd.read_csv(uploaded_file)
                # Converti il contenuto del CSV in una stringa
                csv_string = df.to_string(index=False)
                st.write("Contenuto del CSV:")
                st.write(csv_string)
                # Invia il contenuto al chatbot
                st.session_state.messages.append({"role": "user", "content": f"Analizza il seguente dataset:\n{csv_string}"})
                response = ask_gpt(deployment, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
            except Exception as e:
                st.error(f"Errore durante l'analisi del file: {e}")

# Esegui la funzione per configurare la pagina
if __name__ == "__main__":
    chatbot_page()