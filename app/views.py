from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.db.models import Sum
from django.http import HttpResponseRedirect
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
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_profile = get_user_profile(request)
            
            if not user_profile or not isinstance(user_profile, dict):
                messages.error(request, 'Erro ao verificar sua sessão. Faça login novamente.')
                return redirect(reverse('login'))

            # Verifica autenticação
            if not user_profile.get('is_authenticated', False):
                messages.error(request, 'Você não está logado.')
                return redirect(reverse('login'))

            # Verifica permissão
            user_profile = get_user_profile(request)
            if user_profile.get('user_role') not in roles:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('home')
            return view_func(request, *args, **kwargs)  

            return view_func(request, *args, **kwargs)
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

@role_required('Administrador', 'Staff')
def register_client(request, id):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_client = request.POST.get('nome')
        email_client = request.POST.get('email')
        cpf_client = request.POST.get('cpf')
        
        if not name_client or not email_client or not cpf_client:
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect(reverse('register_client', args=[id]))
        
        if models.Cliente.objects.filter(cpf=cpf_client).exists():
            messages.error(request, 'Cliente já cadastrado!')
            return redirect(reverse('register_client', args=[id]))
        
        try:
            client = models.Cliente.objects.create(
                nome=name_client,
                e_mail=email_client,
                cpf=cpf_client
            )
            client.full_clean()
            client.save()
            
            messages.success(request, 'Cliente cadastrado com sucesso!')
            # Armazenar o cliente_id na sessão e redirecionar para a compra
            request.session['cliente_id'] = client.id
            return redirect(reverse('buy_ticket', args=[id]))
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar cliente: {str(ve)}')
            return redirect(reverse('register_client', args=[id]))
    
    # Adicionar o event_id ao contexto para uso no template
    context['event_id'] = id
    return render(request, 'reg_cliente/reg_cliente.html', context)

def register_profile(request):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_profile = request.POST.get('nome')
        description = request.POST.get('descricao')
        
        if not name_profile or not description:
            messages.error(request, 'Todos os campos são obrigatórios')
            return redirect('register_profile')
        
        try:
            profile = models.Perfil.objects.create(
                nome=name_profile,
                descricao=description
            )
            profile.full_clean()
            profile.save()
            
            messages.success(request, 'Perfil salvo com sucesso!')
            return redirect('register_profile')
            
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar perfil {str(ve)}')
            return redirect('register_profile')
        
    return render(request, 'perfil/reg_perfil.html', context)

@role_required('Administrador', 'Staff')
def register_events(request):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_event = request.POST.get('nome')
        date_event = request.POST.get('date')
        hour_event = request.POST.get('hour')
        image_event = request.POST.get('imagem')
        price_event = request.POST.get('price')
        limit_peaple = request.POST.get('peaple_limit')
        adress = request.POST.get('adress')
        description = request.POST.get('descricao')
        
        if not name_event or not date_event or not hour_event or not image_event or not price_event or not limit_peaple or not adress or not description:
            messages.error(request, 'Todos os campos são obrigatórios')
            return redirect('register_events')
        
        if models.Evento.objects.filter(nome=name_event).exists():
            messages.error(request, 'Evento já existente.')
            return redirect('register_events')
        
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                messages.error(request, 'Usuário não autenticado.')
                return redirect('login')
            
            event = models.Evento.objects.create(
                nome=name_event,
                data_evento=date_event,
                horario=hour_event,
                cpt_pessoas=limit_peaple,
                imagem=image_event,
                preco_evento=price_event,
                local_evento=adress,
                id_usuario_id=user_id
            )
            event.full_clean()
            event.save()
            
            request.session['last_event_id'] = event.id
            messages.success(request, 'Evento salvo com sucesso!')
            return redirect('register_setor')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar evento {str(ve)}')
            return redirect('register_events')
    
    return render(request, 'reg_eventos/reg_evento.html', context)

