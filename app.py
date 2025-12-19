import streamlit as st
import pandas as pd
from fpdf import FPDF
from num2words import num2words
from datetime import datetime
import os
import tempfile

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador de Recibos - Sell", page_icon="🏢")

# --- FUNÇÕES AUXILIARES ---
def formatar_valor_extenso(valor):
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))
    try:
        extenso_reais = num2words(inteiro, lang='pt_BR').upper()
        texto = f"{extenso_reais} REAL" if inteiro == 1 else f"{extenso_reais} REAIS"
        if centavos > 0:
            extenso_centavos = num2words(centavos, lang='pt_BR').upper()
            texto += f" E {extenso_centavos} CENTAVOS"
    except NotImplementedError:
        texto = "VALOR POR EXTENSO (ERRO NA CONVERSÃO)"
    return texto

class PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            # Ajuste de posição do logo
            self.image(self.logo_path, x=160, y=10, w=35)
        self.ln(45)

    def footer(self):
        self.set_y(-35)
        self.set_font('Arial', '', 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 0, '', 'T', 1, 'C')
        self.ln(5)
        self.cell(0, 5, 'Contato: (11) 96305-4875', 0, 1, 'C')
        self.cell(0, 5, 'E-mail: cobranca-extrajudicial@recuperajur.adv.br', 0, 1, 'C')

# --- TÍTULO E UPLOAD ---
st.title("🏢 Gerador de Recibos de Honorários")
st.markdown("Sistema automatizado para geração de PDFs.")

# Barra lateral para uploads e configurações
with st.sidebar:
    st.header("📂 Arquivos")
    uploaded_excel = st.file_uploader("1. Carregar Excel de Condomínios", type=['xlsx'])
    uploaded_logo = st.file_uploader("2. Carregar Logótipo (Opcional)", type=['png', 'jpg', 'jpeg'])
    # --- NOVO UPLOAD PARA ASSINATURA ---
    uploaded_assinatura = st.file_uploader("3. Carregar Assinatura (Opcional)", type=['png', 'jpg', 'jpeg'])
    
    st.info("O sistema usará os arquivos carregados aqui para gerar o PDF.")

# --- CARREGAMENTO DE DADOS ---
BASE_DE_DADOS = {}
df = None

# Prioridade: Arquivo upado > Arquivo local
if uploaded_excel:
    df = pd.read_excel(uploaded_excel, dtype=str)
elif os.path.exists('Condominios_Unicos.xlsx'):
    df = pd.read_excel('Condominios_Unicos.xlsx', dtype=str)

if df is not None:
    df = df.fillna('-')
    for index, row in df.iterrows():
        chave = f"{row['ID']} - {row['Nome']}"
        endereco_completo = f"{row['Endereço']} - CEP: {row['CEP']}"
        BASE_DE_DADOS[chave] = {
            "nome": row['Nome'],
            "cnpj": row['CNPJ'],
            "endereco": endereco_completo
        }
    st.success(f"Base de dados carregada: {len(BASE_DE_DADOS)} condomínios.")
else:
    st.warning("⚠️ Nenhum arquivo Excel encontrado. Faça o upload na barra lateral.")

# Tratamento do Logo
logo_path_final = "LOGO.png" if os.path.exists("LOGO.png") else None
if uploaded_logo:
    with open("temp_logo.png", "wb") as f:
        f.write(uploaded_logo.getbuffer())
    logo_path_final = "temp_logo.png"

# --- TRATAMENTO DA ASSINATURA (NOVO) ---
assinatura_path_final = None
if uploaded_assinatura:
    with open("temp_assinatura.png", "wb") as f:
        f.write(uploaded_assinatura.getbuffer())
    assinatura_path_final = "temp_assinatura.png"
elif os.path.exists("ASSINATURA.png"):
     assinatura_path_final = "ASSINATURA.png"

