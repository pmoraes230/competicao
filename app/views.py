from django.utils import timezone
import qrcode
import uuid
from PIL import Image, ImageDraw, ImageFont
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
    
    username = request.POST.get('login')  # Pode ser CPF ou email
    password = request.POST.get('password')
    
    if not username or not password:
        messages.error(request, 'Preencha todos os campos')
        return render(request, 'login/login.html')
    
    try:
        # Buscar usuário pelo CPF ou email
        user = models.Usuario.objects.filter(cpf=username).first() or models.Usuario.objects.filter(e_mail=username).first()
        
        if not user:
            messages.error(request, 'Usuário não encontrado')
            return render(request, 'login/login.html')
        
        # Verificar senha
        if check_password(password, user.senha):
            messages.success(request, 'Login realizado com sucesso!')
            request.session['user_id'] = user.id
            return redirect('home')
        else:
            messages.error(request, 'Senha incorreta.')
            return redirect('login')
        
    except Exception as e:
        messages.error(request, f'Ocorreu um erro: {str(e)}')
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

@role_required('Administrador')
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

@role_required('Administrador', 'Staff', 'Vendedor')
def register_client(request, id):
    context = get_user_profile(request)
    
    if request.method == 'POST':
        name_client = request.POST.get('nome')
        email_client = request.POST.get('email')
        cpf_client = request.POST.get('cpf')
        
        if not name_client or not email_client or not cpf_client:
            messages.error(request, 'Todos os campos são obrigatórios.')
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
            # Armazenar o cliente_id na sessão
            request.session['cliente_id'] = client.id
            # Redirecionar de volta para os detalhes do evento
            return redirect(reverse('event_details', args=[id]))
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar cliente: {str(ve)}')
            return redirect(reverse('register_client', args=[id]))
    
    # Adicionar o event_id ao contexto para uso no template
    context['event_id'] = id
    return render(request, 'reg_cliente/reg_cliente.html', context)

@role_required('Administrador')
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
    
    # Recuperar todos os eventos para exibir no formulário
    eventos = models.Evento.objects.all()
    context['eventos'] = eventos

    # Verificar se há um evento na sessão ou se o usuário selecionou um evento
    event_id = request.POST.get('event_id') or request.session.get('last_event_id')

    if request.method == 'POST':
        nome_setores = request.POST.getlist('nome_setor[]')  # Lista de nomes
        limit_seats = request.POST.getlist('limit_seats[]')  # Lista de quantidades
        event_id = request.POST.get('event_id')  # Evento selecionado no formulário

        if not event_id:
            messages.error(request, 'Por favor, selecione um evento antes de cadastrar os setores.')
            return redirect('register_setor')

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

            messages.success(request, f'{len(nome_setores)} setor(es) cadastrado(s) com sucesso!')
            return redirect('register_setor')
        except models.Evento.DoesNotExist:
            messages.error(request, 'Evento não encontrado.')
            return redirect('register_setor')
        except ValueError as ve:
            messages.error(request, f'Erro ao salvar setor: {str(ve)}')
            return redirect('register_setor')

    # Preenche o contexto com o evento selecionado (se houver)
    if event_id:
        try:
            event = models.Evento.objects.get(id=event_id)
            context['event'] = event
            context['remaining_seats'] = max(0, event.cpt_pessoas - (models.Setor.objects.filter(id_evento_id=event_id).aggregate(total=Sum('qtd_cadeira'))['total'] or 0))
        except models.Evento.DoesNotExist:
            if 'last_event_id' in request.session:
                del request.session['last_event_id']
            messages.error(request, 'Evento não encontrado.')
            return redirect('register_setor')

    return render(request, 'reg_setor/reg_setor.html', context)

def list_setor(request):
    context = get_user_profile(request)
    
    if not context['is_authenticated']:
        messages.error(request, 'Você não está logado.')
        return redirect('login')
    
    setores = models.Setor.objects.all()
    context['setores'] = setores
    
    return render(request, 'reg_setor/list_setor.html', context)

def update_setor(request, id):
    context = get_user_profile(request)
    
    try:
        setor = models.Setor.objects.get(id=id)
    except models.setor.DoesesNotExist:
        messages.error(request, 'Setor não encontrado.')
        return redirect('list_setor')
    
    if request.method == 'POST':
        nome_setor = request.POST.get('nome_setor')
        limit_seats = request.POST.get('limit_seats')

        if not nome_setor or not limit_seats:
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect('update_setor', id=id)

        try:
            setor.nome = nome_setor
            setor.qtd_cadeira = float(limit_seats.replace(',', '.'))  # Converte "5000,0" para 5000.0
            setor.full_clean()
            setor.save()
            
            messages.success(request, 'Setor atualizado com sucesso!')
            return redirect('list_setor')
        except ValueError as ve:
            messages.error(request, f'Erro ao atualizar setor: {str(ve)}')
            return redirect('update_setor', id=id)
    context.update({
        'setor': setor,
        'event': setor.id_evento,
    })
    
    return render(request, 'reg_setor/update_setor.html', context)

def delete_setor(request, id):
    try:
        setor = models.Setor.objects.get(id=id)
        if request.method == 'POST':
            setor.delete()
            messages.success(request, 'Setor excluído com sucesso!')
            return redirect('list_setor')
        context = {
            'setor': setor,
            **get_user_profile(request)
        }
        return render(request, 'reg_setor/delete_setor.html', context)
    except models.Setor.DoesNotExist:
        messages.error(request, 'Setor não encontrado.')
        return redirect('list_setor')

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
        description = request.POST.get('descricao')
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
            update_event.descricao = description
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

