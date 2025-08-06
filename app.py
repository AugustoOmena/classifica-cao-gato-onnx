import os
import numpy as np
import onnxruntime as ort
from PIL import Image
import cv2
import streamlit as st

# --- Configuração Global do Modelo ---
MODEL_PATH = "meu_modelo_otimizado.onnx" 

DEFAULT_IMG_SIZE = (180, 180) 
class ONNXPredictor:
    def __init__(self, model_path):
        # Verifica se o arquivo do modelo existe
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        # Configura o provedor de execução para CPU.
        providers = ['CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Obtém o nome da entrada e saída do modelo ONNX.
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        # Tenta detectar o tamanho da imagem esperado pelo modelo a partir do input_shape.
        input_shape = self.session.get_inputs()[0].shape
        self.img_size = DEFAULT_IMG_SIZE

        if len(input_shape) >= 3:
            if input_shape[-1] == 3 or input_shape[-1] == 1:
                self.img_size = (input_shape[1], input_shape[2])
            elif input_shape[1] == 3 or input_shape[1] == 1:
                self.img_size = (input_shape[2], input_shape[3])
            else:
                self.img_size = DEFAULT_IMG_SIZE
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocessa a imagem para o formato esperado pelo modelo ONNX.
        Isso inclui redimensionamento, conversão para array NumPy, tratamento de canais
        e normalização.
        """
        # Redimensiona a imagem para o tamanho esperado pelo modelo
        image = image.resize(self.img_size)
        
        # Converte a imagem PIL para um array NumPy
        img_array = np.array(image)
        
        # Garante que a imagem tenha 3 canais (RGB).
        # Se for RGBA (com canal alfa), remove o alfa.
        # Se for Grayscale (2D), converte para 3 canais replicando.
        if img_array.shape[-1] == 4: # RGBA para RGB
            img_array = img_array[:, :, :3]
        elif len(img_array.shape) == 2: # Grayscale para RGB
            img_array = np.stack([img_array] * 3, axis=-1)
        
        # Normaliza os valores dos pixels para o intervalo [0, 1]
        img_array = img_array.astype(np.float32)
        
        input_shape = self.session.get_inputs()[0].shape
        if len(input_shape) == 4 and input_shape[1] == 3:
            img_array = np.transpose(img_array, (2, 0, 1))
        
        img_array = np.expand_dims(img_array, axis=0)
        
        st.sidebar.write(f"Shape da imagem preprocessada: {img_array.shape}")
        
        return img_array
    
    def predict(self, image: Image.Image) -> tuple[str, float, dict]:
        """
        Faz a predição na imagem usando o modelo ONNX.
        Retorna a classe predita, a confiança e as probabilidades para cada classe.
        """
        # Pré-processa a imagem
        input_data = self.preprocess_image(image)
        
        # Realiza a inferência com o modelo ONNX
        outputs = self.session.run([self.output_name], {self.input_name: input_data})
        
        # O output_logit_array é o logit bruto do modelo.
        output_logit_array = outputs[0][0]
    
        
        # Função Sigmoid para converter logit em probabilidade (para classificação binária)
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))
        
        # Exemplo: Se output_logit_array é um único valor (logit para Cão)
        if output_logit_array.size == 1:
            logit_cao = output_logit_array.item()
            prob_cao = sigmoid(logit_cao)
            prob_gato = 1 - prob_cao
        else: 
            exp_scores = np.exp(output_logit_array - np.max(output_logit_array))
            probabilities = exp_scores / np.sum(exp_scores)
            prob_gato = probabilities[0] if probabilities.size > 0 else 0.5
            prob_cao = probabilities[1] if probabilities.size > 1 else 0.5
            pass 

        # Lógica para determinar a predição final e confiança
        if prob_gato > prob_cao:
            prediction = "Gato"
            confidence = prob_gato
        else:
            prediction = "Cão"
            confidence = prob_cao
        
        return prediction, float(confidence), {'cat': float(prob_gato), 'dog': float(prob_cao)}

# --- Inicialização do Modelo (com cache para performance no Streamlit) ---
@st.cache_resource
def load_predictor(model_path):
    try:
        return ONNXPredictor(model_path)
    except FileNotFoundError as e:
        st.error(f"ERRO: {e}")
        st.warning("Certifique-se de que o arquivo 'meu_modelo_otimizado.onnx' está na pasta do projeto!")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o modelo ONNX: {e}")
        st.warning("Verifique se o modelo está no formato ONNX correto e se as dependências estão instaladas.")
        return None

predictor = load_predictor(MODEL_PATH)

# --- Interface do Usuário Streamlit ---
st.set_page_config(
    page_title="Classificador de Cães e Gatos",
    page_icon="🐾",
    layout="centered"
)

st.title("🐱🐶 Classificador de Cães e Gatos")
st.write("Faça o upload de uma imagem para descobrir se é um cão ou um gato!")

# Verifica se o modelo foi carregado com sucesso antes de permitir uploads
if predictor:
    uploaded_file = st.file_uploader(
        "Escolha uma imagem...",
        type=["jpg", "jpeg", "png", "webp"],
        help="Arraste e solte ou clique para selecionar uma imagem (JPG, JPEG, PNG, WEBP)."
    )

    if uploaded_file is not None:
        # Exibe a imagem carregada
        image = Image.open(uploaded_file)
        st.image(image, caption='Imagem Carregada', use_column_width=True)
        st.write("") # Espaço em branco

        # Botão para classificar a imagem
        if st.button("Classificar Imagem"):
            with st.spinner("Classificando..."):
                try:
                    # Chama o método de predição do seu modelo
                    prediction, confidence, probabilities = predictor.predict(image)

                    # Exibe os resultados
                    st.subheader("Resultado da Classificação:")
                    
                    if prediction == "Gato":
                        st.success(f"É um **Gato**! 😻")
                        st.metric(label="Confiança", value=f"{confidence*100:.1f}%")
                    else:
                        st.info(f"É um **Cão**! 🐕")
                        st.metric(label="Confiança", value=f"{confidence*100:.1f}%")
                    
                    st.write("---")
                    st.subheader("Probabilidades Detalhadas:")
                    st.write(f"**Gato:** {probabilities['cat']*100:.1f}%")
                    st.write(f"**Cão:** {probabilities['dog']*100:.1f}%")

                except Exception as e:
                    st.error(f"Erro ao processar a imagem ou fazer a predição: {e}")
                    st.warning("Verifique se a imagem é válida e se o modelo está funcionando corretamente.")
else:
    st.error("O aplicativo não pode funcionar porque o modelo não foi carregado. Verifique os logs acima.")

st.sidebar.markdown("---")
st.sidebar.header("Sobre este App")
st.sidebar.info(
    "Este aplicativo utiliza um modelo de Deep Learning no formato ONNX "
    "para classificar imagens como 'Cão' ou 'Gato'. "
    "Desenvolvido com Streamlit para uma interface interativa."
)
st.sidebar.markdown("---")
st.sidebar.write("Feito com ❤️ para Engenharia de Dados")

