from src import ingest_mitre


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"objects": []}

    def json(self):
        return self._payload


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.closed = False

    def execute(self, query):
        self.queries.append(query)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.commits = 0
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def criar_stix_sintetico():
    return {
        "objects": [
            {
                "type": "x-mitre-tactic",
                "x_mitre_shortname": "credential-access",
                "name": "Credential Access",
            },
            {
                "type": "relationship",
                "relationship_type": "uses",
                "target_ref": "attack-pattern--123",
                "description": "Procedimento real de teste.",
            },
            {
                "type": "attack-pattern",
                "id": "attack-pattern--123",
                "name": "Brute Force",
                "description": "Descrição da técnica.",
                "x_mitre_is_subtechnique": False,
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": "T1110",
                    }
                ],
                "kill_chain_phases": [
                    {
                        "phase_name": "credential-access",
                    }
                ],
            },
        ]
    }


def test_processar_dados_mitre_retorna_tecnica_estruturada():
    resultado = ingest_mitre.processar_dados_mitre(criar_stix_sintetico())

    assert len(resultado) == 1

    registro = resultado[0]

    assert registro[0] == "T1110"
    assert registro[1] == "Brute Force"
    assert registro[2] == "Credential Access"
    assert "Descrição da técnica" in registro[3]
    assert "Procedimento real de teste" in registro[4]


def test_processar_dados_mitre_ignora_subtecnicas():
    dados = criar_stix_sintetico()

    dados["objects"][2]["x_mitre_is_subtechnique"] = True

    resultado = ingest_mitre.processar_dados_mitre(dados)

    assert resultado == []


def test_processar_dados_mitre_ignora_tecnica_sem_id_externo():
    dados = criar_stix_sintetico()

    dados["objects"][2]["external_references"] = []

    resultado = ingest_mitre.processar_dados_mitre(dados)

    assert resultado == []


def test_processar_dados_mitre_usa_fallback_de_procedimento():
    dados = criar_stix_sintetico()

    dados["objects"] = [
        objeto for objeto in dados["objects"] if objeto.get("type") != "relationship"
    ]

    resultado = ingest_mitre.processar_dados_mitre(dados)

    assert len(resultado) == 1
    assert "Nenhum exemplo prático documentado" in resultado[0][4]


def test_processar_dados_mitre_usa_nome_da_fase_quando_tatica_desconhecida():
    dados = criar_stix_sintetico()

    dados["objects"][2]["kill_chain_phases"] = [
        {
            "phase_name": "fase-desconhecida",
        }
    ]

    resultado = ingest_mitre.processar_dados_mitre(dados)

    assert resultado[0][2] == "Fase Desconhecida"


def test_baixar_e_processar_mitre_usa_timeout(monkeypatch):
    chamadas = {}

    def fake_get(url, timeout):
        chamadas["url"] = url
        chamadas["timeout"] = timeout

        return FakeResponse(
            status_code=200,
            payload=criar_stix_sintetico(),
        )

    monkeypatch.setattr(
        ingest_mitre.requests,
        "get",
        fake_get,
    )

    resultado = ingest_mitre.baixar_e_processar_mitre()

    assert chamadas["url"] == ingest_mitre.MITRE_JSON_URL
    assert chamadas["timeout"] == 30
    assert len(resultado) == 1


def test_baixar_e_processar_mitre_rejeita_status_http_invalido(
    monkeypatch,
):
    monkeypatch.setattr(
        ingest_mitre.requests,
        "get",
        lambda url, timeout: FakeResponse(status_code=503),
    )

    try:
        ingest_mitre.baixar_e_processar_mitre()
    except RuntimeError as exc:
        assert "Status: 503" in str(exc)
    else:
        raise AssertionError("Era esperado RuntimeError para resposta HTTP inválida")


def test_salvar_no_supabase_rejeita_mitre_database_url_ausente(monkeypatch):
    monkeypatch.setattr(
        ingest_mitre,
        "MITRE_DATABASE_URL",
        None,
    )

    try:
        ingest_mitre.salvar_no_supabase(
            [],
            database_url=None,
        )
    except ValueError as exc:
        assert "MITRE_DATABASE_URL não encontrada" in str(exc)
    else:
        raise AssertionError("Era esperado ValueError sem MITRE_DATABASE_URL")


def test_salvar_no_supabase_nao_cria_schema(monkeypatch):
    conexao = FakeConnection()

    monkeypatch.setattr(
        ingest_mitre.psycopg2,
        "connect",
        lambda database_url, sslmode: conexao,
    )

    monkeypatch.setattr(
        ingest_mitre,
        "execute_values",
        lambda cursor, query, valores: None,
    )

    ingest_mitre.salvar_no_supabase(
        [],
        database_url="postgresql://fake",
    )

    assert all(
        "CREATE TABLE" not in query.upper() for query in conexao.cursor_obj.queries
    )


def test_salvar_no_supabase_forca_ssl_e_persiste_dados(monkeypatch):
    conexao = FakeConnection()
    chamadas = {}

    def fake_connect(database_url, sslmode):
        chamadas["database_url"] = database_url
        chamadas["sslmode"] = sslmode
        return conexao

    dados = [
        (
            "T1110",
            "Brute Force",
            "Credential Access",
            "Descrição",
            "Procedimento",
        )
    ]

    valores_recebidos = {}

    def fake_execute_values(cursor, query, valores):
        valores_recebidos["cursor"] = cursor
        valores_recebidos["query"] = query
        valores_recebidos["valores"] = valores

    monkeypatch.setattr(
        ingest_mitre.psycopg2,
        "connect",
        fake_connect,
    )

    monkeypatch.setattr(
        ingest_mitre,
        "execute_values",
        fake_execute_values,
    )

    ingest_mitre.salvar_no_supabase(
        dados,
        database_url="postgresql://fake",
    )

    assert chamadas["database_url"] == "postgresql://fake"
    assert chamadas["sslmode"] == "require"

    assert any(
        "TRUNCATE TABLE tbl_mitre_mapping" in query
        for query in conexao.cursor_obj.queries
    )

    assert valores_recebidos["valores"] == dados
    assert conexao.commits == 1
    assert conexao.cursor_obj.closed is True
    assert conexao.closed is True
