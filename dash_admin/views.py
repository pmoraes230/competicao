from django.shortcuts import render
from . import models
from django.utils import timezone
from django.contrib import messages

def home_dash(request):
    # Obter estatísticas
    total_eventos = models.Evento.objects.count()
    total_usuarios = models.Usuario.objects.count()
    total_vendas = models.Venda.objects.count()

    # Atividades recentes (exemplo com base em vendas)
    atividades_recentes = models.Venda.objects.select_related('id_evento', 'id_cliente').order_by('-data_venda')[:6]  # Últimas 5 vendas
    atividades_formatadas = []
    for venda in atividades_recentes:
        atividade = {
            'data': venda.data_venda,
            'descricao': f'Compra de ingresso para {venda.id_evento.nome}',
            'usuario': venda.id_cliente  # Ajuste conforme necessário
        }
        atividades_formatadas.append(atividade)

    # Notificações (exemplo simples)
    notificacoes = []
    if total_vendas > 0 and total_eventos == 0:
        notificacoes.append({'mensagem': 'Atenção: Há vendas registradas sem eventos associados!'})
    elif models.Evento.objects.filter(data_evento__lt=timezone.now()).exists():
        notificacoes.append({'mensagem': 'Há eventos passados que precisam de revisão!'})

    # Contexto para o template
    context = {
        'total_eventos': total_eventos,
        'total_usuarios': total_usuarios,
        'total_vendas': total_vendas,
        'atividades_recentes': atividades_formatadas,
        'notificacoes': notificacoes,
    }

    return render(request, 'home_dashboard/home_dashboard.html', context)

def dash_vendas(request):
    vendas = models.Venda.objects.select_related('id_evento', 'id_cliente').order_by('-data_venda')
    context = {
        'vendas': vendas,
        'total_vendas': vendas.count(),
    }
    return render(request, 'dash_vendas/dash_vendas.html', context)

def dash_usuarios(request):
    usuario = models.Usuario.objects.all()
    context = {
        'usuarios': usuario,
        'total_usuarios': usuario.count(),
    }
    
    return render(request, 'dash_usuarios/dash_usuarios.html', context)

def dash_eventos(request):
    eventos = models.Evento.objects.all()
    context = {
        'eventos': eventos,
        'total_eventos': eventos.count(),
    }
    return render(request, 'dash_eventos/dash_eventos.html', context)