from src.threat_intel.mitre import (
    determinar_padrao_por_correlacao,
    enriquecer_com_mitre,
    limpar_texto_mitre,
)


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.executed_params = None

    def execute(self, query, params):
        self.executed_params = params
        return FakeResult(self.row)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeEngine:
    def __init__(self, row=None, erro=None):
        self.row = row
        self.erro = erro
        self.connection = None

    def connect(self):
        if self.erro:
            raise self.erro

        self.connection = FakeConnection(self.row)
        return self.connection


def test_correlacao_falhas_login_retorna_t1110():
    termo, criterio = determinar_padrao_por_correlacao({"falhas_login_recentes": 3})

    assert termo == "%T1110%"
    assert "falhas de login" in criterio


def test_correlacao_dispositivo_novo_e_limite_retorna_t1098():
    termo, criterio = determinar_padrao_por_correlacao(
        {
            "dispositivo_novo_flag": True,
            "alteracao_limite_flag": True,
        }
    )

    assert termo == "%T1098%"
    assert "tomada de conta" in criterio


def test_correlacao_mudanca_localizacao_retorna_t1078():
    termo, criterio = determinar_padrao_por_correlacao(
        {"mudanca_localizacao_flag": True}
    )

    assert termo == "%T1078%"
    assert "localização" in criterio


def test_correlacao_sem_sinais_retorna_none():
    termo, criterio = determinar_padrao_por_correlacao({})

    assert termo is None
    assert criterio is None


def test_limpar_texto_mitre_remove_markdown_e_citacao():
    texto = "[Mitigação](https://example.com) (Citation: exemplo) aplicar MFA."

    resultado = limpar_texto_mitre(texto)

    assert "https://example.com" not in resultado
    assert "Citation:" not in resultado
    assert "Mitigação" in resultado
    assert "aplicar MFA." in resultado


def test_limpar_texto_mitre_escapa_html():
    resultado = limpar_texto_mitre("<script>alert(1)</script>")

    assert "<script>" not in resultado
    assert "&lt;script&gt;" in resultado


def test_limpar_texto_mitre_retorna_fallback_para_texto_vazio():
    assert limpar_texto_mitre(None) == "Nenhum procedimento de mitigação listado."


def test_enriquecimento_retorna_dados_do_banco():
    engine = FakeEngine(
        row=(
            "T1110",
            "Brute Force",
            "Credential Access",
            "Aplicar MFA.",
        )
    )

    resultado = enriquecer_com_mitre(
        engine=engine,
        tipo_evento="Pix",
        sinais={"falhas_login_recentes": 3},
    )

    assert resultado["mitre_id"] == "T1110"
    assert resultado["tecnica"] == "Brute Force"
    assert resultado["tatica"] == "Credential Access"
    assert resultado["procedimentos"] == "Aplicar MFA."
    assert resultado["fonte"] == "banco de dados (dinâmico)"
    assert "falhas de login" in resultado["criterio"]

    assert engine.connection.executed_params["termo"] == "%T1110%"


def test_enriquecimento_pix_usa_fallback_quando_banco_nao_retorna_resultado():
    engine = FakeEngine(row=None)

    resultado = enriquecer_com_mitre(
        engine=engine,
        tipo_evento="Pix",
        sinais={},
    )

    assert resultado["mitre_id"] == "T1565.001"
    assert resultado["fonte"] == "fallback local"
    assert "tipo de transação" in resultado["criterio"]


def test_enriquecimento_generico_usa_fallback_t1110():
    engine = FakeEngine(row=None)

    resultado = enriquecer_com_mitre(
        engine=engine,
        tipo_evento="Outro",
        sinais={},
    )

    assert resultado["mitre_id"] == "T1110.001"
    assert resultado["fonte"] == "fallback local"


def test_falha_do_banco_usa_fallback_sem_quebrar(capsys):
    engine = FakeEngine(erro=RuntimeError("banco indisponível"))

    resultado = enriquecer_com_mitre(
        engine=engine,
        tipo_evento="Pix",
        sinais={},
    )

    saida = capsys.readouterr()

    assert resultado["mitre_id"] == "T1565.001"
    assert resultado["fonte"] == "fallback local"
    assert "banco indisponível" in saida.out


def test_limpar_texto_mitre_trunca_texto_longo():
    texto = "palavra " * 100

    resultado = limpar_texto_mitre(texto)

    assert len(resultado) <= 451
    assert resultado.endswith("…")


def test_enriquecimento_transferencia_busca_t1043():
    engine = FakeEngine(row=None)

    resultado = enriquecer_com_mitre(
        engine=engine,
        tipo_evento="Transferência",
        sinais={},
    )

    assert engine.connection.executed_params["termo"] == "%T1043%"
    assert resultado["fonte"] == "fallback local"
