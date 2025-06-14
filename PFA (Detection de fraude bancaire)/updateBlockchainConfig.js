
const fs = require('fs');
const path = require('path');

// Chemins des fichiers
const artifactPath = path.join(__dirname, 'frontend/src/contracts/FraudDetection.json');
const configPath = path.join(__dirname, 'frontend/public/blockchain_config.json');

// Fonction pour mettre à jour blockchain_config.json
function updateBlockchainConfig() {
  try {
    // Lire l'artefact FraudDetection.json
    const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
    const networkId = '1337'; // Ganache network ID
    const contractAddress = artifact.networks[networkId]?.address;

    if (!contractAddress) {
      throw new Error(`Aucune adresse de contrat trouvée pour le réseau ${networkId} dans ${artifactPath}`);
    }

    // Créer ou mettre à jour blockchain_config.json
    const config = {
      contract_address: contractAddress
    };

    // Écrire dans blockchain_config.json
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
    console.log(`blockchain_config.json mis à jour avec l'adresse : ${contractAddress}`);
  } catch (err) {
    console.error('Erreur lors de la mise à jour de blockchain_config.json :', err.message);
    process.exit(1);
  }
}

// Exécuter la fonction
updateBlockchainConfig();