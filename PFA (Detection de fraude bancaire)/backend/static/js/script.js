document.addEventListener("DOMContentLoaded", () => {
    // Calcul automatique du nouveau solde de l'expéditeur
    const montantInput = document.getElementById("montant")
    const ancienSoldeSendInput = document.getElementById("ancien_solde_send")
    const newSoldeSendInput = document.getElementById("new_solde_send")
  
    function updateNewSoldeSend() {
      if (montantInput.value && ancienSoldeSendInput.value) {
        const montant = Number.parseFloat(montantInput.value)
        const ancienSolde = Number.parseFloat(ancienSoldeSendInput.value)
        newSoldeSendInput.value = (ancienSolde - montant).toFixed(2)
      }
    }
  
    montantInput.addEventListener("input", updateNewSoldeSend)
    ancienSoldeSendInput.addEventListener("input", updateNewSoldeSend)
  
    // Calcul automatique du nouveau solde du destinataire
    const ancienSoldeDestInput = document.getElementById("ancien_solde_dest")
    const newSoldeDestInput = document.getElementById("new_solde_dest")
  
    function updateNewSoldeDest() {
      if (montantInput.value && ancienSoldeDestInput.value) {
        const montant = Number.parseFloat(montantInput.value)
        const ancienSolde = Number.parseFloat(ancienSoldeDestInput.value)
        newSoldeDestInput.value = (ancienSolde + montant).toFixed(2)
      }
    }
  
    montantInput.addEventListener("input", updateNewSoldeDest)
    ancienSoldeDestInput.addEventListener("input", updateNewSoldeDest)
  
    // Validation du formulaire
    const form = document.querySelector("form")
    form.addEventListener("submit", (event) => {
      let isValid = true
  
      // Vérification que tous les champs sont remplis
      const requiredInputs = form.querySelectorAll("[required]")
      requiredInputs.forEach((input) => {
        if (!input.value.trim()) {
          isValid = false
          input.classList.add("is-invalid")
        } else {
          input.classList.remove("is-invalid")
        }
      })
  
      if (!isValid) {
        event.preventDefault()
        alert("Veuillez remplir tous les champs obligatoires.")
      }
    })
  })
  