"""
Logger seguro que remove automaticamente dados sensíveis dos logs.
Compliance: LGPD - evita exposição de dados pessoais em logs.
"""

import re
import logging
from typing import Any
from datetime import datetime


class SecureLogger:
    """
    Logger que filtra automaticamente dados sensíveis antes de registrar.
    """
    
    # Padrões de dados sensíveis a serem redatados
    SENSITIVE_PATTERNS = [
        # CPF: 123.456.789-00 ou 12345678900
        (r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', '[CPF_REDACTED]'),
        
        # CNPJ: 12.345.678/0001-00 ou 12345678000100
        (r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', '[CNPJ_REDACTED]'),
        
        # Email
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_REDACTED]'),
        
        # Telefone brasileiro: (11) 98888-8888, 11988888888, etc
        (r'\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}', '[PHONE_REDACTED]'),
        
        # API Keys (genérico - padrão de 32+ caracteres alfanuméricos)
        (r'\b[A-Za-z0-9]{32,}\b', '[API_KEY_REDACTED]'),
        
        # Senhas em logs (password=xxx, senha=xxx, etc)
        (r'(password|senha|secret|token)\s*[=:]\s*[^\s,;]+', r'\1=[REDACTED]'),
    ]
    
    def __init__(self, name: str = __name__, level: int = logging.INFO):
        """
        Inicializa o logger seguro.
        
        Args:
            name: Nome do logger
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Configurar handler se ainda não tiver
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    @staticmethod
    def sanitize(message: str) -> str:
        """
        Remove dados sensíveis de uma mensagem de log.
        
        Args:
            message: Mensagem original
        
        Returns:
            Mensagem sanitizada
        """
        if not isinstance(message, str):
            message = str(message)
        
        sanitized = message
        for pattern, replacement in SecureLogger.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def debug(self, message: str, *args, **kwargs):
        """Log DEBUG sanitizado."""
        self.logger.debug(self.sanitize(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log INFO sanitizado."""
        self.logger.info(self.sanitize(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log WARNING sanitizado."""
        self.logger.warning(self.sanitize(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log ERROR sanitizado."""
        self.logger.error(self.sanitize(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log CRITICAL sanitizado."""
        self.logger.critical(self.sanitize(message), *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log EXCEPTION sanitizado."""
        self.logger.exception(self.sanitize(message), *args, **kwargs)


# Logger global seguro
secure_logger = SecureLogger('vista_etl')


# Funções de conveniência
def debug(message: str):
    """Log DEBUG."""
    secure_logger.debug(message)


def info(message: str):
    """Log INFO."""
    secure_logger.info(message)


def warning(message: str):
    """Log WARNING."""
    secure_logger.warning(message)


def error(message: str):
    """Log ERROR."""
    secure_logger.error(message)


def critical(message: str):
    """Log CRITICAL."""
    secure_logger.critical(message)


def exception(message: str):
    """Log EXCEPTION com stack trace."""
    secure_logger.exception(message)


# Exemplo de uso:
# from src.utils.secure_logger import info, error
# info("Processando cliente João - CPF: 123.456.789-00")
# # Output: "Processando cliente João - CPF: [CPF_REDACTED]"