def delete_user(request, id):
    try:
        user = models.Usuario.objects.get(id=id)
        
        if request.method == 'POST':
            user.delete()
            messages.success(request, 'Usuário excluído com sucesso!')
            return redirect('list_users')
        context = {
            'user': user,
            **get_user_profile(request)
        }
        return render(request, 'list_usuarios/delete_user.html', context)
    except models.Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('list_users')


@role_required('Administrador', 'Staff', 'Vendedor')
def event_details(request, event_id):
    try:
        # Recuperar evento e setores
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

        # Preparar o contexto
        context = {
            'event': event,
            'setores': setores,
            **get_user_profile(request)
        }

        # Verificar se há um cliente na sessão (opcional, para exibir formulário de compra)
        cliente_id = request.session.get('cliente_id')
        if cliente_id:
            try:
                cliente = models.Cliente.objects.get(id=cliente_id)
                context['cliente'] = cliente
            except models.Cliente.DoesNotExist:
                del request.session['cliente_id']  # Remove cliente inválido da sessão

        return render(request, 'reg_eventos/detalhes_evento.html', context)

    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')


@role_required('Administrador', 'Staff', 'Vendedor')
def buy_ticket(request, event_id):
    try:
        # Verificar se o cliente está cadastrado
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.info(request, 'Por favor, cadastre um cliente antes de comprar ingressos.')
            return redirect(reverse('register_client', args=[event_id]))

        # Recuperar cliente e evento
        cliente = models.Cliente.objects.get(id=cliente_id)
        event = models.Evento.objects.get(id=event_id)
        setores = models.Setor.objects.filter(id_evento_id=event_id)

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

            total_price = quantidade * (event.preco_evento or 0.00)  # Calcula o preço total
            for _ in range(quantidade):
                # Gerar um ID único para o ingresso
                ticket_id = str(uuid.uuid4())

                venda = models.Venda(
                    id_evento=event,
                    id_cliente=cliente,
                    data_venda=timezone.now(),
                    valor=event.preco_evento or 0.00
                )
                venda.save()
                setor.qtd_cadeira -= 1
                setor.save()

            # Gerar QR Code
            qr_data = f"ID do Ingresso: {ticket_id}\nEvento: {event.nome}\nCliente: {cliente.nome}\nCPF: {cliente.cpf}\nData: {venda.data_venda.strftime('%d/%m/%Y %H:%M')}\nValor: R${total_price:.2f}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill='black', back_color='white')

            # Converter a imagem do QR code para o modo RGB
            qr_img = qr_img.convert('RGB')

            # Criar uma imagem com informações abaixo do QR Code
            img_width, img_height = qr_img.size
            new_height = img_height + 150  # Adicionar espaço para texto
            combined_img = Image.new('RGB', (img_width, new_height), 'white')

            # Colar o QR code na imagem combinada
            combined_img.paste(qr_img, (0, 0))

            # Adicionar texto abaixo do QR Code
            draw = ImageDraw.Draw(combined_img)
            try:
                font = ImageFont.load_default(size=20)  # Tente usar uma fonte com tamanho maior para melhor legibilidade
            except AttributeError:
                font = ImageFont.load_default()  # Fallback para versões mais antigas do Pillow

            text = f"Evento: {event.nome}\nCliente: {cliente.nome}\nCPF: {cliente.cpf}\nData: {venda.data_venda.strftime('%d/%m/%Y %H:%M')}\nValor: R${total_price:.2f}\nID do Ingresso: {ticket_id}"
            text_position = (10, img_height + 10)

            # Adicionar texto na imagem
            draw.multiline_text(text_position, text, fill='black', font=font)

            # Salvar a imagem em um buffer
            buffer = BytesIO()
            combined_img.save(buffer, format='PNG')
            ticket_file = ContentFile(buffer.getvalue(), name=f'ticket_{ticket_id}.png')

            messages.success(request, f'Compra de {quantidade} ingresso(s) realizada com sucesso! Valor total: R${total_price:.2f}. Baixe seu ticket abaixo.')
            response = HttpResponse(buffer.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename=ticket_{ticket_id}.png'
            return response

        context = {
            'event': event,
            'setores': setores,
            'cliente': cliente,
            **get_user_profile(request)
        }
        return render(request, 'reg_eventos/detalhes_evento.html', context)

    except models.Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('home')
    except models.Cliente.DoesNotExist:
        messages.error(request, 'Cliente não encontrado. Por favor, cadastre-se novamente.')
        return redirect(reverse('register_client', args=[event_id]))

@role_required('Administrador')
def list_user(request):
    context = get_user_profile(request)
    
    if not context['is_authenticated']:
        messages.error(request, 'Você não está logado.')
        return redirect('login')
    
    users = models.Usuario.objects.all()
    context['usuarios'] = users
    
    return render(request, 'list_usuarios/list_usuarios.html', context)

def edit_user(request, id):
    context = get_user_profile(request)
    try:
        user = models.Usuario.objects.get(id=id)
    except models.Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('list_user')
    
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
            return redirect(reverse('update_user', args=[id]))

        try:
            hashed_password = make_password(password_user)
            profile_id = models.Perfil.objects.get(id=profile_user)

            user.nome = name_completed
            user.e_mail = email_user
            user.login = login_user
            user.senha = hashed_password
            user.cpf = cpf_user
            user.imagem = image_user
            user.id_perfil = profile_id

            user.full_clean()
            user.save()

            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('list_user')

        except ValueError as ve:
            messages.error(request, f'Erro ao atualizar usuário: {str(ve)}')
            return redirect(reverse('update_user', args=[id]))
        
    context.update({
        'user': user,
        'categorys': models.Perfil.objects.all()
    })
    
    return render(request, 'list_usuarios/edit_user.html', context)