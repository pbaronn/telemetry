import random
import time
import copy
import json
import logging
import os

# CONFIGURAÇÃO DO OPENTELEMETRY

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_DISPONIVEL = True
except ImportError:
    OTLP_DISPONIVEL = False

resource = Resource.create({
    "service.name": "sorting-algorithms",
    "service.version": "1.0.0",
    "student.name": "Pamela Baron",
    "discipline": "Algoritmos e Estruturas de Dados",
})

provider = TracerProvider(resource=resource)

# Tenta conectar ao Jaeger. 
if OTLP_DISPONIVEL:
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",
            insecure=True
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        print("[OTel] Conectado ao Jaeger em http://localhost:4317")
        print("[OTel] Visualize os traces em http://localhost:16686")
    except Exception as e:
        print(f"[OTel] Jaeger indisponível ({e}). Usando saída no console.")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
else:
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    print("[OTel] Exportador OTLP não instalado. Usando saída no console.")

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("sorting.tracer")


# CONFIGURAÇÃO DE LOGGING 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sorting_execution.log", mode="w", encoding="utf-8")
    ]
)
log = logging.getLogger("sorting")


# GERAÇÃO E GRAVAÇÃO DOS DADOS

ARQUIVO_DADOS = "dados_entrada.json"
TAMANHOS = [1000, 5000, 10000, 50000]
SEED = 42  # Semente fixa para reprodutibilidade


def gerar_e_salvar_dados():
    random.seed(SEED)
    dados = {}
    for tamanho in TAMANHOS:
        dados[str(tamanho)] = [random.randint(1, tamanho * 10) for _ in range(tamanho)]

    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f)

    log.info(f"Dados gerados e salvos em '{ARQUIVO_DADOS}' | Seed={SEED} | Tamanhos={TAMANHOS}")
    print(f"\n[Dados] Arquivo '{ARQUIVO_DADOS}' criado com {len(TAMANHOS)} conjuntos.\n")


def carregar_dados(tamanho: int) -> list:
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        todos = json.load(f)
    return todos[str(tamanho)][:]  # Cópia independente



#IMPLEMENTAÇÃO DOS ALGORITMOS

def bubble_sort(arr: list) -> tuple:
    lista = copy.deepcopy(arr)
    n = len(lista)
    comparacoes = 0
    trocas = 0

    for i in range(n):
        trocou = False
        for j in range(0, n - i - 1):
            comparacoes += 1
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
                trocas += 1
                trocou = True
        if not trocou:
            break

    return lista, comparacoes, trocas


def insertion_sort(arr: list) -> tuple:
 
    lista = copy.deepcopy(arr)
    comparacoes = 0
    trocas = 0

    for i in range(1, len(lista)):
        chave = lista[i]
        j = i - 1
        while j >= 0 and lista[j] > chave:
            comparacoes += 1
            lista[j + 1] = lista[j]
            trocas += 1
            j -= 1
        comparacoes += 1  
        lista[j + 1] = chave

    return lista, comparacoes, trocas


# Variáveis globais para contagem no Merge Sort
_merge_comparacoes = 0
_merge_trocas = 0


def merge_sort(arr: list) -> tuple:
    global _merge_comparacoes, _merge_trocas
    _merge_comparacoes = 0
    _merge_trocas = 0

    lista = copy.deepcopy(arr)
    _merge_sort_rec(lista)
    return lista, _merge_comparacoes, _merge_trocas


def _merge_sort_rec(lista: list) -> list:
    global _merge_comparacoes, _merge_trocas

    if len(lista) <= 1:
        return lista

    meio = len(lista) // 2
    esq = _merge_sort_rec(lista[:meio])
    dir_ = _merge_sort_rec(lista[meio:])

    i = j = k = 0
    while i < len(esq) and j < len(dir_):
        _merge_comparacoes += 1
        if esq[i] <= dir_[j]:
            lista[k] = esq[i]
            i += 1
        else:
            lista[k] = dir_[j]
            j += 1
            _merge_trocas += 1
        k += 1

    while i < len(esq):
        lista[k] = esq[i]; i += 1; k += 1
    while j < len(dir_):
        lista[k] = dir_[j]; j += 1; k += 1

    return lista



