import firebase_admin
from firebase_admin import credentials, firestore

# --- Configurazione per la connessione a Firebase ---

# Sostituisci 'percorso/alla/tua/chiave_privata.json' con il percorso effettivo del tuo file JSON scaricato
cred = credentials.Certificate('key_firebase.json')

# Inizializza l'applicazione Firebase
# Non è necessario specificare databaseURL se usi solo Firestore
firebase_admin.initialize_app(cred)

print("Connessione a Firebase stabilita con successo!")

# --- Interazione con Firestore per visualizzare i pazienti ---

# Ottieni un riferimento al client Firestore
db_firestore = firestore.client()

print("\n--- Visualizzazione dei Pazienti da Firestore ---")

# Ottieni un riferimento alla collezione 'patients'
patients_ref = db_firestore.collection('patients')

# Ottieni tutti i documenti dalla collezione 'patients'
docs = patients_ref.stream()

# Itera attraverso i documenti e stampa i dati di ciascun paziente
if docs:
    for doc in docs:
        print(f"ID Paziente: {doc.id}")
        print(f"Dati: {doc.to_dict()}")
        print("-" * 30) # Linea di separazione per chiarezza
else:
    print("Nessun paziente trovato nella collezione 'patients'.")