from questionary import Style

# Estilo padrão unificado para toda a aplicação.
custom_style = Style(
    [
        ('qmark', 'fg:#22c55e'),  # símbolo de pergunta
        ('question', 'bold'),  # texto da pergunta
        ('answer', 'fg:#60a5fa'),  # resposta selecionada
        ('pointer', 'fg:#a78bfa'),  # setinha do menu
        ('highlighted', 'fg:#f59e0b'),  # opção destacada
        ('selected', 'fg:#34d399'),  # opção escolhida
        ('instruction', 'fg:#9ca3af'),  # instrução
        ('text', ''),  # texto comum
        ('disabled', 'fg:#6b7280 italic'),  # opção desabilitada
    ]
)
