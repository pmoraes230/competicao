const priceInput = document.getElementById('price');

priceInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
    if (value.length > 0) {
        // Converte para valor monetário (R$ com duas casas decimais)
        value = (parseFloat(value) / 100).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });
        e.target.value = value;
    } else {
        e.target.value = ''; // Limpa se não houver valor
    }
});

// Opcional: Remover formatação ao enviar o formulário (se necessário)
priceInput.addEventListener('change', function(e) {
    let value = e.target.value.replace(/[^\d]/g, ''); // Remove tudo exceto dígitos
    if (value) {
        e.target.value = value; // Deixa apenas o número para o backend (ex.: 1000)
    }
});