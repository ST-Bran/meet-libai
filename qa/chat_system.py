from typing import List, Tuple, Any

from qa.function_tool import map_question_to_function, map_question_to_function_args
from qa.question_type import QuestionType


def get_outline(question: str, history: List[List | None] = None) -> (Tuple[Any, QuestionType]):
    """
    根据问题获取答案或者完成任务
    :param history:
    :param query:
    :return:
    """
    question_type = parse_question(question)
    entities = check_entity(question)

    # 获取
    outline_generator = map_question_to_function(QuestionType.OUTLINE)
    args_getter = map_question_to_function_args(QuestionType.OUTLINE)
    args = args_getter([question_type, question, history, entities])

    result = outline_generator(*args)
    return result
