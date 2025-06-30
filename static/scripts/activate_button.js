import {validCPF, cpfinput} from "./valid_cpf.js"
// import {password_confirmation, password_confirm} from './see_password.js'
const btn_confirm = document.getElementById('btn_post');



cpfinput.addEventListener('change', function() {  
    if (!validCPF(cpfinput.value)){
        btn_confirm.setAttribute("disabled", "");
        btn_confirm.classList.remove("bg_verde", "color_cinza");
    }else{
        btn_confirm.removeAttribute("disabled");
        btn_confirm.classList.add("bg_verde", "color_cinza");
    }
});
