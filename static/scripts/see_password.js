document.addEventListener('DOMContentLoaded', function(){
    const password = document.getElementById('password');
    const button_pass = document.getElementById('toggle-pass');
    const eye = document.getElementById('eye');
    const btn_confirm_pass = document.getElementById('btn_post');
    const message_alert = document.getElementById('alert_password');
    
    // Confirmar senha
    const password_confirm = document.getElementById('password_confirm');
    const btn_confirm_password = document.getElementById('toggle_pass_confirm');
    const eye_confirm = document.getElementById('eye_confirm');
    
    password_confirm.addEventListener('change', function() {
        if(password.value != password_confirm.value) {
            message_alert.innerHTML = "Senhas diferentes"
            message_alert.classList.remove('display_visibled');
    
        } else {
            message_alert.classList.add("display_visibled");
    
        }
    });
    
    // Ver senha
    eye.addEventListener('click', function() {
        if(password.type == 'password') {
            password.type = 'text';
            eye.src = "static/icons/eye.svg";
        } else {
            password.type = 'password';
            eye.src = "static/icons/eye-slash.svg";
        }
    })
    
    // Ver senha confirmar
    eye_confirm.addEventListener('click', function() {
        if(password_confirm.type == 'password') {
            password_confirm.type = 'text';
            eye_confirm.src = "static/icons/eye.svg";
        } else {
            password_confirm.type = 'password';
            password_confirm.src = "static/icons/eye-slash.svg";
        }
    })
})
