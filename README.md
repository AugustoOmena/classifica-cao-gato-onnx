# 🐱🐶 Classificador de Cães e Gatos com ONNX

<img width="1538" height="1338" alt="image" src="https://github.com/user-attachments/assets/a58197cd-fc77-44f6-bc05-32efc0e45ae2" />


## 📋 Pré-requisitos

- **Docker Desktop** instalado e rodando
- **Um editor de código**

## 🚀 Setup Rápido

### 1. Organizar os arquivos

Crie uma pasta para o projeto e organize assim:

```
meu-projeto/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app.py
├── setup.sh
├── meu_modelo_otimizado.onnx
├── .vscode/
│   └── settings.json
└── test_images/  (opcional)
```

### 2. Executar o setup

```bash
# Dar permissão de execução ao script
chmod +x setup.sh

# Executar o setup
./setup.sh
```

### 3. Iniciar o serviço

```bash
# Iniciar em modo normal
docker-compose up

# Ou em modo detached (background)
docker-compose up -d
```

### 4. Acessar a aplicação

- **Interface web**: http://localhost:8000
- **Health check**: http://localhost:8000/health

## 🛠️ Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f

# Parar o serviço
docker-compose down

# Reconstruir a imagem
docker-compose build --no-cache

# Entrar no container
docker-compose exec onnx-classifier /bin/bash

# Ver status dos containers
docker-compose ps
```

## 📱 Como Usar

1. Acesse http://localhost:8000
2. Clique em "Selecionar Imagem" ou arraste uma foto
3. Aguarde a classificação
4. Veja o resultado com probabilidades

## 🔧 Personalização

### Alterar porta

No `docker-compose.yml`, mude:

```yaml
ports:
  - "8080:8000" # Agora será localhost:8080
```

### Ajustar memória

Para sistemas com menos RAM:

```yaml
deploy:
  resources:
    limits:
      memory: 1G # Reduzir de 2G para 1G
```

### Modificar tamanho da imagem

No `app.py`, altere:

```python
IMG_SIZE = (150, 150)  # Ao invés de (224, 224)
```

## 📊 Monitoramento

### Ver uso de recursos

```bash
# Uso de memória e CPU
docker stats

# Logs específicos
docker-compose logs onnx-classifier
```

## 🔄 Atualização do Modelo

Para trocar o modelo:

1. Pare o serviço: `docker-compose down`
2. Substitua o arquivo `meu_modelo_otimizado.onnx`
3. Reconstrua a imagem: `docker-compose build`
4. Reinicie: `docker-compose up`

**Importante**: O código agora detecta automaticamente o tamanho esperado da imagem pelo modelo!

## 📚 Estrutura do Código

- **Dockerfile**: Configuração do container
- **app.py**: Aplicação Flask com interface web
- **requirements.txt**: Dependências Python
- **docker-compose.yml**: Orquestração dos serviços

## ⚡ Otimizado para processadores ARM

- Usa `CPUExecutionProvider` (compatível com ARM)
- Imagem base `python:3.9-slim` (menor uso de memória)
- Limites de memória configurados
- Cache de dependências otimizado

## 🎯 API Endpoints

### POST /predict

Enviar imagem para classificação:

```bash
curl -X POST -F "image=@minha_foto.jpg" http://localhost:8000/predict
```

Resposta:

```json
{
  "prediction": "Gato",
  "confidence": 0.95,
  "probabilities": {
    "cat": 0.95,
    "dog": 0.05
  }
}
```

### GET /health

Verificar status:

```bash
curl http://localhost:8000/health
```

