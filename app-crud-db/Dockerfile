FROM python:3.10

# Cria e define o diretório de trabalho
ENV APP_HOME=/home/app/api/app-crud-db
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# 1. Copia APENAS o requirements.txt primeiro para dentro da pasta do container
COPY requirements.txt .

# 2. Instala as dependências (o Docker fará cache desta camada)
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 3. Copia o restante do código para o container
COPY . .

# 4. Instala o projeto em modo editável (necessário apenas se você tiver um setup.py ou pyproject.toml)
RUN pip install -e .

# Comando para iniciar o servidor
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000", "--reload"]