@role_required('Administrador', 'Staff')
def register_setor(request):
    context = get_user_profile(request)
    event_id = request.session.get('last_event_id')

    if not event_id:
        messages.error(request, 'Nenhum evento criado. Crie um evento primeiro.')
        return redirect('register_events')

    if request.method == 'POST':
        setores_data = []
        nome_setores = request.POST.getlist('nome_setor[]')  # Lista de nomes
        limit_seats = request.POST.getlist('limit_seats[]')  # Lista de quantidades

        if not nome_setores or not limit_seats:
            messages.error(request, 'Pelo menos um setor deve ser preenchido.')
            return redirect('register_setor')

        try:
            event = models.Evento.objects.get(id=event_id)
            total_existing_seats = models.Setor.objects.filter(id_evento_id=event_id).aggregate(total=Sum('qtd_cadeira'))['total'] or 0
            total_new_seats = sum(float(seat) for seat in limit_seats if seat)

            if total_existing_seats + total_new_seats > event.cpt_pessoas:
                messages.error(request, f'A soma das cadeiras ({total_existing_seats + total_new_seats}) excede o limite de pessoas do evento ({event.cpt_pessoas}).')
                return redirect('register_setor')

            for nome, seats in zip(nome_setores, limit_seats):
                if nome and seats:  # Só cria se ambos os campos estiverem preenchidos
                    setor = models.Setor.objects.create(
                        nome=nome,
                        qtd_cadeira=float(seats),
                        id_evento_id=event_id
                    )
                    setor.full_clean()
                    setor.save()
                    setores_data.append({'nome': nome, 'seats': seats})

            messages.success(request, f'{len(setores_data)} setor(es) cadastrado(s) com sucesso!')
            return redirect('register_setor')
        except models.Evento.DoesNotExist:
            messages.error(request, 'Evento não encontrado.')
            return redirect('register_events')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar setor: {str(ve)}')
            return redirect('register_setor')

    # Preenche o contexto com o evento
    try:
        event = models.Evento.objects.get(id=event_id)
        context['event'] = event
        context['remaining_seats'] = max(0, event.cpt_pessoas - (models.Setor.objects.filter(id_evento_id=event_id).aggregate(total=Sum('qtd_cadeira'))['total'] or 0))
    except models.Evento.DoesNotExist:
        del request.session['last_event_id']
        messages.error(request, 'Evento não encontrado.')
        return redirect('register_events')

    return render(request, 'reg_setor/reg_setor.html', context)

@role_required('Administrador', 'Staff')  # Adicione o decorador para restringir acesso
def edit_event(request, id):
    context = get_user_profile(request)
    
    try:
        update_event = models.Evento.objects.get(id=id)
    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('register_events')

    if request.method == 'POST':
        name_event = request.POST.get('nome')
        date_event = request.POST.get('date')
        hour_event = request.POST.get('hour')
        image_event = request.FILES.get('imagem')
        price_event = request.POST.get('price')
        limit_peaple = request.POST.get('peaple_limit')
        adress = request.POST.get('adress')
        
        # Converte vírgulas para pontos nos campos numéricos
        try:
            if limit_peaple:
                limit_peaple = float(limit_peaple.replace(',', '.'))  # Converte "5000,0" para 5000.0
            if price_event:
                price_event = float(price_event.replace(',', '.'))  # Converte "2000,00" para 2000.00
        except ValueError as ve:
            messages.error(request, 'Formato inválido para preço ou limite de pessoas.')
            return redirect('edit_event', id=id)

        try:
            user_id = request.session.get('user_id')
            if not user_id:
                messages.error(request, 'Usuário não autenticado.')
                return redirect('login')
            
            update_event.nome = name_event
            update_event.data_evento = date_event
            update_event.horario = hour_event
            update_event.cpt_pessoas = limit_peaple
            if image_event:
                update_event.imagem = image_event
            update_event.local_evento = adress
            update_event.preco_evento = price_event
            update_event.id_usuario_id = user_id  # Ajuste para id_usuario_id

            update_event.full_clean()
            update_event.save()
            
            messages.success(request, 'Evento atualizado')
            return HttpResponseRedirect(reverse('edit_event', args=[int(id)]))
        except ValueError as ve:
            messages.error(request, f'Erro ao atualizar evento: {str(ve)}')
            return redirect('edit_event', id=id)

    # Adiciona o evento ao contexto para o formulário
    context['event'] = update_event
    
    return render(request, 'reg_eventos/edit_evento.html', context)

@role_required('Administrador', 'Staff')
def delete_event(request, id):
    try:
        event = models.Evento.objects.get(id=id)
        
        if request.method == 'POST':
            event.delete()
            messages.success(request, 'Evento excluído com sucesso!')
            return redirect('home')
        
        context = {
            'event': event,
            **get_user_profile(request)
        }
        
        return render(request, 'reg_eventos/delete_evento.html', context)
    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')


