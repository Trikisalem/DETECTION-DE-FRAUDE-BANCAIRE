from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime
from flask_cors import CORS  # Importer Flask-CORS

FRAUD_FILE = 'fraudes.json'
MODEL_PATH = 'model'

# Créer l'application Flask
app = Flask(__name__)

# Configuration CORS plus détaillée
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000", "methods": ["GET", "POST", "OPTIONS"], 
                              "allow_headers": ["Content-Type", "Authorization"]}})

# Fonction pour enregistrer les fraudes détectées
def enregistrer_fraude(transaction_data):
    transaction_data["timestamp"] = datetime.now().isoformat()
    if os.path.exists(FRAUD_FILE):
        with open(FRAUD_FILE, 'r', encoding='utf-8') as f:
            try:
                fraudes = json.load(f)
            except json.JSONDecodeError:
                fraudes = []
    else:
        fraudes = []

    fraudes.append(transaction_data)

    with open(FRAUD_FILE, 'w', encoding='utf-8') as f:
        json.dump(fraudes, f, ensure_ascii=False, indent=4)

# Fonction pour charger le modèle et les outils
def load_model():
    try:
        model = joblib.load(os.path.join(MODEL_PATH, 'random_forest_model.pkl'))
        label_encoders = joblib.load(os.path.join(MODEL_PATH, 'label_encoders.pkl'))
        scaler = joblib.load(os.path.join(MODEL_PATH, 'scaler.pkl'))
        
        # Debug: Afficher les noms des caractéristiques attendues
        if hasattr(model, 'feature_names_in_'):
            print("Caractéristiques attendues par le modèle:", model.feature_names_in_)
        
        return model, label_encoders, scaler
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        return None, None, None

# Charger les modèles au démarrage
model, label_encoders, scaler = load_model()

@app.route('/')
def index():
    return render_template('index.html')

