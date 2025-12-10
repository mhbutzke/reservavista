"""
Módulo de validação e sanitização de dados.
Garante que dados da API Vista sejam validados antes de serem salvos no Supabase.
Compliance: LGPD, prevenção de XSS e SQL Injection.
"""

import re
from typing import Any, Dict, Optional, List
from datetime import datetime


class ValidationError(Exception):
    """Exceção para erros de validação."""
    pass


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro.
    
    Args:
        cpf: String com CPF (pode conter pontuação)
    
    Returns:
        True se válido, False caso contrário
    """
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica tamanho
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais (inválido)
    if cpf == cpf[0] * 11:
        return False
    
    # Valida primeiro dígito verificador
    sum_1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit_1 = (sum_1 * 10 % 11) % 10
    
    if int(cpf[9]) != digit_1:
        return False
    
    # Valida segundo dígito verificador
    sum_2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit_2 = (sum_2 * 10 % 11) % 10
    
    if int(cpf[10]) != digit_2:
        return False
    
    return True


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro.
    
    Args:
        cnpj: String com CNPJ (pode conter pontuação)
    
    Returns:
        True se válido, False caso contrário
    """
    if not cnpj:
        return False
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica tamanho
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais (inválido)
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação dos dígitos verificadores
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(int(cnpj[i]) * weights_1[i] for i in range(12))
    digit_1 = 0 if sum_1 % 11 < 2 else 11 - (sum_1 % 11)
    
    if int(cnpj[12]) != digit_1:
        return False
    
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(int(cnpj[i]) * weights_2[i] for i in range(13))
    digit_2 = 0 if sum_2 % 11 < 2 else 11 - (sum_2 % 11)
    
    if int(cnpj[13]) != digit_2:
        return False
    
    return True


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: String com email
    
    Returns:
        True se válido, False caso contrário
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Valida telefone brasileiro.
    Aceita: (11) 98888-8888, 11988888888, etc.
    
    Args:
        phone: String com telefone
    
    Returns:
        True se válido, False caso contrário
    """
    if not phone:
        return False
    
    # Remove caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Aceita 10 ou 11 dígitos (com ou sem 9 no celular)
    return len(phone) in [10, 11]


def sanitize_text(text: str, max_length: int = 5000, allow_html: bool = False) -> Optional[str]:
    """
    Remove caracteres perigosos e limita tamanho do texto.
    
    Args:
        text: Texto a ser sanitizado
        max_length: Tamanho máximo permitido
        allow_html: Se False, remove todas as tags HTML
    
    Returns:
        Texto sanitizado ou None se vazio
    """
    if not text or text.strip() == '':
        return None
    
    # Remove HTML/scripts se não permitido
    if not allow_html:
        text = re.sub(r'<[^>]*>', '', text)
    
    # Remove caracteres de controle perigosos
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limita tamanho
    text = text[:max_length].strip()
    
    return text if text else None


def sanitize_sql_string(text: str) -> Optional[str]:
    """
    Sanitiza string para prevenir SQL injection.
    NOTA: O Supabase client já usa parametrização, mas isto é uma camada extra.
    
    Args:
        text: String a ser sanitizada
    
    Returns:
        String sanitizada
    """
    if not text:
        return None
    
    # Remove caracteres perigosos comuns em SQL injection
    dangerous_patterns = [
        r"(\bDROP\b|\bDELETE\b|\bTRUNCATE\b|\bALTER\b|\bEXEC\b|\bEXECUTE\b)",
        r"(--|#|\/\*|\*\/|;)",
        r"('(\s|%20)OR(\s|%20)'|'(\s|%20)AND(\s|%20)')",
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return sanitize_text(text)


def validate_date(date_str: str) -> bool:
    """
    Valida formato de data.
    
    Args:
        date_str: String com data (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)
    
    Returns:
        True se válido, False caso contrário
    """
    if not date_str:
        return False
    
    # Ignora datas inválidas do Vista (0000-00-00)
    if date_str.startswith('0000-00-00'):
        return False
    
    try:
        # Tenta parsear como datetime
        if ' ' in date_str:
            datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_cliente(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e sanitiza dados de cliente.
    
    Args:
        data: Dicionário com dados do cliente
    
    Returns:
        Dicionário com dados validados e sanitizados
    
    Raises:
        ValidationError: Se dados críticos forem inválidos
    """
    # Código é obrigatório
    if not data.get('Codigo'):
        raise ValidationError("Código do cliente é obrigatório")
    
    # Validar CPF/CNPJ se presente
    if 'CPFCNPJ' in data and data['CPFCNPJ']:
        cpf_cnpj = re.sub(r'[^0-9]', '', data['CPFCNPJ'])
        
        is_valid = False
        if len(cpf_cnpj) == 11:
            is_valid = validate_cpf(data['CPFCNPJ'])
        elif len(cpf_cnpj) == 14:
            is_valid = validate_cnpj(data['CPFCNPJ'])
        
        if not is_valid:
            print(f"AVISO: CPF/CNPJ inválido para cliente {data['Codigo']}: {data['CPFCNPJ']}")
            # Não falha, apenas marca como None para investigação
            data['CPFCNPJ'] = None
    
    # Validar emails
    for email_field in ['EmailResidencial', 'EmailComercial']:
        if email_field in data and data[email_field]:
            if not validate_email(data[email_field]):
                print(f"AVISO: Email inválido para cliente {data['Codigo']}: {data[email_field]}")
                data[email_field] = None
    
    # Validar telefones
    for phone_field in ['FonePrincipal', 'Celular', 'FoneComercial']:
        if phone_field in data and data[phone_field]:
            if not validate_phone(data[phone_field]):
                print(f"AVISO: Telefone inválido para cliente {data['Codigo']}: {data[phone_field]}")
                # Mantém o valor original, pois pode ser formato internacional
    
    # Sanitizar campos de texto
    text_fields = ['Nome', 'Observacoes', 'EnderecoResidencial', 'EnderecoComplemento', 
                   'BairroResidencial', 'CidadeResidencial', 'Profissao']
    for field in text_fields:
        if field in data and data[field]:
            data[field] = sanitize_text(data[field])
    
    # Validar datas
    date_fields = ['DataNascimento', 'DataCadastro', 'DataAtualizacao']
    for field in date_fields:
        if field in data and data[field]:
            if not validate_date(data[field]):
                data[field] = None
    
    return data


