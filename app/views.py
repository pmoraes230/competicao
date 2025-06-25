from functools import wraps
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.urls import reverse
from . import models

def get_user_profile(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = models.Usuario.objects.select_related('id_perfil').get(id=user_id)
            return {
                'user_id': user.id,
                'user_name': user.nome,
                'user_role': user.id_perfil.nome,
                'is_authenticated': True
            }
        except models.Usuario.DoesNotExist:
            return {'user_name': '', 'is_authenticated': False}
    return {'user_name': '', 'is_authenticated': False}

def role_required(*roles):
    def decorator(view_funv):
        @wraps(view_funv)
        def _wrapped_view(request, *args, **kwargs):
            user_profile = get_user_profile(request)
            user_role = user_profile.get('user_role')

            if not user_profile.get('is_authenticated'):
                messages.error(request, 'Você não está logado')
                return [reverse('login')]

            if user_role not in roles:
                messages.error(request, 'Você não tem permissão para acessar esta página')
                return redirect("login")
            return view_funv(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def login(request):
    if request.method == 'GET':
        return render(request, 'login/login.html')
    
    username = request.POST.get('login')
    password = request.POST.get('password')
    
    if not username or not password:
        messages.error(request, 'Preencha todos os campos')
        return render(request, 'login/login.html')
    
    try:
        user = models.Usuario.objects.get(login=username)
        if check_password(password, user.senha):
            messages.success(request, 'Login realizado com sucesso!')
            request.session['user_id'] = user.id
            return redirect('home')
        else:
            messages.error(request, 'Senha incorreta.')
            return redirect('login')
        
    except models.Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado')
        return render(request, 'login/login.html')
    
    return render(request, 'login/login.html')
    
def logout_view(request):
    logout(request)
    messages.success(request, 'Você saiu do sistema')
    return redirect('login')

@role_required('Administrador', 'Staff', 'Vendedor')
def home(request):
    context = get_user_profile(request)
    context['eventos'] = models.Evento.objects.all()
    return render(request, 'home/home.html', context)

def register_user(request):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_completed = request.POST.get('nome')
        login_user = request.POST.get('login')
        email_user = request.POST.get('email')
        cpf_user = request.POST.get('cpf')
        profile_user = request.POST.get('perfil')
        image_user = request.POST.get('imagem')
        password_user = request.POST.get('password')
        
        if not name_completed or not login_user or not email_user or not cpf_user or not profile_user or not image_user or not password_user:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('register_user')
        
        if models.Usuario.objects.filter(cpf=cpf_user).exists():
            messages.error(request, 'CPF já cadastrado')
            return redirect('register_user')    
        
        if models.Usuario.objects.filter(login=login_user).exists():
            messages.error(request, 'Login já cadastrado')
            return redirect('register_user')
         
        try:
            hashed_password = make_password(password_user)
            profile_id = models.Perfil.objects.get(id=profile_user)
            
            profile = models.Usuario.objects.create(
                nome=name_completed,
                e_mail=email_user,
                login=login_user,
                senha=hashed_password,
                cpf=cpf_user,
                imagem=image_user,
                id_perfil=profile_id
            )
            
            profile.full_clean()
            profile.save()
            
            messages.success(request, 'Usuário salvo com sucesso!')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar usuário {str(ve)}')
            return redirect('register_user')
        
    context.update({
        'categorys': models.Perfil.objects.all()
    })
    return render(request, 'reg_usuario/reg_usuario.html', context)

def register_client(request):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_client = request.POST.get('nome')
        email_client = request.POST.get('email')
        cpf_client = request.POST.get('cpf')
        
        if not name_client or not email_client or not cpf_client:
            messages.error(request, 'Todos os campos são obrigátorios')
            return redirect('registe_client')
        
        if models.Cliente.objects.filter(cpf=cpf_client).exists():
            messages.error(request, 'Cliente já cadastrado!')
            return redirect('registe_client')
        
        try:
            client = models.Cliente.objects.create(
                nome=name_client,
                e_mail=email_client,
                cpf=cpf_client
            )
            client.full_clean()
            client.save()
            
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('registe_client')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar cliente {str(ve)}')
            return redirect('registe_client')
    
    return render(request, 'reg_cliente/reg_cliente.html', context)