@role_required('Cliente', 'Administrador', 'Staff')
def buy_ticket(request, event_id):
    try:
        event = models.Evento.objects.get(id=event_id)
        setores = models.Setor.objects.filter(id_evento_id=event_id)

        # Combinar data_evento e horario em um datetime com fuso horário
        if event.horario:
            combined_datetime = timezone.make_aware(timezone.datetime.combine(event.data_evento.date(), event.horario))
            event.data_evento = timezone.localtime(combined_datetime)
        elif isinstance(event.data_evento, timezone.datetime):
            event.data_evento = timezone.localtime(event.data_evento)
        else:
            event.data_evento = timezone.make_aware(timezone.datetime.combine(event.data_evento, timezone.datetime.min.time()))

        if request.method == 'POST':
            setor_id = request.POST.get('setor')
            quantidade = int(request.POST.get('quantidade', 1))

            if not setor_id:
                messages.error(request, 'Por favor, selecione um setor.')
                return redirect(reverse('buy_ticket', args=[event_id]))

            setor = models.Setor.objects.get(id=setor_id)

            if quantidade < 1:
                messages.error(request, 'A quantidade deve ser pelo menos 1.')
                return redirect(reverse('buy_ticket', args=[event_id]))

            if setor.qtd_cadeira < quantidade:
                messages.error(request, f'Só há {setor.qtd_cadeira} cadeiras disponíveis neste setor.')
                return redirect(reverse('buy_ticket', args=[event_id]))

            cliente_id = request.session.get('cliente_id')
            if not cliente_id:
                messages.error(request, 'Por favor, cadastre-se antes de comprar.')
                return redirect(reverse('register_client', args=[event_id]))

            cliente = models.Cliente.objects.get(id=cliente_id)

            if setor.qtd_cadeira >= quantidade:
                for _ in range(quantidade):
                    venda = models.Venda(
                        id_evento=event,
                        id_cliente=cliente,
                        data_venda=timezone.now(),
                        valor=event.preco_evento or 0.00
                    )
                    venda.save()
                    setor.qtd_cadeira -= 1
                    setor.save()

                qr_data = f"Evento: {event.nome}\nCliente: {cliente.nome}\nCPF: {cliente.cpf}\nData: {venda.data_venda}\nValor: R${venda.valor} (x{quantidade} ingressos)"
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                ticket_file = ContentFile(buffer.getvalue(), name=f'ticket_{venda.id}.png')

                messages.success(request, f'Compra de {quantidade} ingresso(s) realizada com sucesso! Baixe seu ticket abaixo.')
                response = HttpResponse(buffer.getvalue(), content_type='image/png')
                response['Content-Disposition'] = f'attachment; filename=ticket_{venda.id}.png'
                return response
            else:
                messages.error(request, 'Não há cadeiras suficientes disponíveis neste setor.')
                return redirect(reverse('buy_ticket', args=[event_id]))

        cliente_id = request.session.get('cliente_id')
        cliente = models.Cliente.objects.get(id=cliente_id) if cliente_id else None

        context = {
            'event': event,
            'setores': setores,
            'cliente': cliente,
        }
        return render(request, 'reg_eventos/detalhes_evento.html', context)

    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')
    except models.Cliente.DoesNotExist:
        messages.error(request, 'Cliente não encontrado. Por favor, cadastre-se novamente.')
        return redirect(reverse('register_client', args=[event_id]))

# Ajuste a view event_details
def event_details(request, id):
    try:
        event = models.Evento.objects.get(id=id)
        # Combinar data_evento e horario em um datetime com fuso horário
        if event.horario:
            combined_datetime = timezone.make_aware(timezone.datetime.combine(event.data_evento.date(), event.horario))
            event.data_evento = timezone.localtime(combined_datetime)
        elif isinstance(event.data_evento, timezone.datetime):
            event.data_evento = timezone.localtime(event.data_evento)
        else:
            event.data_evento = timezone.make_aware(timezone.datetime.combine(event.data_evento, timezone.datetime.min.time()))
        user_profile = get_user_profile(request)
        context = {
            'event': event,
            'user_profile': user_profile
        }
        return redirect(reverse('register_client', args=[id]))
    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')