def validate_negocio(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e sanitiza dados de negócio.
    
    Args:
        data: Dicionário com dados do negócio
    
    Returns:
        Dicionário com dados validados
    """
    if not data.get('Codigo'):
        raise ValidationError("Código do negócio é obrigatório")
    
    # Sanitizar campos de texto
    text_fields = ['NomeNegocio', 'ObservacaoPerda', 'MotivoPerda']
    for field in text_fields:
        if field in data and data[field]:
            data[field] = sanitize_text(data[field], max_length=1000)
    
    # Validar valores numéricos
    numeric_fields = ['ValorNegocio', 'ValorLocacao']
    for field in numeric_fields:
        if field in data and data[field]:
            try:
                float(data[field])
            except (ValueError, TypeError):
                data[field] = None
    
    return data


def validate_atividade(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e sanitiza dados de atividade.
    
    Args:
        data: Dicionário com dados da atividade
    
    Returns:
        Dicionário com dados validados
    """
    # Sanitizar campos de texto
    text_fields = ['Assunto', 'Texto', 'TextoProposta', 'Local']
    for field in text_fields:
        if field in data and data[field]:
            data[field] = sanitize_text(data[field], max_length=2000)
    
    return data


def validate_batch(data: List[Dict[str, Any]], validator_func) -> List[Dict[str, Any]]:
    """
    Valida um lote de registros.
    
    Args:
        data: Lista de dicionários
        validator_func: Função de validação a aplicar
    
    Returns:
        Lista de registros validados (remove registros inválidos)
    """
    validated = []
    errors = []
    
    for idx, record in enumerate(data):
        try:
            validated_record = validator_func(record)
            validated.append(validated_record)
        except ValidationError as e:
            errors.append(f"Registro {idx}: {str(e)}")
        except Exception as e:
            errors.append(f"Registro {idx}: Erro inesperado - {str(e)}")
    
    if errors:
        print(f"AVISOS DE VALIDAÇÃO: {len(errors)} registros com problemas")
        for error in errors[:10]:  # Mostra apenas os primeiros 10
            print(f"  - {error}")
    
    return validated
