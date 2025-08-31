# Adicionar ao final do arquivo core/models.py

class SystemVersion(models.Model):
    """Modelo para gerenciar versões do sistema"""
    
    VERSION_TYPES = [
        ('major', 'Major'),
        ('minor', 'Minor'), 
        ('patch', 'Patch'),
    ]
    
    CHANGE_TYPES = [
        ('feature', 'Nova Funcionalidade'),
        ('improvement', 'Melhoria'),
        ('fix', 'Correção'),
        ('security', 'Segurança'),
    ]
    
    version = models.CharField(max_length=20, unique=True, help_text="Ex: 2.1.5")
    version_type = models.CharField(max_length=10, choices=VERSION_TYPES, default='patch')
    title = models.CharField(max_length=200, help_text="Título da versão")
    release_date = models.DateField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-release_date', '-version']
        verbose_name = "Versão do Sistema"
        verbose_name_plural = "Versões do Sistema"
    
    def __str__(self):
        return f"v{self.version} - {self.title}"


class ChangelogEntry(models.Model):
    """Entradas do changelog para cada versão"""
    
    version = models.ForeignKey(SystemVersion, on_delete=models.CASCADE, related_name='changes')
    change_type = models.CharField(max_length=15, choices=SystemVersion.CHANGE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Entrada do Changelog"
        verbose_name_plural = "Entradas do Changelog"
    
    def __str__(self):
        return f"{self.get_change_type_display()}: {self.title}"