# --- FORMULÁRIO ---
if BASE_DE_DADOS:
    col1, col2 = st.columns(2)
    with col1:
        escolha = st.selectbox("Selecione o Condomínio:", options=list(BASE_DE_DADOS.keys()))
    with col2:
        valor_input = st.number_input("Valor (R$):", min_value=0.0, step=100.0, format="%.2f")

    col3, col4 = st.columns(2)
    LISTA_MESES = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    ano_atual = datetime.now().year
    LISTA_ANOS = [str(ano) for ano in range(ano_atual-1, ano_atual+6)]
    
    with col3:
        mes_select = st.selectbox("Mês de Referência:", options=LISTA_MESES, index=datetime.now().month - 1)
    with col4:
        ano_select = st.selectbox("Ano:", options=LISTA_ANOS, index=1)

    # Botão de Geração
    if st.button("Gerar Recibo PDF", type="primary"):
        if valor_input <= 0:
            st.error("O valor deve ser maior que zero.")
        else:
            # Lógica de Geração
            condo = BASE_DE_DADOS[escolha]
            mes_ref = f"{mes_select}/{ano_select}"
            valor_ext = formatar_valor_extenso(valor_input)
            valor_form = f"{valor_input:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            pdf = PDF(logo_path=logo_path_final)
            pdf.add_page()
            pdf.set_margins(20, 20, 20)

            pdf.set_font("Arial", 'BU', 11)
            pdf.multi_cell(0, 8, txt="RECIBO DE REPASSE DE HONORÁRIOS ADVOCATICIOS\nCOBRANÇA EXTRAJUDICIAL DE INADIMPLÊNCIA", align='L')
            pdf.ln(10)

            pdf.set_font("Arial", size=11)
            texto_corpo = (
                f"CAIO.C.S.MOREIRA SOCIEDADE INDIVIDUAL DE ADVOCACIA, pessoa jurídica de direito privado, "
                f"com CNPJ sob nº 56.603.783/0001-52, com contrato social registrado na ORDEM DOS ADVOGADOS DO BRASIL, "
                f"subseção de São Paulo sob o nº 55501, DECLARA QUE RECEBEU do(a) {condo['nome']}, "
                f"pessoa jurídica de direito privado, inscrita no CNPJ sob nº {condo['cnpj']}, "
                f"com sede à {condo['endereco']}, o importe de R$ {valor_form} ({valor_ext}), "
                f"a título de repasse de honorários advocatícios, em decorrência da atividade prestada de "
                f"cobrança de inadimplência referentes ao(s) mês(es) de {mes_ref}, "
                f"originando o recebimento dos valores inseridos em cota associativa/condominial pelo Associação/Condomínio, "
                f"repassando os valores da atividade nesta data, dando a mais ampla geral e irrestrita quitação quanto aos valores que compõe a presente."
            )
            pdf.multi_cell(0, 7, txt=texto_corpo, align='J')
            
            # Data e Assinatura
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            pdf.ln(5)
            pdf.cell(0, 10, txt=f"São Paulo/SP, {data_hoje}.", ln=True, align='R')
            
            # --- ÁREA DA ASSINATURA MODIFICADA ---
            pdf.ln(10) # Espaço antes da assinatura

            if assinatura_path_final:
                # Insere a imagem da assinatura centralizada
                # x=85 é uma posição aproximada para centralizar numa folha A4
                # w=40 é a largura da assinatura (ajuste se ficar muito grande/pequena)
                current_y = pdf.get_y()
                pdf.image(assinatura_path_final, x=85, y=current_y, w=40)
                pdf.ln(15) # Move o cursor para baixo da imagem da assinatura
            else:
                 pdf.ln(25) # Espaço em branco se não tiver imagem

            # Desenha a linha
            pdf.cell(0, 5, txt="_" * 50, ln=True, align='C')
            
            # REMOVIDO: O texto com o nome da empresa que ficava aqui embaixo
            # ------------------------------------

            # Salva e Baixar
            id_condo = escolha.split('-')[0].strip()
            nome_arquivo = f"Recibo_{id_condo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_content = pdf.output(dest='S').encode('latin-1')
            st.success("✅ PDF Gerado com Sucesso!")
            st.download_button(
                label="📥 Baixar PDF Agora",
                data=pdf_content,
                file_name=nome_arquivo,
                mime="application/pdf"
            )
