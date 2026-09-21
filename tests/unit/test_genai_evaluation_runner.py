from src.genai.contracts import LlmResponse
from src.genai.evaluation_cases import build_generative_evaluation_cases
from src.genai.evaluation_runner import run_generative_evaluation
from src.genai.response_evaluation import EvaluationVerdict


class RecordingAdapter:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)

        return LlmResponse(
            content=(
                "O incidente não está confirmado. "
                "É necessário coletar e verificar as evidências ausentes."
            )
        )


class FalseConfirmationAdapter:
    def generate(self, request):
        return LlmResponse(
            content=("O incidente está confirmado e houve comprometimento da conta.")
        )


def _criterion(execution, criterion_name):
    return next(
        criterion
        for criterion in execution.evaluation.criteria
        if criterion.name == criterion_name
    )


def test_runner_executa_todo_catalogo_pelo_conversation_service():
    adapter = RecordingAdapter()
    cases = build_generative_evaluation_cases()

    run = run_generative_evaluation(
        adapter,
        cases=cases,
    )

    assert len(run.executions) == 5
    assert len(adapter.requests) == 5

    assert [execution.case_id for execution in run.executions] == [
        case.case_id for case in cases
    ]

    for request, case in zip(
        adapter.requests,
        cases,
        strict=True,
    ):
        assert request.user_message == case.user_message
        assert case.assessment.alert_id in request.context


def test_runner_preserva_resposta_bruta_e_avaliacao():
    adapter = RecordingAdapter()
    case = build_generative_evaluation_cases()[3]

    run = run_generative_evaluation(
        adapter,
        cases=(case,),
    )

    execution = run.executions[0]

    assert execution.case_id == "ALT-EVAL-004"
    assert execution.response_text
    assert execution.evaluation.case_id == "ALT-EVAL-004"


def test_runner_detecta_confirmacao_falsa_em_resposta_do_adapter():
    adapter = FalseConfirmationAdapter()

    case = next(
        case
        for case in build_generative_evaluation_cases()
        if case.case_id == "ALT-EVAL-003"
    )

    run = run_generative_evaluation(
        adapter,
        cases=(case,),
    )

    execution = run.executions[0]

    authority = _criterion(
        execution,
        "authority_preservation",
    )

    assert authority.verdict is EvaluationVerdict.FAIL
