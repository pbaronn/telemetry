# Implementação, Instrumentação e Análise de Algoritmos de Ordenação

## Observabilidade com OpenTelemetry e Jaeger
Este projeto tem como objetivo implementar e comparar algoritmos de ordenação, analisando tempo de execução e métricas como comparações e trocas, utilizando OpenTelemetry para instrumentação e Jaeger para visualização dos traces.

---

### Tecnologias utilizadas
- Python
- OpenTelemetry
- Jaeger (Docker)

### Instalação das dependências:
    pip install opentelemetry-api opentelemetry-sdk
    pip install opentelemetry-exporter-otlp-proto-grpc

### Iniciar Jaeger com Docker:
    docker run -d --name jaeger \
      -e COLLECTOR_OTLP_ENABLED=true \
      -p 16686:16686 \
      -p 4317:4317 \
      jaegertracing/all-in-one:latest


### Acessar o Jaeger
Após iniciar o container, acesse o painel do Jaeger no navegador:

    Acesso do jaeger http://localhost:16686
