import customtkinter as ctkinter
import customtkinter as ctk
import os
import sqlite3
import pandas as pd
import shutil

from tkinter import messagebox
from datetime import datetime

print("🚀 RODANDO ESSE MAIN AQUI 🚀")

def obter_cardapio_completo():
    conn = sqlite3.connect("lanchonete.db")
    cursor = conn.cursor()
    # Busca itens ordenados por categoria e nome
    cursor.execute("SELECT nome, categoria, preco FROM cardapio ORDER BY categoria, nome")
    dados = cursor.fetchall()
    conn.close()
    
    # Organiza em um dicionário para o sistema entender
    cardapio_organizado = {}
    for nome, cat, preco in dados:
        if cat not in cardapio_organizado:
            cardapio_organizado[cat] = []
        cardapio_organizado[cat].append({"nome": nome, "preco": preco})
    
    return cardapio_organizado

def obter_mesas():
    conn = sqlite3.connect("lanchonete.db")
    cursor = conn.cursor()
    cursor.execute("SELECT numero, status FROM mesas ORDER BY numero")
    dados = cursor.fetchall()
    conn.close()
    return dados

def exportar_vendas_excel():
    try:
        conn = sqlite3.connect("lanchonete.db")
        # Query avançada que junta Venda + Cliente + Recebimentos Detalhados
        query = """
        SELECT 
            v.data_hora as 'Data/Hora',
            m.cliente_nome as 'Cliente',
            m.cliente_contato as 'WhatsApp',
            v.id_mesa as 'Mesa',
            r.forma_pagamento as 'Forma de Pagto',
            r.valor as 'Valor Recebido',
            v.valor_total as 'Total da Comanda'
        FROM vendas v
        JOIN recebimentos r ON v.id = r.id_venda
        JOIN mesas m ON v.id_mesa = m.numero
        ORDER BY v.data_hora DESC
        """
        df_completo = pd.read_sql_query(query, conn)
        conn.close()

        nome_arq = f"Relatorio_Detallhado_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
        df_completo.to_excel(nome_arq, index=False)
        messagebox.showinfo("Sucesso", f"Excel Gerado: {nome_arq}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar Excel: {e}")

def atualizar_cardapio():
    return obter_cardapio_completo()

