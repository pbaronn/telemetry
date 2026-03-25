Instalação das dependências:
    pip install opentelemetry-api opentelemetry-sdk
    pip install opentelemetry-exporter-otlp-proto-grpc

Iniciar Jaeger com Docker:
    docker run -d --name jaeger \
      -e COLLECTOR_OTLP_ENABLED=true \
      -p 16686:16686 \
      -p 4317:4317 \
      jaegertracing/all-in-one:latest

Acesso do jaeger http://localhost:16686