#!/bin/bash

echo "🐱🐶 Configurando Classificador de Cães e Gatos com ONNX"
echo "========================================================="

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado!"
    echo "📦 Instale o Docker Desktop em: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar se o Docker está rodando
if ! docker info &> /dev/null; then
    echo "❌ Docker não está rodando!"
    echo "🚀 Inicie o Docker Desktop e tente novamente"
    exit 1
fi

# Verificar se o modelo existe
if [ ! -f "meu_modelo_otimizado.onnx" ]; then
    echo "❌ Arquivo 'meu_modelo_otimizado.onnx' não encontrado!"
    echo "📂 Certifique-se de que o arquivo do modelo está na pasta atual"
    exit 1
fi

echo "✅ Docker encontrado e rodando"
echo "✅ Modelo ONNX encontrado"

# Criar pasta para imagens de teste (opcional)
mkdir -p test_images

echo "🔨 Construindo imagem Docker..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Imagem construída com sucesso!"
    echo ""
    echo "🚀 Para iniciar o serviço, execute:"
    echo "   docker-compose up"
    echo ""
    echo "📱 Depois acesse: http://localhost:8000"
    echo ""
    echo "🛑 Para parar: docker-compose down"
    echo ""
    echo "📊 Para monitorar: docker-compose logs -f"
else
    echo "❌ Erro ao construir a imagem Docker"
    exit 1
fi