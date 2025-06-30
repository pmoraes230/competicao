export const cpfinput = document.getElementById('cpf');
const alert_cpf = document.getElementById('alert_cpf');




cpfinput.addEventListener('input', function(e) {
    let value = e.target.value;
    let cpfPattern = value.replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1-$2')
    .replace(/(-\d{2})\d+?$/, '$1')

    e.target.value = cpfPattern
});

cpfinput.addEventListener('change', function() {
    if(!validCPF(cpfinput.value)) {
        alert_cpf.innerHTML = "CPF Invalido"
        alert_cpf.removeAttribute("style");
    } else {
        alert_cpf.innerHTML = "CPF Válido"
        alert_cpf.removeAttribute("style");
    }
});


export function validCPF(cpf) {
    cpf = String(cpf).replace(/\D+/g, '');

    if(cpf.length != 11) return false;

    let soma = 0;
    let resto;

    if(/^(\d)\1{10}$/.test(cpf)) return false;

    for(let i = 1; i <= 9; i++) soma += parseInt(cpf.substring(i-1, i)) * (11 - i);
    resto = (soma * 10) % 11;
    if ((resto === 10) || (resto === 11)) resto = 0;
    if (resto !== parseInt(cpf.substring(9, 10))) return false;

    soma = 0
    for(let i = 1; i <= 10; i++) soma += parseInt(cpf.substring(i-1, i)) * (12 - i);
    resto = (soma * 10) % 11;
    if(resto !== parseInt(cpf.substring(10, 11))) return false;

    return true
}