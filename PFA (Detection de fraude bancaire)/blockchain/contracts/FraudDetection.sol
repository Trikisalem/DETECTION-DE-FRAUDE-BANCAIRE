// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FraudDetection {
    // Structure pour stocker les transactions
    struct Transaction {
        address from;
        address to;
        uint256 amount;
        uint256 timestamp;
        bool flaggedAsFraud;
        string transactionType;
        string details;
    }
    
    // Mapping des transactions par ID
    mapping(uint256 => Transaction) public transactions;
    uint256 public transactionCount;
    
    // Mapping des adresses reportées comme frauduleuses
    mapping(address => bool) public reportedAddresses;
    
    // Événements
    event TransactionRecorded(uint256 indexed id, address indexed from, address indexed to, uint256 amount);
    event FraudReported(uint256 indexed transactionId, address reporter);
    event AddressFlagged(address indexed suspiciousAddress, address reporter);
    
    // Modifier pour restreindre l'accès aux autorités bancaires
    modifier onlyBankAuthority() {
        // Dans un environnement réel, vous implémenteriez ici un système de contrôle d'accès
        // Pour cet exemple, nous supposons que n'importe qui peut être une autorité
        _;
    }
    
    // Enregistrer une nouvelle transaction et transférer ETH
    function recordTransaction(
        address _from, 
        address _to, 
        uint256 _amount, 
        string memory _transactionType,
        string memory _details
    ) public payable returns (uint256) {
        require(_from == msg.sender, "Sender must be the caller");
        require(_to != address(0), "Invalid recipient address");
        require(_amount > 0, "Amount must be greater than 0");
        require(msg.value == _amount, "Sent ETH must match the amount");

        // Transfer ETH to the recipient
        (bool sent, ) = _to.call{value: msg.value}("");
        require(sent, "Failed to send ETH");

        uint256 transactionId = transactionCount;
        
        transactions[transactionId] = Transaction({
            from: _from,
            to: _to,
            amount: _amount,
            timestamp: block.timestamp,
            flaggedAsFraud: false,
            transactionType: _transactionType,
            details: _details
        });
        
        transactionCount++;
        
        emit TransactionRecorded(transactionId, _from, _to, _amount);
        
        // Vérification automatique pour détecter des fraudes potentielles
        checkForFraudPatterns(transactionId);
        
        return transactionId;
    }
    
    // Signaler une transaction comme frauduleuse
    function reportFraud(uint256 _transactionId) public onlyBankAuthority {
        require(_transactionId < transactionCount, "Transaction does not exist");
        
        Transaction storage transaction = transactions[_transactionId];
        transaction.flaggedAsFraud = true;
        
        // Marquer l'adresse comme suspecte
        reportedAddresses[transaction.from] = true;
        
        emit FraudReported(_transactionId, msg.sender);
    }
    
    // Vérifier les modèles de fraude potentiels
    function checkForFraudPatterns(uint256 _transactionId) internal {
        Transaction storage transaction = transactions[_transactionId];
        
        // Vérifier si l'adresse a déjà été signalée comme frauduleuse
        if (reportedAddresses[transaction.from]) {
            transaction.flaggedAsFraud = true;
        }
        
        // D'autres vérifications pourraient être ajoutées ici:
        // - Transactions multiples en peu de temps
        // - Montants inhabituels
        // - Destinations suspectes
        // etc.
    }
    
    // Obtenir les détails d'une transaction
    function getTransaction(uint256 _transactionId) public view returns (
        address from,
        address to,
        uint256 amount,
        uint256 timestamp,
        bool flaggedAsFraud,
        string memory transactionType,
        string memory details
    ) {
        require(_transactionId < transactionCount, "Transaction does not exist");
        Transaction memory transaction = transactions[_transactionId];
        
        return (
            transaction.from,
            transaction.to,
            transaction.amount,
            transaction.timestamp,
            transaction.flaggedAsFraud,
            transaction.transactionType,
            transaction.details
        );
    }
    
    // Vérifier si une adresse est signalée comme frauduleuse
    function isAddressFlagged(address _address) public view returns (bool) {
        return reportedAddresses[_address];
    }
    
    // Obtenir le nombre total de transactions
    function getTransactionCount() public view returns (uint256) {
        return transactionCount;
    }

    // Fallback function to receive ETH
    receive() external payable {}
}