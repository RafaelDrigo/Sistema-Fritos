import sqlite3

def conectar():
    return sqlite3.connect("lanchonete.db")

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # 1. Mesas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesas (
        numero INTEGER PRIMARY KEY,
        cliente_nome TEXT,
        cliente_contato TEXT,
        status TEXT DEFAULT 'Livre', 
        observacao TEXT
    )""")

    # 2. Pedidos Atuais (Modificado para suportar descrição de adicionais/níveis)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_mesa INTEGER,
        item_nome TEXT,
        valor REAL,
        status_pedido TEXT DEFAULT 'Pendente',
        detalhes TEXT
    )""")

    # 3. Cardápio Principal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cardapio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        preco REAL NOT NULL,
        ingredientes TEXT
    )""")

    # --- NOVAS TABELAS ESTILO IFOOD ---

    # 4. Adicionais Gerais (Ex: Bacon, Ovo, Cheddar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adicionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL
    )""")

    # 5. Variações/Níveis por Item (Ex: 1 Blend, 2 Blends)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_item INTEGER,
        nome_variacao TEXT NOT NULL,
        preco REAL NOT NULL,
        FOREIGN KEY (id_item) REFERENCES cardapio(id)
    )""")

    # 6. Tabela Ponte: Quais adicionais aparecem em quais itens?
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS item_adicionais (
        id_item INTEGER,
        id_adicional INTEGER,
        PRIMARY KEY (id_item, id_adicional),
        FOREIGN KEY (id_item) REFERENCES cardapio(id),
        FOREIGN KEY (id_adicional) REFERENCES adicionais(id)
    )""")

    # 7. Restante das tabelas (Vendas, Recebimentos, Taxas)
    cursor.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP, id_mesa INTEGER, valor_total REAL, forma_pagamento TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS recebimentos (id INTEGER PRIMARY KEY AUTOINCREMENT, id_venda INTEGER, valor REAL, forma_pagamento TEXT, data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS itens_vendidos_historico (id INTEGER PRIMARY KEY AUTOINCREMENT, id_venda INTEGER, item_nome TEXT, valor REAL, data_venda DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes_taxas (id INTEGER PRIMARY KEY, nome_taxa TEXT, porcentagem REAL)")

    # Inicializar mesas se vazio
    cursor.execute("SELECT COUNT(*) FROM mesas")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 31):
            cursor.execute("INSERT INTO mesas (numero, status) VALUES (?, ?)", (i, 'Livre'))

    conn.commit()
    conn.close()