// Seleciona os campos de entrada
const limit_peaple = document.getElementById('peaple_limit');
const limit_seats = document.getElementById('limit_seats');
const priceInput = document.getElementById('price');

// Função para formatar números inteiros (remove qualquer caractere não numérico)
const handleIntegerInput = (e) => {
    let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
    e.target.value = value || ''; // Define o valor ou vazio se não houver dígitos
};

// Função para formatar o campo de preço (exibe como R$ no frontend, envia como decimal)
const handlePriceInput = (e) => {
    let value = e.target.value.replace(/[^\d]/g, ''); // Remove tudo exceto dígitos
    if (value.length > 0) {
        // Converte para número decimal (divide por 100 para duas casas decimais)
        value = (parseFloat(value) / 100).toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        e.target.value = value;
    } else {
        e.target.value = ''; // Limpa se não houver valor
    }
};

// Função para preparar o valor do preço para envio ao backend
const handlePriceSubmit = (e) => {
    let value = e.target.value.replace(/[^\d]/g, ''); // Remove tudo exceto dígitos
    if (value) {
        // Converte para formato decimal com ponto (ex.: 200000 -> 2000.00)
        value = (parseFloat(value) / 100).toFixed(2).replace('.', '.');
        e.target.value = value;
    } else {
        e.target.value = ''; // Limpa se não houver valor
    }
};

// Aplica máscara para números inteiros nos campos limit_peaple e limit_seats
[limit_peaple, limit_seats].forEach(element => {
    if (element) {
        element.addEventListener('input', handleIntegerInput);
    }
});

// Aplica máscara para o campo de preço
if (priceInput) {
    priceInput.addEventListener('input', handlePriceInput);
}

// Prepara os valores para envio ao submeter o formulário
document.querySelector('form').addEventListener('submit', (e) => {
    if (priceInput) {
        handlePriceSubmit({ target: priceInput }); // Formata o preço para o backend
    }
    // Não precisa formatar limit_peaple e limit_seats, pois já são inteiros
});