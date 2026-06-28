"""BBAP-Sec — Attack Execution Engine"""
from .runner import AttackRunner, ATTACK_REGISTRY
from . import implementations  # Auto-registers all attacks
