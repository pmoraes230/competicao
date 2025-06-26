from django.db import models

class Cadeira(models.Model):
    status_cadeira = models.CharField(max_length=10)
    id_setor = models.ForeignKey('Setor', on_delete=models.CASCADE, db_column='id_setor')
    linha = models.CharField(max_length=3, blank=True, null=True)
    coluna = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cadeira'
        
    def __str__(self):
        return f'Cadeira {self.status_cadeira}'


class Cliente(models.Model):
    nome = models.CharField(max_length=20)
    e_mail = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14)

    class Meta:
        managed = False
        db_table = 'cliente'
        
    def __str__(self):
        return self.nome

class Evento(models.Model):
    nome = models.CharField(max_length=20)
    data_evento = models.DateField()
    horario = models.TimeField()
    cpt_pessoas = models.FloatField()
    imagem = models.ImageField(upload_to='eventos')
    local_evento = models.CharField(max_length=20)
    preco_evento = models.DecimalField(max_digits=10, decimal_places=2)
    id_usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, db_column='id_usuario')

    class Meta:
        managed = False
        db_table = 'evento'
        
    def __str__(self):
        return self.nome


class Perfil(models.Model):
    nome = models.CharField(max_length=20)
    descricao = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'perfil'
        
    def __str__(self):
        return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=50)
    qtd_cadeira = models.PositiveBigIntegerField()
    id_evento = models.ForeignKey('Evento', on_delete=models.CASCADE, db_column='id_evento')

    class Meta:
        managed = False
        db_table = 'setor'
        
    def __str__(self):
        return self.nome


class Usuario(models.Model):
    nome = models.CharField(max_length=50)
    e_mail = models.CharField(max_length=50)
    login = models.CharField(max_length=20)
    senha = models.CharField(max_length=230)
    cpf = models.CharField(max_length=14)
    imagem = models.ImageField(upload_to='usuarios')
    id_perfil = models.ForeignKey('Perfil', on_delete=models.CASCADE, db_column='id_perfil')

    class Meta:
        managed = False
        db_table = 'usuario'
        
    def __str__(self):
        return self.nome


class Venda(models.Model):
    id_evento = models.ForeignKey('Evento', on_delete=models.CASCADE, db_column='id_evento')
    id_cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, db_column='id_cliente')
    data_venda = models.DateTimeField()
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venda'
        unique_together = (('id_evento', 'id_cliente'),)
        
    def __str__(self):
        return f'Venda no dia {self.data_venda} do evento {self.id_evento} para {self.id_cliente}'