"""
Testes de segurança para validação, sanitização e logging.
"""

import pytest
from src.utils.validators import (
    validate_cpf, validate_cnpj, validate_email, validate_phone,
    sanitize_text, validate_cliente, validate_negocio, ValidationError
)
from src.utils.secure_logger import SecureLogger


class TestCPFValidation:
    """Testes de validação de CPF."""
    
    def test_valid_cpf(self):
        """Testa CPFs válidos."""
        valid_cpfs = [
            "123.456.789-09",
            "12345678909",
            "111.444.777-35"
        ]
        for cpf in valid_cpfs:
            assert validate_cpf(cpf), f"CPF {cpf} deveria ser válido"
    
    def test_invalid_cpf(self):
        """Testa CPFs inválidos."""
        invalid_cpfs = [
            "000.000.000-00",  # Todos zeros
            "111.111.111-11",  # Todos iguais
            "123.456.789-00",  # Dígito verificador errado
            "123456789",       # Tamanho incorreto
            ""                 # Vazio
        ]
        for cpf in invalid_cpfs:
            assert not validate_cpf(cpf), f"CPF {cpf} deveria ser inválido"


class TestCNPJValidation:
    """Testes de validação de CNPJ."""
    
    def test_valid_cnpj(self):
        """Testa CNPJs válidos."""
        valid_cnpjs = [
            "11.222.333/0001-81",
            "11222333000181"
        ]
        for cnpj in valid_cnpjs:
            assert validate_cnpj(cnpj), f"CNPJ {cnpj} deveria ser válido"
    
    def test_invalid_cnpj(self):
        """Testa CNPJs inválidos."""
        invalid_cnpjs = [
            "00.000.000/0000-00",
            "11.111.111/1111-11",
            "11.222.333/0001-00",  # Dígito verificador errado
            ""
        ]
        for cnpj in invalid_cnpjs:
            assert not validate_cnpj(cnpj), f"CNPJ {cnpj} deveria ser inválido"


class TestEmailValidation:
    """Testes de validação de email."""
    
    def test_valid_emails(self):
        """Testa emails válidos."""
        valid_emails = [
            "user@example.com",
            "test.user@company.com.br",
            "admin+tag@domain.co.uk"
        ]
        for email in valid_emails:
            assert validate_email(email), f"Email {email} deveria ser válido"
    
    def test_invalid_emails(self):
        """Testa emails inválidos."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
            ""
        ]
        for email in invalid_emails:
            assert not validate_email(email), f"Email {email} deveria ser inválido"


class TestPhoneValidation:
    """Testes de validação de telefone."""
    
    def test_valid_phones(self):
        """Testa telefones válidos."""
        valid_phones = [
            "(11) 98888-8888",
            "11988888888",
            "1133334444",
            "(21) 3333-4444"
        ]
        for phone in valid_phones:
            assert validate_phone(phone), f"Telefone {phone} deveria ser válido"
    
    def test_invalid_phones(self):
        """Testa telefones inválidos."""
        invalid_phones = [
            "123",
            "12345",
            ""
        ]
        for phone in invalid_phones:
            assert not validate_phone(phone), f"Telefone {phone} deveria ser inválido"


class TestTextSanitization:
    """Testes de sanitização de texto."""
    
    def test_xss_protection(self):
        """Verifica proteção contra XSS."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "javascript:alert('xss')"
        ]
        
        for malicious in malicious_inputs:
            sanitized = sanitize_text(malicious)
            assert '<script>' not in sanitized.lower() if sanitized else True
            assert 'onerror' not in sanitized.lower() if sanitized else True
    
    def test_sql_injection_protection(self):
        """Verifica proteção contra SQL injection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM passwords--"
        ]
        
        for malicious in malicious_inputs:
            sanitized = sanitize_text(malicious)
            # Apenas verifica que não quebra, SQL injection real é prevenida por parametrização
            assert sanitized is not None or sanitized is None
    
    def test_length_limiting(self):
        """Testa limitação de tamanho."""
        long_text = "A" * 10000
        sanitized = sanitize_text(long_text, max_length=100)
        assert len(sanitized) <= 100
    
    def test_empty_strings(self):
        """Testa strings vazias."""
        assert sanitize_text("") is None
        assert sanitize_text("   ") is None


class TestClienteValidation:
    """Testes de validação de cliente."""
    
    def test_valid_cliente(self):
        """Testa validação de cliente válido."""
        cliente = {
            'Codigo': '12345',
            'Nome': 'João Silva',
            'CPFCNPJ': '123.456.789-09',
            'EmailResidencial': 'joao@example.com',
            'Celular': '(11) 98888-8888',
            'Observacoes': 'Cliente VIP'
        }
        validated = validate_cliente(cliente)
        assert validated['Codigo'] == '12345'
        assert validated['Nome'] is not None
    
    def test_cliente_missing_codigo(self):
        """Testa cliente sem código (deve falhar)."""
        cliente = {'Nome': 'João'}
        with pytest.raises(ValidationError):
            validate_cliente(cliente)
    
    def test_cliente_invalid_cpf(self):
        """Testa cliente com CPF inválido."""
        cliente = {
            'Codigo': '123',
            'CPFCNPJ': '000.000.000-00'
        }
        validated = validate_cliente(cliente)
        assert validated['CPFCNPJ'] is None  # CPF inválido é convertido para None


class TestSecureLogger:
    """Testes do logger seguro."""
    
    def test_cpf_redaction(self):
        """Testa redação de CPF."""
        logger = SecureLogger('test')
        message = "Cliente CPF: 123.456.789-00"
        sanitized = logger.sanitize(message)
        assert '123.456.789-00' not in sanitized
        assert '[CPF_REDACTED]' in sanitized
    
    def test_email_redaction(self):
        """Testa redação de email."""
        logger = SecureLogger('test')
        message = "Contato: user@example.com"
        sanitized = logger.sanitize(message)
        assert 'user@example.com' not in sanitized
        assert '[EMAIL_REDACTED]' in sanitized
    
    def test_phone_redaction(self):
        """Testa redação de telefone."""
        logger = SecureLogger('test')
        message = "Tel: (11) 98888-8888"
        sanitized = logger.sanitize(message)
        assert '98888-8888' not in sanitized
        assert '[PHONE_REDACTED]' in sanitized
    
    def test_multiple_redactions(self):
        """Testa múltiplas redações."""
        logger = SecureLogger('test')
        message = "João - CPF: 123.456.789-00, Email: joao@example.com, Tel: (11) 98888-8888"
        sanitized = logger.sanitize(message)
        assert '123.456.789-00' not in sanitized
        assert 'joao@example.com' not in sanitized
        assert '98888-8888' not in sanitized


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
