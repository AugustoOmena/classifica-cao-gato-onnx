import os
import numpy as np
import onnxruntime as ort
from PIL import Image
import cv2
from flask import Flask, request, jsonify, render_template_string
import io
import base64

app = Flask(__name__)

# Configuração global do modelo
MODEL_PATH = "meu_modelo_otimizado.onnx"
IMG_SIZE = (180, 180)  # Tamanho esperado pelo seu modelo específico

class ONNXPredictor:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        # Configurar para usar CPU (compatível com M2)
        providers = ['CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Obter informações do modelo
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        # Detectar automaticamente o tamanho esperado da imagem
        input_shape = self.session.get_inputs()[0].shape
        if len(input_shape) >= 3:
            # Formato típico: [batch, height, width, channels] ou [batch, channels, height, width]
            if input_shape[1] == input_shape[2]:  # height == width (imagem quadrada)
                self.img_size = (input_shape[1], input_shape[2])
            elif input_shape[2] == input_shape[3]:  # formato [batch, channels, height, width]
                self.img_size = (input_shape[2], input_shape[3])
            else:
                self.img_size = IMG_SIZE  # usar padrão como fallback
        else:
            self.img_size = IMG_SIZE
        
        print(f"Modelo carregado com sucesso!")
        print(f"Input shape: {input_shape}")
        print(f"Tamanho da imagem detectado: {self.img_size}")
        print(f"Output shape: {self.session.get_outputs()[0].shape}")
        print(f"Input name: {self.input_name}")
        print(f"Output name: {self.output_name}")
    
    def preprocess_image(self, image):
        """Preprocessa a imagem para o formato esperado pelo modelo"""
        # Redimensionar para o tamanho detectado do modelo
        image = image.resize(self.img_size)
        
        # Converter para array numpy
        img_array = np.array(image)
        
        # Se a imagem for RGB, manter; se for RGBA, converter para RGB
        if img_array.shape[-1] == 4:
            img_array = img_array[:, :, :3]
        elif len(img_array.shape) == 2:  # Grayscale
            img_array = np.stack([img_array] * 3, axis=-1)
        
        # Normalizar para [0, 1]
        img_array = img_array.astype(np.float32)
        
        # Adicionar dimensão do batch
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"Shape da imagem preprocessada: {img_array.shape}")
        
        return img_array
    
    def predict(self, image):
        """Faz a predição na imagem"""
        # Preprocessar a imagem
        input_data = self.preprocess_image(image)
        
        # Fazer a inferência
        outputs = self.session.run([self.output_name], {self.input_name: input_data})
        
        # Obter probabilidades
        probabilities = outputs[0][0]
        
        # Aplicar softmax se necessário
        if len(probabilities) > 1:
            exp_scores = np.exp(probabilities - np.max(probabilities))
            probabilities = exp_scores / np.sum(exp_scores)
        
        return probabilities

# Inicializar o modelo
try:
    predictor = ONNXPredictor(MODEL_PATH)
except FileNotFoundError as e:
    print(f"ERRO: {e}")
    print("Certifique-se de que o arquivo 'meu_modelo_otimizado.onnx' está na pasta do projeto!")
    predictor = None

# Template HTML simples para upload
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Classificador de Cães e Gatos</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .result { margin: 20px 0; padding: 20px; border-radius: 5px; }
        .cat { background-color: #e8f5e8; }
        .dog { background-color: #e8e8f5; }
        img { max-width: 300px; max-height: 300px; }
        .progress { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🐱🐶 Classificador de Cães e Gatos</h1>
    
    <div class="upload-area">
        <input type="file" id="imageInput" accept="image/*" style="display: none;">
        <button onclick="document.getElementById('imageInput').click()">Selecionar Imagem</button>
        <p>ou arraste uma imagem aqui</p>
    </div>
    
    <div id="preview"></div>
    <div id="result"></div>
    
    <script>
        const imageInput = document.getElementById('imageInput');
        const preview = document.getElementById('preview');
        const result = document.getElementById('result');
        
        imageInput.addEventListener('change', handleImage);
        
        // Drag and drop
        document.addEventListener('dragover', e => e.preventDefault());
        document.addEventListener('drop', handleDrop);
        
        function handleDrop(e) {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                processFile(files[0]);
            }
        }
        
        function handleImage(e) {
            const file = e.target.files[0];
            if (file) {
                processFile(file);
            }
        }
        
        function processFile(file) {
            if (!file.type.startsWith('image/')) {
                alert('Por favor, selecione uma imagem válida');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                classifyImage(file);
            };
            reader.readAsDataURL(file);
        }
        
        function classifyImage(file) {
            const formData = new FormData();
            formData.append('image', file);
            
            result.innerHTML = '<div class="progress">Classificando...</div>';
            
            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    result.innerHTML = `<div style="color: red;">Erro: ${data.error}</div>`;
                } else {
                    const prediction = data.prediction;
                    const confidence = (data.confidence * 100).toFixed(1);
                    const className = prediction === 'Gato' ? 'cat' : 'dog';
                    
                    result.innerHTML = `
                        <div class="result ${className}">
                            <h3>Resultado: ${prediction}</h3>
                            <p>Confiança: ${confidence}%</p>
                            <p>Probabilidades:</p>
                            <ul>
                                <li>Gato: ${(data.probabilities.cat * 100).toFixed(1)}%</li>
                                <li>Cão: ${(data.probabilities.dog * 100).toFixed(1)}%</li>
                            </ul>
                        </div>
                    `;
                }
            })
            .catch(error => {
                result.innerHTML = `<div style="color: red;">Erro na comunicação: ${error}</div>`;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def sigmoid(x):
  """Calcula a função sigmoide para converter um logit em probabilidade."""
  return 1 / (1 + np.exp(-x))

@app.route('/predict', methods=['POST'])
def predict():
    if predictor is None:
        return jsonify({'error': 'Modelo não carregado'}), 500
    
    if 'image' not in request.files:
        return jsonify({'error': 'Nenhuma imagem enviada'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        # Carregar a imagem
        image = Image.open(file.stream)
        
        # O método 'predictor.predict' retorna o logit bruto do modelo
        output_logit_array = predictor.predict(image)
        
        # 1. Extrair o valor do logit
        # CORREÇÃO: A saída do modelo corresponde à classe "Cão"
        logit_cao = output_logit_array[0]
        
        # 2. Aplicar a função Sigmoid para obter a probabilidade real
        prob_cao = sigmoid(logit_cao)
        
        # 3. Calcular a probabilidade do outro animal
        prob_gato = 1 - prob_cao
        
        # 4. Determinar a classe predita e a confiança (esta lógica agora funciona corretamente)
        if prob_gato > prob_cao:
            prediction = "Gato"
            confidence = prob_gato
        else:
            prediction = "Cão"
            confidence = prob_cao
        
        # 5. Retornar o JSON com valores corretos
        return jsonify({
            'prediction': prediction,
            'confidence': float(confidence),
            'probabilities': {
                'cat': float(prob_gato),
                'dog': float(prob_cao)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar imagem: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model_loaded': predictor is not None})

if __name__ == '__main__':
    print("🚀 Iniciando servidor...")
    print("📱 Acesse: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health")
    
    app.run(host='0.0.0.0', port=8000, debug=True)