class JanelaMesas(ctkinter.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Gestão de Mesas")
        self.geometry("1300x850")
        self.after(100, self.grab_set) 
        
        self.carregar_dados_dinamicos()
        self.carrinho = {} 
        self.itens_ja_pedidos = {}
        self.mesa_atual = None
        self.labels_qtd = {} 

        self.main_container = ctkinter.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.mostrar_mapa_mesas()

    def carregar_dados_dinamicos(self):
        """Busca o cardápio atualizado do Banco de Dados e monta as variáveis de sistema"""
        dados_banco = obter_cardapio_completo() # Chama sua função que já existe lá no topo!
        
        self.categorias_ordem = list(dados_banco.keys())
        self.itens_por_categoria = {}
        self.precos = {}

        for categoria, itens in dados_banco.items():
            self.itens_por_categoria[categoria] = []
            for item in itens:
                nome_item = item["nome"]
                preco_item = item["preco"]
                
                # Preenche as listas com os dados reais
                self.itens_por_categoria[categoria].append(nome_item)
                self.precos[nome_item] = preco_item

    def mostrar_mapa_mesas(self):
        for widget in self.main_container.winfo_children(): widget.destroy()
        self.carrinho = {}
        ctkinter.CTkLabel(self.main_container, text="📍 MAPA DE MESAS", font=("Arial", 24, "bold")).pack(pady=10)
        grid_frame = ctkinter.CTkScrollableFrame(self.main_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        for i, (num, status) in enumerate(obter_mesas()):
            cor = "#2ecc71" if status == 'Livre' else "#f1c40f" if status == 'Ocupada' else "#e74c3c"
            btn = ctkinter.CTkButton(grid_frame, text=f"MESA {num:02d}\n{status}", 
                                     fg_color=cor, width=150, height=100, font=("Arial", 13, "bold"),
                                     command=lambda n=num: self.abrir_detalhes_mesa(n))
            btn.grid(row=i//6, column=i%6, padx=12, pady=12)

    def abrir_detalhes_mesa(self, num_mesa):
        self.mesa_atual = num_mesa
        self.carrinho = {}
        self.itens_ja_pedidos = {}
        self.labels_qtd = {}
        for widget in self.main_container.winfo_children(): widget.destroy()

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT cliente_nome, cliente_contato FROM mesas WHERE numero=?", (num_mesa,))
        info = cursor.fetchone()
        cursor.execute("SELECT item_nome, COUNT(item_nome) FROM pedidos WHERE id_mesa=? GROUP BY item_nome", (num_mesa,))
        for nome, qtd in cursor.fetchall():
            self.itens_ja_pedidos[nome] = qtd
        conn.close()

        self.frame_lat = ctkinter.CTkScrollableFrame(self.main_container, width=180, fg_color="#34495e")
        self.frame_lat.pack(side="left", fill="y")
        self.frame_central = ctkinter.CTkFrame(self.main_container, fg_color="transparent")
        self.frame_central.pack(side="left", fill="both", expand=True, padx=10)

        topo = ctkinter.CTkFrame(self.frame_central)
        topo.pack(fill="x", pady=5)
        ctkinter.CTkButton(topo, text="⬅ VOLTAR", width=70, command=self.mostrar_mapa_mesas).grid(row=0, column=0, padx=5)
        self.ent_nome = ctkinter.CTkEntry(topo, placeholder_text="Nome Cliente", width=180)
        if info and info[0]: self.ent_nome.insert(0, info[0])
        self.ent_nome.grid(row=0, column=1, padx=5)
        self.ent_whats = ctkinter.CTkEntry(topo, placeholder_text="WhatsApp", width=140)
        if info and info[1]: self.ent_whats.insert(0, info[1])
        self.ent_whats.grid(row=0, column=2, padx=5)

        scroll_c = ctkinter.CTkScrollableFrame(self.frame_central, label_text="CARDÁPIO - ADICIONAR ITENS")
        scroll_c.pack(fill="both", expand=True, pady=5)

        for cat in self.categorias_ordem:
            ctkinter.CTkLabel(scroll_c, text=f"--- {cat.upper()} ---", font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=5)
            for item in self.itens_por_categoria[cat]:
                preco = self.precos.get(item, 0)
                f = ctkinter.CTkFrame(scroll_c, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctkinter.CTkLabel(f, text=f"{item} (R${preco:.2f})", width=200, anchor="w").pack(side="left", padx=10)
                ctkinter.CTkButton(f, text="+", width=30, command=lambda i=item: self.abrir_pop_up_adicionais_por_nome(i)).pack(side="right", padx=2)
                lbl_q = ctkinter.CTkLabel(f, text="0", width=30, font=("Arial", 12, "bold"))
                lbl_q.pack(side="right", padx=5)
                self.labels_qtd[item] = lbl_q
                ctkinter.CTkButton(f, text="-", width=30, command=lambda i=item: self.alterar_qtd(i, -1)).pack(side="right", padx=2)

        self.frame_res = ctkinter.CTkFrame(self.main_container, width=300)
        self.frame_res.pack(side="right", fill="both", padx=5)
        self.lista_visual = ctkinter.CTkTextbox(self.frame_res, width=280, height=450, font=("Courier", 12))
        self.lista_visual.pack(padx=10, pady=10)
        self.lbl_tot = ctkinter.CTkLabel(self.frame_res, text="TOTAL: R$ 0.00", font=("Arial", 22, "bold"), text_color="#2ecc71")
        self.lbl_tot.pack(pady=10)

        ctkinter.CTkButton(self.frame_res, text="✅ LANÇAR NOVOS ITENS", fg_color="#27ae60", height=45, command=self.confirmar_pedido).pack(fill="x", padx=20, pady=5)
        ctkinter.CTkButton(self.frame_res, text="🖨️ IMPRIMIR CONTA", fg_color="#7f8c8d", 
                   command=self.imprimir_pre_conta).pack(fill="x", padx=20, pady=5)
        ctkinter.CTkButton(self.frame_res, text="💰 FECHAR CONTA", fg_color="#2980b9", height=45, command=self.tela_fechamento_conta).pack(fill="x", padx=20, pady=5)

        for n, s in obter_mesas():
            cor = "#2ecc71" if s == 'Livre' else "#f1c40f" if s == 'Ocupada' else "#e74c3c"
            ctkinter.CTkButton(self.frame_lat, text=f"MESA {n:02d}", fg_color=cor, command=lambda num=n: self.abrir_detalhes_mesa(num)).pack(pady=2, fill="x", padx=5)
        
        self.atualizar_visual_resumo()

    def abrir_pop_up_adicionais_por_nome(self, item_nome):
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, preco FROM cardapio WHERE nome = ?", (item_nome,))
        res = cursor.fetchone()
        conn.close()

        if res:
            item_id, preco = res
            self.abrir_pop_up_adicionais_mesas(item_id, item_nome, preco)
        else:
            messagebox.showerror("Erro", "Item não encontrado no banco!")

    def alterar_qtd(self, item, valor):
            qtd = self.carrinho.get(item, 0) + valor
            if qtd <= 0:
                if item in self.carrinho: del self.carrinho[item]
                if item in self.labels_qtd: self.labels_qtd[item].configure(text="0")
            else:
                self.carrinho[item] = qtd
                if item in self.labels_qtd: self.labels_qtd[item].configure(text=str(qtd))
            self.atualizar_visual_resumo()

    def atualizar_visual_resumo(self):
        self.lista_visual.delete("0.0", "end")
        total = 0
        
        # Itens que já estavam salvos na conta
        if self.itens_ja_pedidos:
            self.lista_visual.insert("end", ">>> NA CONTA <<<\n")
            for i, q in self.itens_ja_pedidos.items():
                # PROTEÇÃO: .get(i, 0) garante que se não achar o preço, ele assume 0 em vez de travar
                preco = self.precos.get(i, 0)
                sub = q * preco
                self.lista_visual.insert("end", f"{q}x {i:<15} R${sub:>6.2f}\n")
                total += sub
            self.lista_visual.insert("end", "-"*25 + "\n")
            
        # Novos itens no carrinho
        if self.carrinho:
            self.lista_visual.insert("end", ">>> NOVOS <<<\n")
            for i, q in self.carrinho.items():
                # PROTEÇÃO: .get(i, 0) evita o erro com a palavra 'Lanches'
                preco = self.precos.get(i, 0)
                sub = q * preco
                self.lista_visual.insert("end", f"{q}x {i:<15} R${sub:>6.2f}\n")
                total += sub
                
        self.lbl_tot.configure(text=f"TOTAL: R$ {total:.2f}")

    def confirmar_pedido(self):
        if not self.carrinho and not self.ent_nome.get(): 
            return
            
        try:
            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()
            
            status = 'Ocupada' if (self.carrinho or self.itens_ja_pedidos) else 'Livre'
            
            cursor.execute("UPDATE mesas SET status=?, cliente_nome=?, cliente_contato=? WHERE numero=?", 
                    (status, self.ent_nome.get(), self.ent_whats.get(), self.mesa_atual))
            
            for item, qtd in self.carrinho.items():
                preco_item = self.precos.get(item)
                
                # SÓ SALVA NO BANCO SE O ITEM TIVER UM PREÇO (Isso ignora 'Lanches' ou categorias)
                if preco_item is not None:
                    for _ in range(qtd):
                        cursor.execute("INSERT INTO pedidos (id_mesa, item_nome, valor) VALUES (?, ?, ?)", 
                                    (self.mesa_atual, item, preco_item))
            
            conn.commit()
            conn.close()
            
            if self.carrinho:
                self.imprimir_via_cozinha(self.carrinho)
            
            messagebox.showinfo("Sucesso", "Mesa Atualizada!", parent=self)
            self.mostrar_mapa_mesas()
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao salvar: {e}", parent=self)

    def tela_fechamento_conta(self):
        for widget in self.frame_central.winfo_children(): widget.destroy()
        
        # Cálculo do total (Pedidos já salvos + Novos no carrinho)
        self.total_conta = sum(q * self.precos[i] for i, q in self.itens_ja_pedidos.items()) + \
                        sum(q * self.precos[i] for i, q in self.carrinho.items())
        
        self.pagamentos_lista = [] # Guarda tuplas (valor, forma)
        self.saldo_restante = self.total_conta

        ctkinter.CTkLabel(self.frame_central, text="💰 FINALIZAR CONTA", font=("Arial", 22, "bold")).pack(pady=15)
        
        # Painel de Saldo Dinâmico
        self.f_saldo = ctkinter.CTkFrame(self.frame_central, fg_color="#2c3e50", height=100)
        self.f_saldo.pack(fill="x", padx=40, pady=10)
        
        self.lbl_saldo_dinamico = ctkinter.CTkLabel(self.f_saldo, 
            text=f"VALOR RESTANTE: R$ {self.saldo_restante:.2f}", 
            font=("Arial", 26, "bold"), text_color="#f1c40f")
        self.lbl_saldo_dinamico.place(relx=0.5, rely=0.5, anchor="center")

        # Seleção de Forma Única ou Múltipla
        ctkinter.CTkLabel(self.frame_central, text="Escolha como o cliente vai pagar:", font=("Arial", 14)).pack(pady=5)
        
        self.forma_pag = ctkinter.CTkOptionMenu(self.frame_central, width=350, height=40,
            values=["Dinheiro", "PIX", "Cartão Débito", "Cartão Crédito à Vista", "Múltiplas Formas"],
            command=self.toggle_interface_pagamento)
        self.forma_pag.pack(pady=10)

        # Container para os campos de pagamento (Misto ou Único)
        self.container_pagamento = ctkinter.CTkFrame(self.frame_central, fg_color="transparent")
        self.container_pagamento.pack(fill="both", expand=True, padx=40)

        # Botão Finalizar (Inicia desativado por segurança)
        self.btn_finalizar = ctkinter.CTkButton(self.frame_central, text="FINALIZAR VENDA", 
                                            fg_color="gray", height=55, width=350, 
                                            font=("Arial", 18, "bold"), command=self.finalizar_venda)
        self.btn_finalizar.pack(pady=20)

    def toggle_interface_pagamento(self, escolha):
        for w in self.container_pagamento.winfo_children(): w.destroy()
        
        if escolha == "Múltiplas Formas":
            # Campos para adicionar valores parciais
            f_add = ctkinter.CTkFrame(self.container_pagamento)
            f_add.pack(fill="x", pady=10)
            
            self.ent_v_parcial = ctkinter.CTkEntry(f_add, placeholder_text="Valor R$", width=120)
            self.ent_v_parcial.pack(side="left", padx=10, pady=10)
            
            self.f_m_parcial = ctkinter.CTkOptionMenu(f_add, values=["Dinheiro", "PIX", "Débito", "Crédito"], width=130)
            self.f_m_parcial.pack(side="left", padx=5)
            
            ctkinter.CTkButton(f_add, text="ADICIONAR +", width=100, fg_color="#16a085", 
                            command=self.adicionar_valor_misto).pack(side="left", padx=10)

            # Lista onde os pagamentos vão aparecendo embaixo
            self.scroll_pagos = ctkinter.CTkScrollableFrame(self.container_pagamento, height=200, label_text="Pagamentos Lançados")
            self.scroll_pagos.pack(fill="both", expand=True, pady=5)
            
            self.btn_finalizar.configure(fg_color="gray", state="disabled") # Só libera quando saldo for 0
        else:
            ctkinter.CTkLabel(self.container_pagamento, text=f"O valor total de R$ {self.total_conta:.2f}\nserá quitado via {escolha}.", 
                            font=("Arial", 14, "italic")).pack(pady=20)
            self.btn_finalizar.configure(fg_color="#27ae60", state="normal")

    def adicionar_valor_misto(self):
        try:
            valor = float(self.ent_v_parcial.get().replace(",", "."))
            forma = self.f_m_parcial.get()
            
            if valor > (self.saldo_restante + 0.01):
                messagebox.showwarning("Aviso", "Valor maior que o saldo restante!", parent=self)
                return

            self.pagamentos_lista.append((valor, forma))
            self.saldo_restante -= valor
            
            # Atualiza visual do saldo
            self.lbl_saldo_dinamico.configure(text=f"VALOR RESTANTE: R$ {self.saldo_restante:.2f}")
            
            # Adiciona linha visual na lista embaixo
            f_item = ctkinter.CTkFrame(self.scroll_pagos, fg_color="transparent")
            f_item.pack(fill="x", pady=2)
            ctkinter.CTkLabel(f_item, text=f"✔ {forma}: R$ {valor:.2f}", font=("Arial", 13)).pack(side="left", padx=10)
            
            self.ent_v_parcial.delete(0, "end")

            # Se saldo zerou, libera o botão
            if self.saldo_restante < 0.05: # Tolerância de centavos
                self.lbl_saldo_dinamico.configure(text="CONTA QUITADA!", text_color="#2ecc71")
                self.btn_finalizar.configure(fg_color="#27ae60", state="normal")
        
        except ValueError:
            messagebox.showerror("Erro", "Digite um valor numérico válido.", parent=self)

    def finalizar_venda(self):
        # 1. Identifica quais são os recebimentos
        if self.forma_pag.get() == "Múltiplas Formas":
            pago_agora = sum(v for v, f in self.pagamentos_lista)
            # Verifica se realmente pagou tudo (tolerância de 5 centavos)
            if pago_agora < (self.total_conta - 0.05):
                messagebox.showwarning("Saldo Pendente", f"Ainda faltam R$ {self.total_conta - pago_agora:.2f}", parent=self)
                return
            recebimentos = self.pagamentos_lista
        else:
            # Pagamento único
            recebimentos = [(self.total_conta, self.forma_pag.get())]

        try:
            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()
            
            # 2. Registra a Venda Geral
            cursor.execute("INSERT INTO vendas (id_mesa, valor_total, forma_pagamento) VALUES (?, ?, ?)", 
                        (self.mesa_atual, self.total_conta, self.forma_pag.get()))
            id_venda = cursor.lastrowid
            
            # 3. Registra cada parte do pagamento (Importante para o financeiro!)
            for valor, forma in recebimentos:
                cursor.execute("INSERT INTO recebimentos (id_venda, valor, forma_pagamento) VALUES (?, ?, ?)", 
                            (id_venda, valor, forma))
            
            # 4. Move itens da mesa para o HISTÓRICO (Para o Ranking funcionar)
            cursor.execute("SELECT item_nome, valor FROM pedidos WHERE id_mesa=?", (self.mesa_atual,))
            itens_mesa = cursor.fetchall()
            for nome, preco in itens_mesa:
                cursor.execute("INSERT INTO itens_vendidos_historico (id_venda, item_nome, valor) VALUES (?, ?, ?)", 
                            (id_venda, nome, preco))

            # 5. LIMPEZA TOTAL DA MESA (O que estava faltando!)
            cursor.execute("UPDATE mesas SET status='Livre', cliente_nome='', cliente_contato='', observacao='' WHERE numero=?", (self.mesa_atual,))
            cursor.execute("DELETE FROM pedidos WHERE id_mesa=?", (self.mesa_atual,))
            
            conn.commit() # Salva tudo no "caderno"
            conn.close()
            
            messagebox.showinfo("Sucesso", f"Mesa {self.mesa_atual:02d} finalizada e liberada!", parent=self)
            self.mostrar_mapa_mesas() # Volta para os quadradinhos verdes/amarelos
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível liberar a mesa: {e}", parent=self)

    def formatar_nome_item(self, nome, largura_max=22):
        """Função auxiliar para quebrar nomes longos sem perder informação"""
        if len(nome) <= largura_max:
            return nome
        # Se for maior, ele apenas corta mas sem os pontinhos, 
        # ou você pode optar por deixar o nome em duas linhas (mais complexo).
        # Para 58mm, o ideal é abreviar palavras comuns ou permitir 2 linhas:
        return nome[:largura_max]

    def imprimir_via_cozinha(self, novos_itens):
        # 1. Pegamos todas as categorias que existem no seu banco de dados
        # 2. Filtramos para REMOVER a categoria "Bebidas" (independente de maiúscula/minúscula)
        categorias_cozinha = [
            cat for cat in self.itens_por_categoria.keys() 
            if cat.lower() != "bebidas"
        ]
        
        # 3. Filtramos os itens que pertencem a essas categorias permitidas
        itens_para_imprimir = {
            item: qtd for item, qtd in novos_itens.items() 
            if any(item in self.itens_por_categoria.get(cat, []) for cat in categorias_cozinha)
        }
        
        # Se não houver nada para imprimir (ex: só pediram bebida), a função para aqui
        if not itens_para_imprimir: 
            return

        data_h = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # --- PADRÃO 80MM ---
        txt =  "================================================\n"
        txt += "               PEDIDO COZINHA                   \n"
        txt += "================================================\n"
        txt += f"MESA: {self.mesa_atual:02d} | DATA/HORA: {data_h}\n"
        txt += "------------------------------------------------\n"
        txt += f"{'QTD':<5} | {'ITEM':<40}\n"
        txt += "------------------------------------------------\n"
        
        for item, qtd in itens_para_imprimir.items():
            txt += f"{qtd:>3}x   | {item.upper():<38}\n"
        
        txt += "------------------------------------------------\n"
        txt += "           BOM TRABALHO, EQUIPE!                \n"
        txt += "================================================\n\n\n\n\n"
        
        self.salvar_e_abrir_txt(f"cozinha_m{self.mesa_atual}.txt", txt)

    def abrir_pop_up_adicionais_mesas(self, item_id, item_nome, item_preco):
        """Abre a janela de adicionais antes de confirmar o item."""
        pop_up = ctkinter.CTkToplevel(self)
        pop_up.title(f"Adicionais: {item_nome}")
        pop_up.geometry("400x600")
        pop_up.transient(self)
        pop_up.after(150, pop_up.grab_set)

        ctkinter.CTkLabel(pop_up, text=f"Personalizar {item_nome}", font=("Arial", 16, "bold")).pack(pady=15)
        
        # Buscar ID do item no cardápio pelo nome para achar os adicionais vinculados
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cardapio WHERE nome = ?", (item_nome,))
        res = cursor.fetchone()
        
        lista_checkboxes = {}
        adicionais_disponiveis = []

        if res:
            id_do_cardapio = res[0]
            query = """
                SELECT a.id, a.nome, a.preco 
                FROM adicionais a
                JOIN item_adicionais ia ON a.id = ia.id_adicional
                WHERE ia.id_item = ?
            """
            cursor.execute(query, (id_do_cardapio,))
            adicionais_disponiveis = cursor.fetchall()
        conn.close()

        if not adicionais_disponiveis:
            ctkinter.CTkLabel(pop_up, text="Este item não possui adicionais específicos.").pack(pady=10)
        else:
            frame_lista = ctkinter.CTkScrollableFrame(pop_up, width=350, height=250)
            frame_lista.pack(pady=10, padx=20)
            for ad_id, ad_nome, ad_preco in adicionais_disponiveis:
                var = ctkinter.BooleanVar(value=False)
                cb = ctkinter.CTkCheckBox(frame_lista, text=f"{ad_nome} (+ R$ {ad_preco:.2f})", variable=var)
                cb.pack(anchor="w", pady=5, padx=10)
                lista_checkboxes[ad_id] = {"var": var, "nome": ad_nome, "preco": ad_preco}

        ctkinter.CTkLabel(pop_up, text="Observações:").pack(pady=(10, 0))
        entry_obs = ctkinter.CTkEntry(pop_up, width=300, placeholder_text="Sem cebola, mal passado...")
        entry_obs.pack(pady=5)

        def confirmar():
            valor_total_item = item_preco
            detalhes = []
            for ad_id, info in lista_checkboxes.items():
                if info["var"].get():
                    valor_total_item += info["preco"]
                    detalhes.append(info["nome"])
            
            obs = entry_obs.get().strip()
            detalhes_str = f"Add: {', '.join(detalhes)}" if detalhes else ""
            if obs: detalhes_str += f" | Obs: {obs}" if detalhes_str else f"Obs: {obs}"

            # Agora sim, adiciona ao pedido usando o método que você já tem
            self.adicionar_item_pedido(item_nome, valor_total_item, detalhes_str)
            pop_up.destroy()

        ctkinter.CTkButton(pop_up, text="✅ Confirmar", fg_color="green", command=confirmar).pack(pady=20)

    def imprimir_pre_conta(self):
        todos = {}
        for i, q in self.itens_ja_pedidos.items(): todos[i] = todos.get(i, 0) + q
        for i, q in self.carrinho.items(): todos[i] = todos.get(i, 0) + q
        if not todos: return

        data_h = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # --- CABEÇALHO ---
        txt =  "================================================"
        txt += "\n             CONFERENCIA DE CONSUMO             "
        txt += "\n================================================"
        txt += f"\n MESA: {self.mesa_atual:02d} | CLIENTE: {self.ent_nome.get()[:20]:<20}"
        txt += f"\n DATA: {data_h}"
        txt += "\n------------------------------------------------"
        # Cabeçalho da Tabela (QTD + UNIT + TOTAL)
        txt += f"\n{'QTD':<6} {'VALOR UNIT.':>18} {'TOTAL':>19}"
        txt += "\n------------------------------------------------"
        
        total_geral = 0
        for item, qtd in todos.items():
            prc = self.precos.get(item, 0)
            sub = qtd * prc
            total_geral += sub
            
            # LINHA 1: Quantidade e Valores alinhados nas pontas
            # Ocupa 48 caracteres de largura
            txt += f"\n{str(qtd)+'x':<6} {prc:>18.2f} {sub:>19.2f}"
            
            # LINHA 2: O Nome do Item logo abaixo (pode ser grande que não quebra as colunas)
            txt += f"\n      {item.upper()}"
            txt += "\n------------------------------------------------"
        
        txt += f"\n TOTAL A PAGAR:                      R${total_geral:>9.2f}"
        txt += "\n------------------------------------------------"
        txt += "\n          OBRIGADO PELA PREFERENCIA!            "
        txt += "\n================================================\n\n\n\n\n"
        
        self.salvar_e_abrir_txt(f"conta_m{self.mesa_atual}.txt", txt)

    def salvar_e_abrir_txt(self, nome, conteudo):
        """Função auxiliar para salvar e abrir o arquivo"""
        with open(nome, "w", encoding="utf-8") as f:
            f.write(conteudo)
        if os.name == 'nt': os.startfile(nome)
        else: os.system(f"xdg-open {nome}")

    def adicionar_item_pedido(self, nome, valor, detalhes):
        if nome not in self.carrinho:
            self.carrinho[nome] = 0
        
        self.carrinho[nome] += 1

        # Aqui você pode evoluir depois para salvar os detalhes separados
        print(f"Item: {nome} | Valor: {valor} | Detalhes: {detalhes}")

        self.atualizar_visual_resumo()
    def confirmar_pedido(self):
        print("🔥 FUNÇÃO NOVA RODANDO 🔥")

class JanelaFaturamento(ctkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Relatórios e Performance")
        self.geometry("1000x750")
        self.after(100, self.grab_set)
        
        self.tabview = ctkinter.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Diário")
        self.tabview.add("Performance")
        self.tabview.add("Itens Vendidos")
        
        self.renderizar_diario()
        self.setup_aba_performance()
        self.renderizar_ranking()

    def renderizar_diario(self):
        tab = self.tabview.tab("Diário")
        # CORREÇÃO ERRO 1: Limpa tudo antes de redesenhar
        for w in tab.winfo_children(): w.destroy()

        ctkinter.CTkLabel(tab, text="FATURAMENTO HOJE", font=("Arial", 20, "bold")).pack(pady=10)
        
        # Botão Excel
        ctkinter.CTkButton(tab, text="📥 Gerar Planilha Excel", fg_color="#27ae60", 
                           command=exportar_vendas_excel).pack(pady=10)

        frame_cards = ctkinter.CTkFrame(tab, fg_color="transparent")
        frame_cards.pack(pady=10)

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT forma_pagamento, SUM(valor) FROM recebimentos WHERE date(data_pagamento) = date('now') GROUP BY forma_pagamento")
        dados = cursor.fetchall()
        conn.close()

        total = 0
        for i, (forma, valor) in enumerate(dados):
            card = ctkinter.CTkFrame(frame_cards, width=180, height=80, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=5)
            ctkinter.CTkLabel(card, text=forma).pack()
            ctkinter.CTkLabel(card, text=f"R$ {valor:.2f}", font=("Arial", 16, "bold")).pack()
            total += valor
        
        ctkinter.CTkLabel(tab, text=f"TOTAL BRUTO: R$ {total:.2f}", font=("Arial", 24, "bold")).pack(pady=20)
        ctkinter.CTkButton(tab, text="🔄 Atualizar", command=self.renderizar_diario).pack()

    def renderizar_ranking(self):
        tab = self.tabview.tab("Itens Vendidos")
        for w in tab.winfo_children(): w.destroy()
        
        # CORREÇÃO ERRO 2: Ranking por Categoria
        txt = ctkinter.CTkTextbox(tab, width=600, height=400, font=("Courier", 13))
        txt.pack(pady=10)

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        # Aqui, no futuro, vamos cruzar com a tabela de cardápio para pegar a categoria real
        cursor.execute("SELECT item_nome, COUNT(*) as qtd FROM itens_vendidos_historico GROUP BY item_nome ORDER BY qtd DESC")
        
        txt.insert("end", f"{'QTD':<5} | {'ITEM':<25}\n" + "-"*35 + "\n")
        for nome, qtd in cursor.fetchall():
            txt.insert("end", f"{qtd:>3}x   | {nome:<25}\n")
        conn.close()

    def obter_dados_hoje(self):
        """Busca no banco o que entrou hoje por forma de pagamento"""
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        # Soma por forma de pagamento na tabela recebimentos (usando a data de hoje)
        cursor.execute("""
            SELECT forma_pagamento, SUM(valor) 
            FROM recebimentos 
            WHERE date(data_pagamento) = date('now', 'localtime')
            GROUP BY forma_pagamento
        """)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def setup_aba_diario(self):
        aba = self.tabview.tab("Faturamento Diário")
        
        for widget in aba.winfo_children():
            widget.destroy()

        ctkinter.CTkLabel(aba, text="RESUMO DE HOJE", font=("Arial", 20, "bold")).pack(pady=10)
        
        frame_cards = ctkinter.CTkFrame(aba, fg_color="transparent")
        frame_cards.pack(fill="x", padx=10)

        dados = self.obter_dados_hoje()
        total_geral = 0
        
        # Criando "Cards" para cada tipo de entrada
        for i, (forma, valor) in enumerate(dados):
            card = ctkinter.CTkFrame(frame_cards, width=200, height=100, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10)
            ctkinter.CTkLabel(card, text=forma.upper(), font=("Arial", 12)).pack(pady=5)
            ctkinter.CTkLabel(card, text=f"R$ {valor:.2f}", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(pady=5)
            total_geral += valor

        # Totalizador no rodapé da aba
        self.lbl_total_dia = ctkinter.CTkLabel(aba, text=f"FATURAMENTO BRUTO TOTAL: R$ {total_geral:.2f}", 
                                               font=("Arial", 22, "bold"), text_color="#3498db")
        self.lbl_total_dia.pack(pady=30)
        
        ctkinter.CTkButton(aba, text="🔄 Atualizar Dados", command=self.setup_aba_diario).pack()

        ctkinter.CTkButton(aba, text="📥 Gerar Planilha Excel", fg_color="#27ae60", 
                   command=self.exportar_para_excel).pack(pady=5)

    def setup_aba_performance(self):
        aba = self.tabview.tab("Performance")
        for w in aba.winfo_children(): w.destroy()

        ctkinter.CTkLabel(aba, text="📊 DESEMPENHO DE VENDAS", font=("Arial", 20, "bold")).pack(pady=10)

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()

        # 1. Vendas por Dia da Semana (Últimos 30 dias)
        # 0=Sunday, 6=Saturday no SQLite
        query_dias = """
            SELECT strftime('%w', data_pagamento) as dia_semana, SUM(valor) 
            FROM recebimentos 
            WHERE data_pagamento >= date('now', '-30 days')
            GROUP BY dia_semana
        """
        cursor.execute(query_dias)
        vendas_dias = dict(cursor.fetchall())
        
        nomes_dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        
        # Exibição visual simples (Barras de texto ou Cards)
        frame_performance = ctkinter.CTkFrame(aba)
        frame_performance.pack(fill="x", padx=20, pady=10)

        for i, nome in enumerate(nomes_dias):
            valor = vendas_dias.get(str(i), 0)
            f = ctkinter.CTkFrame(frame_performance, width=80, height=100)
            f.pack(side="left", expand=True, padx=5, pady=10)
            ctkinter.CTkLabel(f, text=nome, font=("Arial", 12, "bold")).pack(pady=5)
            ctkinter.CTkLabel(f, text=f"R${valor:.0f}", font=("Arial", 11)).pack()

        # 2. Resumo Financeiro (Bruto vs Líquido Estimado)
        cursor.execute("SELECT valor, forma_pagamento FROM recebimentos WHERE data_pagamento >= date('now', '-30 days')")
        todos_recebimentos = cursor.fetchall()
        conn.close()

        bruto_total = sum(item[0] for item in todos_recebimentos)
        liquido_total = sum(self.calcular_liquido(item[0], item[1]) for item in todos_recebimentos)
        taxas_pagas = bruto_total - liquido_total

        # Painel de Resultados
        f_resumo = ctkinter.CTkFrame(aba, fg_color="#34495e")
        f_resumo.pack(fill="x", padx=20, pady=20)
        
        ctkinter.CTkLabel(f_resumo, text=f"Faturamento Bruto (30 dias): R$ {bruto_total:.2f}", text_color="white").pack(pady=5)
        ctkinter.CTkLabel(f_resumo, text=f"Total de Taxas Maquininha: - R$ {taxas_pagas:.2f}", text_color="#e74c3c").pack(pady=5)
        ctkinter.CTkLabel(f_resumo, text=f"LUCRO LÍQUIDO ESTIMADO: R$ {liquido_total:.2f}", 
                          font=("Arial", 18, "bold"), text_color="#2ecc71").pack(pady=10)

    def setup_aba_ranking(self):
        aba = self.tabview.tab("Itens Mais Vendidos")
        for widget in aba.winfo_children(): widget.destroy()

        ctkinter.CTkLabel(aba, text="🏆 RANKING POR CATEGORIA", font=("Arial", 20, "bold")).pack(pady=10)
        lista_rank = ctkinter.CTkTextbox(aba, width=550, height=400, font=("Courier", 13))
        lista_rank.pack(pady=10)

        # Categorias que já definimos no JanelaMesas
        categorias = {
            "LANCHES": ["FRT Classico", "FRT Bacon", "FRT Salada Especial"],
            "BLENDS": ["Frango e Batata Especial", "Mega Blend"],
            "BEBIDAS": ["Coca Cola lata", "Fanta Laranja lata", "Pepsi 2 Litros", "Suco de Laranja 2 Litros"]
        }

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT item_nome, COUNT(item_nome) FROM itens_vendidos_historico GROUP BY item_nome ORDER BY COUNT(item_nome) DESC")
        vendas = dict(cursor.fetchall())
        conn.close()

        for cat, itens in categorias.items():
            lista_rank.insert("end", f"\n--- {cat} ---\n")
            for item in itens:
                qtd = vendas.get(item, 0)
                lista_rank.insert("end", f"{qtd:>3}x | {item:<25}\n") 

    def exportar_para_excel():
        try:
            conn = sqlite3.connect("lanchonete.db")
            
            # Lê as tabelas do banco de dados
            df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
            df_itens = pd.read_sql_query("SELECT * FROM itens_vendidos_historico", conn)
            
            conn.close()

            # Define o nome do arquivo com a data de hoje
            data_hoje = datetime.now().strftime("%d-%m-%Y")
            nome_arquivo = f"Relatorio_Vendas_{data_hoje}.xlsx"
            
            # Salva em Excel com duas abas diferentes
            with pd.ExcelWriter(nome_arquivo) as writer:
                df_vendas.to_excel(writer, sheet_name='Resumo_Vendas', index=False)
                df_itens.to_excel(writer, sheet_name='Itens_Detalhado', index=False)
                
            messagebox.showinfo("Sucesso", f"Excel gerado com sucesso: {nome_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", f"Erro: {e}")

    def calcular_liquido(self, valor_bruto, forma_pagamento):
        """Consulta o banco de taxas e subtrai a comissão da maquininha"""
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        
        # Mapeia a forma de pagamento para o nome da taxa no banco
        mapa = {
            "Dinheiro": None,
            "PIX": None, # PIX direto costuma ser 0%
            "Cartão Débito": "Debito_Point",
            "Cartão Crédito à Vista": "Credito_Point",
            "PIX Maquininha": "Pix_Point"
        }
        
        tag_taxa = mapa.get(forma_pagamento)
        if not tag_taxa:
            conn.close()
            return valor_bruto # Sem taxas
        
        cursor.execute("SELECT porcentagem FROM configuracoes_taxas WHERE nome_taxa=?", (tag_taxa,))
        res = cursor.fetchone()
        taxa = res[0] if res else 0
        conn.close()
        
        return valor_bruto * (1 - (taxa / 100))

class JanelaTaxas(ctkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuração de Taxas")
        self.geometry("500x600")
        self.after(100, self.grab_set)

        ctkinter.CTkLabel(self, text="⚙️ TAXAS E COMISSÕES", font=("Arial", 20, "bold")).pack(pady=20)
        
        self.entries = {}
        self.container = ctkinter.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=10)

        # Busca taxas do banco
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nome_taxa, porcentagem FROM configuracoes_taxas")
        for nome, valor in cursor.fetchall():
            f = ctkinter.CTkFrame(self.container, fg_color="transparent")
            f.pack(fill="x", pady=5)
            ctkinter.CTkLabel(f, text=nome.replace("_", " "), width=150, anchor="w").pack(side="left")
            ent = ctkinter.CTkEntry(f, width=80)
            ent.insert(0, str(valor))
            ent.pack(side="right")
            self.entries[nome] = ent
        conn.close()

        ctkinter.CTkButton(self, text="SALVAR ALTERAÇÕES", fg_color="#27ae60", command=self.salvar_taxas).pack(pady=20)

    def salvar_taxas(self):
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        for nome, ent in self.entries.items():
            cursor.execute("UPDATE configuracoes_taxas SET porcentagem=? WHERE nome_taxa=?", (float(ent.get()), nome))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Taxas atualizadas!", parent=self)

class JanelaCardapio(ctkinter.CTkToplevel):
    def __init__(self, parent):
            super().__init__(parent)
            self.title("Gerenciar Cardápio")
            self.geometry("700x700")
            self.after(100, self.grab_set)

            ctkinter.CTkLabel(self, text="🍔 GESTÃO DE CARDÁPIO", font=("Arial", 22, "bold")).pack(pady=15)

            # Apenas este botão no topo:
            self.btn_adicionar = ctk.CTkButton(self, text="➕ ADICIONAR NOVO ITEM", 
                                            command=self.abrir_form_novo_item, 
                                            fg_color="green", height=40)
            self.btn_adicionar.pack(pady=10)

            # Botão para abrir o Gerenciador de Adicionais
            ctkinter.CTkButton(self, text="🍔 Gerenciar Adicionais", 
                           fg_color="#f39c12", hover_color="#f1c40f", font=("Arial", 14, "bold"),
                           command=self.abrir_janela_adicionais).pack(pady=10)

            # Lista de Itens
            self.scroll_itens = ctkinter.CTkScrollableFrame(self, label_text="Itens no Sistema")
            self.scroll_itens.pack(fill="both", expand=True, padx=20, pady=10)
            
            self.renderizar_lista()
    
    def abrir_form_novo_item(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Novo Item")
        popup.geometry("420x600")

        frame_principal = ctk.CTkScrollableFrame(popup)
        frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame_principal, text="Cadastrar Novo Produto", font=("Arial", 16, "bold")).pack(pady=10)

        # Nome
        ctk.CTkLabel(frame_principal, text="Nome do produto").pack(anchor="w", padx=20)
        entry_nome = ctk.CTkEntry(frame_principal)
        entry_nome.pack(fill="x", padx=20, pady=(0,10))

        # Preço
        ctk.CTkLabel(frame_principal, text="Preço (R$)").pack(anchor="w", padx=20)
        entry_preco = ctk.CTkEntry(frame_principal)
        entry_preco.pack(fill="x", padx=20, pady=(0,10))

        # Categoria
        ctk.CTkLabel(frame_principal, text="Categoria").pack(anchor="w", padx=20)
        
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT categoria FROM cardapio")
        categorias = [row[0] for row in cursor.fetchall()]

        conn.close()    

        combo_categoria = ctk.CTkOptionMenu(frame_principal, values=categorias)
        combo_categoria.pack(fill="x", padx=20, pady=5)

        entry_nova_categoria = ctk.CTkEntry(frame_principal, placeholder_text="Ou digite nova categoria")
        entry_nova_categoria.pack(fill="x", padx=20, pady=(0,10))

        # Adicionais (checkbox)
        ctk.CTkLabel(frame_principal, text="Adicionais disponíveis").pack(pady=10)

        frame_add = ctk.CTkFrame(frame_principal)
        frame_add.pack(fill="x", padx=20, pady=5)

        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM adicionais")
        adicionais = cursor.fetchall()
        conn.close()

        vars_add = {}

        for ad_id, ad_nome in adicionais:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(frame_add, text=ad_nome, variable=var)
            cb.pack(anchor="w")
            vars_add[ad_id] = var

        # SALVAR
        def salvar():
            nome = entry_nome.get().strip()
            try:
                preco = float(entry_preco.get().replace(",", "."))
            except:
                messagebox.showerror("Erro", "Preço inválido")
                return

            nova_cat = entry_nova_categoria.get().strip()
            categoria = nova_cat if nova_cat else combo_categoria.get()

            if not nome:
                messagebox.showerror("Erro", "Nome obrigatório")
                return

            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()

            # Salva produto
            cursor.execute(
                "INSERT INTO cardapio (nome, preco, categoria) VALUES (?, ?, ?)",
                (nome, preco, categoria)
            )
            id_item = cursor.lastrowid

            # Salva vínculos com adicionais
            for ad_id, var in vars_add.items():
                if var.get():
                    cursor.execute(
                        "INSERT INTO item_adicionais (id_item, id_adicional) VALUES (?, ?)",
                        (id_item, ad_id)
                    )

            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Produto cadastrado!")

            
            popup.destroy()

        ctk.CTkButton(frame_principal, text="💾 SALVAR", fg_color="green", command=salvar).pack(pady=20)
    def abrir_janela_adicionais(self):
            janela_add = ctkinter.CTkToplevel(self)
            janela_add.title("Gerenciar Adicionais")
            janela_add.geometry("450x500")
            janela_add.transient(self)
            janela_add.after(150, janela_add.grab_set)

            # --- Área de Cadastro ---
            frame_top = ctkinter.CTkFrame(janela_add)
            frame_top.pack(pady=15, padx=15, fill="x")

            ctkinter.CTkLabel(frame_top, text="Novo Adicional (Ex: Bacon extra):", font=("Arial", 14, "bold")).pack(pady=(10, 5))
            entry_nome = ctkinter.CTkEntry(frame_top, width=250, placeholder_text="Nome do adicional")
            entry_nome.pack(pady=5)

            ctkinter.CTkLabel(frame_top, text="Preço (R$):", font=("Arial", 14, "bold")).pack(pady=5)
            entry_preco = ctkinter.CTkEntry(frame_top, width=150, placeholder_text="Ex: 3.50")
            entry_preco.pack(pady=5)

            def salvar_adicional():
                nome = entry_nome.get().strip()
                preco_str = entry_preco.get().replace(",", ".") # Aceita vírgula ou ponto
                
                if not nome or not preco_str:
                    messagebox.showwarning("Aviso", "Preencha o nome e o preço!", parent=janela_add)
                    return
                
                try:
                    preco = float(preco_str)
                    conn = sqlite3.connect("lanchonete.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO adicionais (nome, preco) VALUES (?, ?)", (nome, preco))
                    conn.commit()
                    conn.close()
                    
                    entry_nome.delete(0, 'end')
                    entry_preco.delete(0, 'end')
                    entry_nome.focus()
                    carregar_lista() # Atualiza a lista na hora
                except ValueError:
                    messagebox.showwarning("Erro", "Digite um valor numérico válido para o preço!", parent=janela_add)
                except sqlite3.OperationalError:
                    messagebox.showerror("Erro", "Tabela não encontrada. Você rodou o novo database.py?", parent=janela_add)

            ctkinter.CTkButton(frame_top, text="➕ Salvar Adicional", fg_color="#27ae60", hover_color="#2ecc71", 
                            command=salvar_adicional).pack(pady=15)

            # --- Área da Lista de Adicionais Cadastrados ---
            ctkinter.CTkLabel(janela_add, text="Adicionais Cadastrados:", font=("Arial", 14, "bold")).pack(pady=(10, 0))
            frame_lista = ctkinter.CTkScrollableFrame(janela_add, width=400, height=200)
            frame_lista.pack(pady=10, padx=15, fill="both", expand=True)

            def deletar_adicional(id_add):
                if messagebox.askyesno("Excluir", "Tem certeza que deseja apagar este adicional?", parent=janela_add):
                    conn = sqlite3.connect("lanchonete.db")
                    cursor = conn.cursor()
                    # Deleta o adicional e as ligações dele com os lanches
                    cursor.execute("DELETE FROM adicionais WHERE id = ?", (id_add,))
                    cursor.execute("DELETE FROM item_adicionais WHERE id_adicional = ?", (id_add,))
                    conn.commit()
                    conn.close()
                    carregar_lista()

            def carregar_lista():
                # Limpa a tela antes de atualizar
                for widget in frame_lista.winfo_children():
                    widget.destroy()
                
                try:
                    conn = sqlite3.connect("lanchonete.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, nome, preco FROM adicionais ORDER BY nome")
                    adicionais = cursor.fetchall()
                    conn.close()

                    for ad_id, ad_nome, ad_preco in adicionais:
                        linha = ctkinter.CTkFrame(frame_lista, fg_color="transparent")
                        linha.pack(fill="x", pady=2)
                        
                        texto = f"{ad_nome} - R$ {ad_preco:.2f}"
                        ctkinter.CTkLabel(linha, text=texto, font=("Arial", 13)).pack(side="left", padx=10)
                        
                        ctkinter.CTkButton(linha, text="❌", width=30, height=25, fg_color="#c0392b", hover_color="#e74c3c",
                                        command=lambda id_add=ad_id: deletar_adicional(id_add)).pack(side="right", padx=10)
                except sqlite3.OperationalError:
                    ctkinter.CTkLabel(frame_lista, text="Erro ao carregar banco de dados.", text_color="red").pack()

            # Carrega a lista ao abrir a janela
            carregar_lista()

    def renderizar_lista(self):
            for w in self.scroll_itens.winfo_children(): w.destroy()
            
            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()
            # Note que agora buscamos também os ingredientes
            cursor.execute("SELECT id, nome, categoria, preco, ingredientes FROM cardapio ORDER BY categoria")
            itens = cursor.fetchall()
            conn.close()

            for info in itens:
                f = ctkinter.CTkFrame(self.scroll_itens, fg_color="transparent")
                f.pack(fill="x", pady=5)

                ctkinter.CTkLabel(f, text=f"{info[1]} ({info[2]}) - R$ {info[3]:.2f}", 
                                font=("Arial", 13), width=350, anchor="w").pack(side="left", padx=10)
                
                ctkinter.CTkButton(f, text="🗑️", width=40, fg_color="#c0392b", 
                                command=lambda i=info[0]: self.excluir_item(i)).pack(side="right", padx=5)
                
                # Aqui estava o erro! Agora chamamos abrir_janela_item passando os dados
                ctkinter.CTkButton(f, text="📝", width=40, fg_color="#2980b9", 
                                command=lambda d=info: self.abrir_janela_item(d)).pack(side="right", padx=5)

    def abrir_janela_item(self, dados_item=None):
        janela_item = ctkinter.CTkToplevel(self)
        janela_item.title("Cadastrar/Editar Item")
        janela_item.geometry("500x750") # Aumentei a altura para caber os adicionais
        janela_item.transient(self)
        janela_item.after(150, janela_item.grab_set)

        # Campos de texto
        ctkinter.CTkLabel(janela_item, text="Nome do Item:").pack(pady=(10, 0))
        entry_nome = ctkinter.CTkEntry(janela_item, width=300)
        entry_nome.pack(pady=5)

        ctkinter.CTkLabel(janela_item, text="Categoria:").pack(pady=5)
        entry_cat = ctkinter.CTkEntry(janela_item, width=300)
        entry_cat.pack(pady=5)

        ctkinter.CTkLabel(janela_item, text="Preço:").pack(pady=5)
        entry_preco = ctkinter.CTkEntry(janela_item, width=300)
        entry_preco.pack(pady=5)

        ctkinter.CTkLabel(janela_item, text="Ingredientes:").pack(pady=5)
        entry_ingred = ctkinter.CTkEntry(janela_item, width=300)
        entry_ingred.pack(pady=5)

        # --- SEÇÃO DE ADICIONAIS DISPONÍVEIS ---
        ctkinter.CTkLabel(janela_item, text="Selecione os Adicionais Disponíveis:", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        frame_checks = ctkinter.CTkScrollableFrame(janela_item, width=350, height=200)
        frame_checks.pack(pady=5, padx=20)

        # Carregar todos os adicionais do banco
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM adicionais ORDER BY nome")
        todos_adicionais = cursor.fetchall()
        
        # Se for edição, carregar quais já estão marcados
        adicionais_marcados = []
        if dados_item:
            cursor.execute("SELECT id_adicional FROM item_adicionais WHERE id_item = ?", (dados_item[0],))
            adicionais_marcados = [row[0] for row in cursor.fetchall()]
        conn.close()

        lista_checkboxes = {} # Para guardar as variáveis e saber o que foi marcado

        for id_ad, nome_ad in todos_adicionais:
            var = ctkinter.BooleanVar(value=(id_ad in adicionais_marcados))
            cb = ctkinter.CTkCheckBox(frame_checks, text=nome_ad, variable=var)
            cb.pack(anchor="w", pady=2, padx=10)
            lista_checkboxes[id_ad] = var

        if dados_item:
            entry_nome.insert(0, dados_item[1])
            entry_cat.insert(0, dados_item[2])
            entry_preco.insert(0, str(dados_item[3]))
            entry_ingred.insert(0, dados_item[4] if dados_item[4] else "")

        def salvar():
            nome = entry_nome.get()
            cat = entry_cat.get()
            preco = entry_preco.get()
            ingred = entry_ingred.get()

            if not nome or not cat or not preco:
                messagebox.showwarning("Aviso", "Preencha os campos obrigatórios!")
                return

            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()

            if dados_item: # EDITAR
                id_item = dados_item[0]
                cursor.execute("UPDATE cardapio SET nome=?, categoria=?, preco=?, ingredientes=? WHERE id=?",
                            (nome, cat, float(preco), ingred, id_item))
                # Limpa os adicionais antigos para inserir os novos marcados
                cursor.execute("DELETE FROM item_adicionais WHERE id_item = ?", (id_item,))
            else: # NOVO
                cursor.execute("INSERT INTO cardapio (nome, categoria, preco, ingredientes) VALUES (?, ?, ?, ?)",
                            (nome, cat, float(preco), ingred))
                id_item = cursor.lastrowid

            # Salva os novos adicionais selecionados
            for id_ad, var in lista_checkboxes.items():
                if var.get():
                    cursor.execute("INSERT INTO item_adicionais (id_item, id_adicional) VALUES (?, ?)", (id_item, id_ad))

            conn.commit()
            conn.close()
            self.renderizar_lista()
            janela_item.destroy()

        ctkinter.CTkButton(janela_item, text="Confirmar", command=salvar, fg_color="green").pack(pady=20)

    def abrir_pop_up_adicionais(self, item_id, item_nome, item_preco, id_mesa, callback_atualizar):
        """
        Abre uma janela para selecionar os adicionais antes de confirmar o item na mesa.
        """
        pop_up = ctkinter.CTkToplevel(self)
        pop_up.title(f"Adicionais: {item_nome}")
        pop_up.geometry("400x550")
        pop_up.transient(self)
        pop_up.after(150, pop_up.grab_set)

        ctkinter.CTkLabel(pop_up, text=f"Personalizar {item_nome}", font=("Arial", 16, "bold")).pack(pady=15)
        
        # --- BUSCAR ADICIONAIS VINCULADOS ---
        conn = sqlite3.connect("lanchonete.db")
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.nome, a.preco 
            FROM adicionais a
            JOIN item_adicionais ia ON a.id = ia.id_adicional
            WHERE ia.id_item = ?
        """
        cursor.execute(query, (item_id,))
        adicionais_disponiveis = cursor.fetchall()
        conn.close()

        lista_checkboxes = {}

        if not adicionais_disponiveis:
            ctkinter.CTkLabel(pop_up, text="Nenhum adicional disponível para este item.").pack(pady=20)
        else:
            frame_lista = ctkinter.CTkScrollableFrame(pop_up, width=350, height=300)
            frame_lista.pack(pady=10, padx=20)

            for ad_id, ad_nome, ad_preco in adicionais_disponiveis:
                var = ctkinter.BooleanVar(value=False)
                cb = ctkinter.CTkCheckBox(frame_lista, text=f"{ad_nome} (+ R$ {ad_preco:.2f})", variable=var)
                cb.pack(anchor="w", pady=5, padx=10)
                lista_checkboxes[ad_id] = {"var": var, "nome": ad_nome, "preco": ad_preco}

        # --- OBSERVAÇÃO ---
        ctkinter.CTkLabel(pop_up, text="Observações (Ex: Sem cebola):").pack(pady=(10, 0))
        entry_obs = ctkinter.CTkEntry(pop_up, width=300, placeholder_text="Remover ingredientes, ponto da carne...")
        entry_obs.pack(pady=5)

        def confirmar_item():
            preco_final = item_preco
            detalhes_lista = []
            
            # Soma os adicionais marcados
            for ad_id, info in lista_checkboxes.items():
                if info["var"].get():
                    preco_final += info["preco"]
                    detalhes_lista.append(info["nome"])
            
            obs = entry_obs.get().strip()
            # Monta a string de detalhes: "Adicionais: Bacon, Ovo | Obs: Sem sal"
            detalhes_str = ""
            if detalhes_lista:
                detalhes_str += "Adicionais: " + ", ".join(detalhes_lista)
            if obs:
                detalhes_str += f" | Obs: {obs}" if detalhes_str else f"Obs: {obs}"

            # SALVAR NO BANCO DE DADOS (Tabela pedidos)
            try:
                conn = sqlite3.connect("lanchonete.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pedidos (id_mesa, item_nome, valor, detalhes, status_pedido) 
                    VALUES (?, ?, ?, ?, ?)
                """, (id_mesa, item_nome, preco_final, detalhes_str, 'Pendente'))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sucesso", f"{item_nome} adicionado!", parent=pop_up)
                callback_atualizar() # Atualiza a lista da mesa
                pop_up.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

        ctkinter.CTkButton(pop_up, text="✅ Confirmar e Adicionar", fg_color="green", 
                        command=confirmar_item).pack(pady=20)

    def processar_salvamento(self, id_item, nome, cat, preco, ingredientes):
            try:
                conn = sqlite3.connect("lanchonete.db")
                cursor = conn.cursor()
                
                if id_item: # Se tem ID, é EDIÇÃO
                    cursor.execute("""UPDATE cardapio 
                                SET nome=?, categoria=?, preco=?, ingredientes=? 
                                WHERE id=?""", (nome, cat, float(preco), ingredientes, id_item))
                    msg = "Item atualizado!"
                else: # Se não tem ID, é NOVO ITEM
                    cursor.execute("""INSERT INTO cardapio (nome, categoria, preco, ingredientes) 
                                VALUES (?, ?, ?, ?)""", (nome, cat, float(preco), ingredientes))
                    msg = "Item adicionado!"

                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sucesso", msg, parent=self.janela_form)
                self.janela_form.destroy() # Fecha a janelinha
                self.renderizar_lista()    # Atualiza a lista principal
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}", parent=self.janela_form)

    def salvar_item(self):
        nome = self.ent_nome.get()
        preco = self.ent_preco.get().replace(",", ".")
        cat = self.ent_cat.get()
        
        if not nome or not preco or not cat:
            messagebox.showwarning("Aviso", "Preencha todos os campos!", parent=self)
            return

        try:
            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()
            
            if self.id_editando:
                # LÓGICA DE EDIÇÃO
                cursor.execute("UPDATE cardapio SET nome=?, categoria=?, preco=? WHERE id=?", 
                            (nome, cat, float(preco), self.id_editando))
                self.id_editando = None # Reseta após editar
                messagebox.showinfo("Sucesso", "Item atualizado!", parent=self)
            else:
                # LÓGICA DE NOVO CADASTRO
                cursor.execute("INSERT INTO cardapio (nome, categoria, preco) VALUES (?, ?, ?)", 
                            (nome, cat, float(preco)))
                messagebox.showinfo("Sucesso", "Item adicionado!", parent=self)

            conn.commit()
            conn.close()
            self.renderizar_lista()
            
            # Limpa campos
            self.ent_nome.delete(0, "end")
            self.ent_preco.delete(0, "end")
            self.ent_cat.delete(0, "end")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}", parent=self) 

    def excluir_item(self, id_item):
        if messagebox.askyesno("Confirmar", "Deseja excluir este item do cardápio?", parent=self):
            conn = sqlite3.connect("lanchonete.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cardapio WHERE id=?", (id_item,))
            conn.commit()
            conn.close()
            self.renderizar_lista()
    
def realizar_backup_manual():
    try:
        # Cria a pasta de backups se não existir
        if not os.path.exists("backups"):
            os.makedirs("backups")

        data_hora = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_arquivo = f"backups/backup_lanchonete_{data_hora}.db"
        
        # Copia o banco de dados atual para a pasta de backup
        shutil.copy2("lanchonete.db", nome_arquivo)
        
        messagebox.showinfo("Backup", f"Cópia de segurança criada com sucesso!\nSalvo em: {nome_arquivo}")
    except Exception as e:
        messagebox.showerror("Erro no Backup", f"Não foi possível criar o backup: {e}")

class AppPrincipal(ctkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão Pro - Lanchonete")
        self.geometry("700x600")

        # Banner Principal
        self.banner = ctkinter.CTkLabel(self, text="FRITOS", font=("Arial", 26, "bold"), 
                                        height=120, fg_color="#2c3e50", text_color="white", corner_radius=10)
        self.banner.pack(pady=20, padx=20, fill="x")

        # Container de Botões (Grid 2x3)
        self.frame_btn = ctkinter.CTkFrame(self, fg_color="transparent")
        self.frame_btn.pack(pady=10)

        # Fileira 1
        self.criar_botao("📦 Abrir Caixa / Mesas", self.abrir_mesas, 0, 0)
        self.criar_botao("📊 Faturamento", self.abrir_faturamento, 0, 1)

        # Fileira 2
        self.criar_botao("🍔 Cardápio", self.abrir_cardapio, 1, 0)
        self.criar_botao("⚙️ Taxas", self.abrir_taxas, 1, 1)

        # Fileira 3
        self.criar_botao("💾 Backup", self.abrir_backup, 2, 0)
        self.criar_botao("❌ Sair", self.quit, 2, 1, cor="#c0392b")

    def criar_botao(self, texto, comando, linha, coluna, cor=None):
        btn = ctkinter.CTkButton(self.frame_btn, text=texto, width=280, height=60, 
                                 font=("Arial", 15, "bold"), fg_color=cor, command=comando)
        btn.grid(row=linha, column=coluna, padx=15, pady=15)

    # Funções para chamar as janelas (vamos construir as outras telas agora)
    def abrir_mesas(self):
        JanelaMesas(self)

    def abrir_faturamento(self):
        JanelaFaturamento(self)

    def abrir_cardapio(self):
        JanelaCardapio(self)

    def abrir_taxas(self):
        JanelaTaxas(self)

    def abrir_backup(self):
        realizar_backup_manual()

if __name__ == "__main__":
    # Garante que as tabelas existam ao iniciar
    import database
    database.criar_tabelas()
    
    app = AppPrincipal()
    app.mainloop()