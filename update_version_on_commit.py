#!/usr/bin/env python3
"""
Script para atualizar versão automaticamente baseado na mensagem do commit
Integrado com GitHub Actions ou execução manual
"""

import subprocess
import sys
import re
from pathlib import Path

def run_command(command, capture_output=True):
    """Executa comando e retorna resultado"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def get_last_commit_message():
    """Obtém a mensagem do último commit"""
    success, output, error = run_command("git log -1 --pretty=%B")
    if success:
        return output.strip()
    return ""

def determine_version_type(commit_message):
    """Determina o tipo de versão baseado na mensagem do commit"""
    message = commit_message.lower()
    
    # Palavras-chave para MAJOR version
    major_keywords = [
        'breaking', 'major', 'incompatible', 'refactor', 'breaking change',
        'major update', 'major version', 'breaking changes'
    ]
    
    # Palavras-chave para MINOR version  
    minor_keywords = [
        'feat', 'feature', 'minor', 'add', 'new', 'implement', 'enhancement',
        'nova funcionalidade', 'funcionalidade', 'implementado', 'adicionado'
    ]
    
    # Palavras-chave para PATCH version
    patch_keywords = [
        'fix', 'patch', 'bug', 'correction', 'hotfix', 'bugfix',
        'corrigido', 'correção', 'ajuste', 'melhoria', 'otimização'
    ]
    
    # Verificar se contém palavras-chave (ordem de prioridade: major > minor > patch)
    for keyword in major_keywords:
        if keyword in message:
            return 'major'
    
    for keyword in minor_keywords:
        if keyword in message:
            return 'minor'
    
    for keyword in patch_keywords:
        if keyword in message:
            return 'patch'
    
    # Padrão: patch para qualquer commit sem palavras-chave específicas
    return 'patch'

def update_version(version_type):
    """Atualiza a versão usando o version_manager.py"""
    print(f"🔄 Atualizando versão ({version_type})...")
    
    success, output, error = run_command(f"python version_manager.py {version_type}")
    if success:
        print(f"✅ Versão atualizada com sucesso!")
        print(output)
        return True
    else:
        print(f"❌ Erro ao atualizar versão: {error}")
        return False

def commit_version_changes(version_type, commit_message):
    """Faz commit das mudanças de versão"""
    print("📝 Fazendo commit das mudanças de versão...")
    
    # Adicionar arquivos modificados
    files_to_add = [
        "VERSION",
        "frontend/frontend/package.json", 
        "frontend/frontend/package-lock.json",
        "frontend/frontend/pnpm-lock.yaml",
        "backend/niochat/settings.py",
        "backend/core/telegram_service.py",
        "CHANGELOG.json",
        "frontend/frontend/public/CHANGELOG.json",
        "VERSION_INFO.md"
    ]
    
    for file in files_to_add:
        if Path(file).exists():
            run_command(f"git add {file}", capture_output=False)
    
    # Fazer commit com mensagem descritiva
    success, output, error = run_command(
        f'git commit -m "📦 Auto-update version ({version_type}): {commit_message[:50]}..."',
        capture_output=False
    )
    
    if success:
        print("✅ Commit de versão realizado com sucesso!")
        return True
    else:
        print(f"⚠️  Nenhuma mudança para commit ou erro: {error}")
        return True  # Não é erro crítico

def main():
    """Função principal"""
    print("🚀 Sistema de Versionamento Automático - NioChat")
    print("=" * 50)
    
    # Verificar se estamos em um repositório Git
    success, _, _ = run_command("git rev-parse --git-dir")
    if not success:
        print("❌ Não é um repositório Git")
        sys.exit(1)
    
    # Obter mensagem do último commit
    commit_message = get_last_commit_message()
    if not commit_message:
        print("❌ Não foi possível obter mensagem do commit")
        sys.exit(1)
    
    print(f"📋 Último commit: {commit_message}")
    
    # Determinar tipo de versão
    version_type = determine_version_type(commit_message)
    print(f"🎯 Tipo de versão detectado: {version_type}")
    
    # Verificar se deve ser processado (ignorar commits de versão automática)
    if "auto-update version" in commit_message.lower():
        print("⏭️  Ignorando commit de versão automática")
        sys.exit(0)
    
    # Atualizar versão
    if update_version(version_type):
        # Fazer commit das mudanças (opcional)
        if len(sys.argv) > 1 and sys.argv[1] == "--commit":
            commit_version_changes(version_type, commit_message)
        
        print(f"\n🎉 Processo concluído!")
        print(f"📝 Execute 'git push origin main' para enviar para o GitHub")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()



