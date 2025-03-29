import streamlit as st
import pandas as pd
from openai import OpenAI
from datetime import datetime

# Configurações iniciais
st.set_page_config(
    page_title="Alves Advocacia",
    page_icon="⚖️",
    layout="wide"
)

# Carregar CSS customizado
with open(".streamlit/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Função de autenticação
def verificar_autenticacao():
    if not st.session_state.get("autenticado"):
        with st.sidebar:
            st.title("🔒 Acesso Restrito")
            senha = st.text_input("Senha de Acesso", type="password")
            
            if senha == st.secrets.get("SENHA_ADMIN"):
                st.session_state.autenticado = True
                st.rerun()
            elif senha:
                st.error("Senha incorreta. Tente novamente.")
        st.stop()

# Inicializar cliente OpenAI
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except KeyError:
    st.error("Erro de configuração: Chave da OpenAI não encontrada no secrets.toml")
    st.stop()

# Carregar dados do CRM
@st.cache_data
def load_crm_data():
    try:
        return pd.read_csv("data/clientes.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["id", "nome", "cpf", "email", "telefone", "data_cadastro", "status"])

# Função de consulta à OpenAI
def consultar_ia(prompt):
    contexto = """
    Você é um assistente virtual de um escritório de advocacia brasileiro. 
    Responda de forma clara e técnica, citando artigos de lei quando relevante.
    Se a pergunta for complexa ou específica, recomende a consulta com um advogado humano.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro na consulta: {str(e)}"

# Interface principal
def main():
    verificar_autenticacao()
    st.title("Alves Advocacia ⚖️")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu Principal",
        ["Atendimento", "Agendamento", "Clientes", "Documentos"]
    )

    # Módulo de Atendimento - Chatbot
    if menu == "Atendimento":
        st.header("Chatbot Jurídico")
        
        # Inicializar histórico do chat
        if "mensagens" not in st.session_state:
            st.session_state.mensagens = []
        
        # Exibir histórico de mensagens
        for mensagem in st.session_state.mensagens:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])
            
            if mensagem.get("alerta"):
                st.error(mensagem["alerta"])
        
        # Input de mensagem com enter
        prompt = st.chat_input("Digite sua dúvida jurídica...")
        
        if prompt:
            # Adicionar mensagem do usuário
            st.session_state.mensagens.append({"role": "user", "content": prompt})
            
            # Obter resposta da IA
            resposta = consultar_ia(prompt)
            
            # Adicionar resposta ao histórico
            st.session_state.mensagens.append({
                "role": "assistant", 
                "content": resposta,
                "alerta": "Caso complexo detectado! Transferindo para um profissional..." 
                    if "consulte um advogado" in resposta.lower() else None
            })
            
            # Rerun para atualizar a tela
            st.rerun()

    # Módulo de Agendamento
    elif menu == "Agendamento":
        st.header("Agendamento de Reuniões")
        
        with st.form("agendamento_form"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data da Reunião", min_value=datetime.today())
            with col2:
                horario = st.time_input("Horário")
            
            assunto = st.text_input("Assunto da Reunião")
            if st.form_submit_button("Confirmar Agendamento"):
                st.success(f"Reunião agendada para {data.strftime('%d/%m/%Y')} às {horario.strftime('%H:%M')}")

    # Módulo de Clientes
    elif menu == "Clientes":
        st.header("Gestão de Clientes")
        
        df = load_crm_data()
        st.dataframe(df, use_container_width=True)
        
        with st.expander("Adicionar Novo Cliente"):
            with st.form("novo_cliente_form"):
                nome = st.text_input("Nome Completo")
                cpf = st.text_input("CPF")
                email = st.text_input("E-mail")
                telefone = st.text_input("Telefone")
                
                if st.form_submit_button("Salvar Cliente"):
                    novo_cliente = pd.DataFrame([{
                        "id": len(df) + 1,
                        "nome": nome,
                        "cpf": cpf,
                        "email": email,
                        "telefone": telefone,
                        "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
                        "status": "Ativo"
                    }])
                    
                    df = pd.concat([df, novo_cliente], ignore_index=True)
                    df.to_csv("data/clientes.csv", index=False)
                    st.success("Cliente cadastrado com sucesso!")

    # Módulo de Documentos
    elif menu == "Documentos":
        st.header("Geração de Documentos")
        
        tipo_documento = st.selectbox(
            "Selecione o Tipo de Documento",
            ["Contrato", "Petição Inicial", "Procuração"]
        )
        
        if tipo_documento:
            st.info("Funcionalidade em desenvolvimento. Em breve disponível!")

if __name__ == "__main__":
    main()