import sqlite3

def conectar():
    return sqlite3.connect("lanchonete.db")

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # 1. Tabela de Mesas (Status e Cliente)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        numero INTEGER PRIMARY KEY,
        cliente_nome TEXT,
        cliente_contato TEXT,
        status TEXT DEFAULT 'Livre', 
        observacao TEXT
    )""")

    # 2. Tabela de Pedidos (Itens consumidos na mesa no momento)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_mesa INTEGER,
        item_nome TEXT,
        valor REAL,
        status_pedido TEXT DEFAULT 'Pendente'
    )""")

    # 3. Tabela de Vendas (Histórico Geral de cada conta fechada)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        id_mesa INTEGER,
        valor_total REAL,
        forma_pagamento TEXT
    )""")

    # 4. TABELA DE RECEBIMENTOS (ESSA É A NOVA!)
    # Aqui salvamos cada parte do pagamento (Ex: R$ 20 no PIX e R$ 30 no Dinheiro)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recebimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda INTEGER,
        valor REAL,
        forma_pagamento TEXT,
        data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_venda) REFERENCES vendas(id)
    )""")

    # Inicializar as 30 mesas se o banco estiver vazio
    cursor.execute("SELECT COUNT(*) FROM mesas")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 31):
            cursor.execute("INSERT INTO mesas (numero, status) VALUES (?, ?)", (i, 'Livre'))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_vendidos_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda INTEGER,
        item_nome TEXT,
        valor REAL,
        data_venda DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes_taxas (
        id INTEGER PRIMARY KEY,
        nome_taxa TEXT,
        porcentagem REAL
    )""")
# Inicializa com valores padrão se estiver vazio
    cursor.execute("SELECT COUNT(*) FROM configuracoes_taxas")
    if cursor.fetchone()[0] == 0:
        # Definimos a lista FORA do comando de execução para evitar o erro
        taxas_padrao = [
            ('Debito_Point', 1.99), 
            ('Credito_Point', 4.74), 
            ('Pix_Point', 0.99),
            ('iFood_Comissao', 12.0), 
            ('iFood_Pagamento', 3.5)
        ]
        cursor.executemany("INSERT INTO configuracoes_taxas (nome_taxa, porcentagem) VALUES (?, ?)", taxas_padrao)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados atualizado com sucesso!")