#  EXECUÇÃO INSTRUMENTADA COM OpenTelemetry


def executar_instrumentado(nome: str, funcao, dados: list) -> dict:
  
    log.info(f"[INÍCIO] Algoritmo={nome} | n={len(dados)}")

    with tracer.start_as_current_span(f"sort.{nome.lower().replace(' ', '_')}") as span:
        span.set_attribute("sort.algorithm", nome)
        span.set_attribute("sort.input_size", len(dados))

        inicio = time.perf_counter()

        try:
            resultado, comparacoes, trocas = funcao(dados)
            duracao = time.perf_counter() - inicio

            span.set_attribute("sort.duration_ms", round(duracao * 1000, 4))
            span.set_attribute("sort.comparisons", comparacoes)
            span.set_attribute("sort.swaps", trocas)
            span.set_attribute("sort.status", "success")

            log.info(
                f"[FIM] Algoritmo={nome} | n={len(dados)} | "
                f"tempo={duracao*1000:.2f}ms | comparações={comparacoes} | trocas={trocas}"
            )

        except Exception as e:
            duracao = time.perf_counter() - inicio
            span.set_attribute("sort.status", "error")
            span.set_attribute("sort.error", str(e))
            log.error(f"[ERRO] Algoritmo={nome} | n={len(dados)} | erro={e}")
            raise

    return {
        "algoritmo": nome,
        "n": len(dados),
        "tempo_ms": round(duracao * 1000, 4),
        "comparacoes": comparacoes,
        "trocas": trocas,
    }


# LOOP PRINCIPAL

ALGORITMOS = {
    "Bubble Sort":    bubble_sort,
    "Insertion Sort": insertion_sort,
    "Merge Sort":     merge_sort,
}

LIMITE_N2 = 10000


def main():
    print("=" * 65)
    print("  N1 — Algoritmos de Ordenação com OpenTelemetry + Jaeger")
    print("  Aluna: Pâmela Baron")
    print("=" * 65)

    gerar_e_salvar_dados()

    resultados = []

    for tamanho in TAMANHOS:
        print(f"\n{'─'*65}")
        print(f"  Tamanho de entrada: n = {tamanho:,}")
        print(f"{'─'*65}")
        print(f"  {'Algoritmo':<20} {'Tempo (ms)':>12} {'Comparações':>14} {'Trocas':>10}")
        print(f"  {'─'*20} {'─'*12} {'─'*14} {'─'*10}")

        for nome, funcao in ALGORITMOS.items():
        
            complexidade = "O(n²)" if nome != "Merge Sort" else "O(n log n)"
            if complexidade == "O(n²)" and tamanho > LIMITE_N2:
                print(f"  {nome:<20} {'(pulado — n muito grande)':>38}")
                log.warning(f"[PULADO] {nome} | n={tamanho} excede limite de {LIMITE_N2} para O(n²)")
                continue

    
            dados = carregar_dados(tamanho)

            resultado = executar_instrumentado(nome, funcao, dados)
            resultados.append(resultado)

            print(
                f"  {nome:<20} {resultado['tempo_ms']:>10.2f}ms "
                f"{resultado['comparacoes']:>14,} {resultado['trocas']:>10,}"
            )

    # Salva resultados em JSON para uso no relatório
    with open("resultados_experimento.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*65}")
    print(f"  Experimento concluído. Resultados salvos em 'resultados_experimento.json'")
    print(f"  Log completo em 'sorting_execution.log'")
    if OTLP_DISPONIVEL:
        print(f"  Traces disponíveis em http://localhost:16686 (serviço: sorting-algorithms)")
    print(f"{'='*65}\n")

    provider.shutdown()


if __name__ == "__main__":
    main()