def prepare_data(data):
    # Créer une copie des données pour éviter de modifier l'original
    data_copy = data.copy()
    
    # Normalisation des clés: s'assurer que nous avons 'étype' et non 'type'
    if 'type' in data_copy and 'étype' not in data_copy:
        data_copy['étype'] = data_copy.pop('type')
    
    # Créer un DataFrame à partir des données
    df = pd.DataFrame([data_copy])
    
    # Créer les colonnes dérivées pour la détection de fraude
    df['fraude_montant_negatif'] = df['montant'].apply(lambda x: 1 if x < 0 else 0)
    df['fraude_diff_montant_send'] = ((df['new_solde_send'] - df['ancien_solde_send']) != -df['montant']).astype(int)
    df['fraude_diff_montant_dest'] = ((df['new_solde_dest'] - df['ancien_solde_dest']) != df['montant']).astype(int)

    # Créer un DataFrame vide avec toutes les colonnes attendues et dans le bon ordre
    # Ajouter les colonnes attendues si nous connaissons les caractéristiques du modèle
    expected_columns = None
    if hasattr(model, 'feature_names_in_'):
        expected_columns = list(model.feature_names_in_)
    else:
        # Si nous ne connaissons pas les caractéristiques, utiliser celles que nous avons
        expected_columns = ['étype', 'montant', 'code_nom_send', 'ancien_solde_send', 'new_solde_send', 
                           'code_nom_dest', 'ancien_solde_dest', 'new_solde_dest', 'pays_send', 'pays_dest',
                           'fraude_montant_negatif', 'fraude_diff_montant_send', 'fraude_diff_montant_dest']
    
    # Créer un dataframe vide avec les colonnes attendues
    df_prepared = pd.DataFrame(columns=expected_columns)
    
    # Remplir avec les données disponibles
    for col in expected_columns:
        if col in df.columns:
            df_prepared[col] = df[col]
        else:
            # Si la colonne est manquante, la créer avec des valeurs par défaut
            print(f"Colonne '{col}' manquante, ajout avec valeur par défaut")
            if col in ['fraude_montant_negatif', 'fraude_diff_montant_send', 'fraude_diff_montant_dest']:
                df_prepared[col] = 0  # Valeur par défaut pour les indicateurs de fraude
            else:
                df_prepared[col] = ''  # Chaîne vide pour les autres colonnes
    
    # Debug: Afficher les colonnes pour vérification
    print("Colonnes du DataFrame avant encodage:", df_prepared.columns.tolist())
    
    # Encodage des variables catégorielles
    for col, encoder in label_encoders.items():
        if col in df_prepared.columns:
            try:
                df_prepared[col] = encoder.transform(df_prepared[col])
            except ValueError as e:
                print(f"Erreur d'encodage pour '{col}': {e}")
                # Utiliser la valeur la plus fréquente en cas d'erreur
                most_frequent = encoder.classes_[0]
                df_prepared[col] = encoder.transform([most_frequent] * len(df_prepared))

    # Mise à l'échelle des colonnes numériques
    numeric_columns = ['montant', 'ancien_solde_send', 'new_solde_send', 'ancien_solde_dest', 'new_solde_dest']
    numeric_columns_present = [col for col in numeric_columns if col in df_prepared.columns]
    if numeric_columns_present:
        df_prepared[numeric_columns_present] = scaler.transform(df_prepared[numeric_columns_present])

    # Debug: Afficher les colonnes après transformation
    print("Colonnes du DataFrame après transformation:", df_prepared.columns.tolist())
    
    return df_prepared

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or label_encoders is None or scaler is None:
        return "Model or resources not loaded correctly, please check the logs.", 500

    # Récupérer les données du formulaire
    data = {
        'étype': request.form.get('étype', request.form.get('type', '')),
        'montant': float(request.form['montant']),
        'code_nom_send': request.form['code_nom_send'],
        'ancien_solde_send': float(request.form['ancien_solde_send']),
        'new_solde_send': float(request.form['new_solde_send']),
        'code_nom_dest': request.form['code_nom_dest'],
        'ancien_solde_dest': float(request.form['ancien_solde_dest']),
        'new_solde_dest': float(request.form['new_solde_dest']),
        'pays_send': request.form['pays_send'],
        'pays_dest': request.form['pays_dest']
    }

    df_encoded = prepare_data(data)

    # Prédiction
    prediction = model.predict(df_encoded)[0]
    probability = model.predict_proba(df_encoded)[0][1]

    # Facteurs de risque
    risk_factors = []
    if 'fraude_montant_negatif' in df_encoded and df_encoded['fraude_montant_negatif'].values[0]: 
        risk_factors.append("Montant négatif détecté")
    if 'fraude_diff_montant_send' in df_encoded and df_encoded['fraude_diff_montant_send'].values[0]: 
        risk_factors.append("Incohérence dans le solde de l'expéditeur")
    if 'fraude_diff_montant_dest' in df_encoded and df_encoded['fraude_diff_montant_dest'].values[0]: 
        risk_factors.append("Incohérence dans le solde du destinataire")

    if prediction == 1:
        enregistrer_fraude(data)

    result = {
        'prediction': int(prediction),
        'probability': float(probability) * 100,
        'risk_factors': risk_factors,
        'transaction': data
    }

    return render_template('result.html', result=result)

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def api_predict():
    # Ajout des en-têtes CORS manuellement pour plus de contrôle
    response_headers = {
        'Access-Control-Allow-Origin': 'http://localhost:3000',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    # Gérer les requêtes OPTIONS pour les requêtes préalables CORS
    if request.method == 'OPTIONS':
        return '', 200, response_headers
        
    if model is None or label_encoders is None or scaler is None:
        return jsonify({"error": "Model or resources not loaded correctly, please check the logs."}), 500

    try:
        print("Requête API reçue")
        data = request.json
        print(f"Données reçues: {data}")
        
        if not data:
            return jsonify({"error": "Données invalides ou manquantes"}), 400
            
        # Préparation des données
        df_encoded = prepare_data(data)
        
        # Vérifier si les données sont correctement préparées
        if df_encoded.empty:
            return jsonify({"error": "Erreur lors de la préparation des données"}), 500

        # Prédiction
        print("Exécution de la prédiction")
        prediction = model.predict(df_encoded)[0]
        probability = model.predict_proba(df_encoded)[0][1]
        print(f"Résultat de la prédiction: {prediction}, probabilité: {probability}")

        # Facteurs de risque
        risk_factors = []
        if 'fraude_montant_negatif' in df_encoded and df_encoded['fraude_montant_negatif'].values[0]: 
            risk_factors.append("Montant négatif détecté")
        if 'fraude_diff_montant_send' in df_encoded and df_encoded['fraude_diff_montant_send'].values[0]: 
            risk_factors.append("Incohérence dans le solde de l'expéditeur")
        if 'fraude_diff_montant_dest' in df_encoded and df_encoded['fraude_diff_montant_dest'].values[0]: 
            risk_factors.append("Incohérence dans le solde du destinataire")

        if prediction == 1:
            enregistrer_fraude(data)

        result = {
            'prediction': int(prediction),
            'probability': float(probability) * 100,
            'risk_factors': risk_factors
        }

        print(f"Résultat final: {result}")
        response = jsonify(result)
        
        # Ajouter les en-têtes CORS à la réponse
        for key, value in response_headers.items():
            response.headers.add(key, value)
            
        return response
        
    except Exception as e:
        print(f"Erreur lors du traitement de la prédiction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

if __name__ == '__main__':
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH)
        print(f"Dossier {MODEL_PATH} créé. Veuillez y placer les fichiers du modèle.")
    
    # Lancer le serveur Flask - s'assurer qu'il est accessible depuis l'extérieur
    app.run(debug=True, host='0.0.0.0')