# Use uma imagem base leve do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Instale dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copie o arquivo de requisitos
COPY requirements.txt .

# Instale as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie os arquivos da aplicação
COPY . .

# Exponha a porta
EXPOSE 8000

# Comando para executar a aplicação
CMD ["python", "app.py"]