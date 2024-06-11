import json
import re

import pymysql
from pymysql.cursors import DictCursor

from config.prompt_config import init_draft_prompt, label_query_prompt, outline_generate_prompt, MUSEUM_COLLECTION_DDL
from lang_chain.retriever.document_retriever import retrieve_docs, retrieve_docs_with_score
from lang_chain.zhipu_chat import chat_with_ai


def get_initial_draft(user_input: str):
    """
    根据用户输入生成初稿
    """
    draft = []
    _prompt = f"""    
    {init_draft_prompt}
    用户输入: {user_input}
    """

    origin_draft = chat_with_ai(_prompt)
    print(f'AI返回的初稿：{origin_draft}')
    pattern = r"```json(.*?)```"
    matched = re.search(pattern, origin_draft, re.DOTALL)
    if matched:
        draft = json.loads(matched.group(1).strip())  # 清除前后的空格和换行符
        print(f'初稿内容：{draft}')
    else:
        print("No JSON code block found.")
    return draft


def get_related_docs(bullypoint):
    """
    根据用户输入检索相关文档
    """
    # bullypoint = json.loads(user_input)
    print(f'检索文档的用户输入：{bullypoint}')
    content = bullypoint.get("content")
    _context, docs = retrieve_docs_with_score(content)
    bullypoint["docs"] = _context
    return bullypoint


def get_related_labels(initial_draft):
    """
    根据初稿检索多媒体资源标签(元数据)
    """
    # 存储结果的字典
    results = {}
    # 结果输出为需要的格式
    output = []
    _prompt = f"""    
    {label_query_prompt}
    J={initial_draft}
    M={MUSEUM_COLLECTION_DDL}
    """
    response = chat_with_ai(_prompt)
    print(f'增加了多媒体查询语句的初稿：{response}')
    pattern = r"```json(.*?)```"
    matched = re.search(pattern, response, re.DOTALL)
    if matched:
        draft_with_sql = json.loads(matched.group(1).strip())  # 清除前后的空格和换行符
        print(f'bullypoint_with_sql：{draft_with_sql}')
        # 执行sql，处理数据
        # 处理数据
        for entry in draft_with_sql:
            bullypoint = entry['bullypoint']
            sql_query = entry['sql_query']
            query_result = execute_sql(sql_query)
            if bullypoint not in results:
                results[bullypoint] = []  # 初始化空列表
            if query_result:
                results[bullypoint].extend(query_result)
        for key, value in results.items():
            output.append({"bullypoint": key, "resources": value})
    else:
        print(f'No JSON code block found.')
    return output



def get_outline(draft: str, resources_map):
    """
    根据解说初稿和资源生成解说大纲
    """
    _prompt = f"""    
    {outline_generate_prompt}
    J: {draft}
    X: {resources_map}
    """
    response = chat_with_ai(_prompt)
    print(f'增加了多媒体查询语句的初稿：{response}')


def execute_sql(sql: str):
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="admin",
        database="knowledge_base"
    )
    try:
        # 创建 cursor 使用 DictCursor 方便结果以字典形式返回
        cursor = conn.cursor(cursor=DictCursor)

        # 执行 SQL 语句
        cursor.execute(sql)

        # 判断 SQL 类型，如果是 SELECT，则返回结果
        if sql.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
            return result
        else:
            # 对于非 SELECT 语句，如 INSERT、UPDATE 或 DELETE，提交事务
            conn.commit()
    finally:
        # 无论成功与否，都关闭 cursor 和连接以释放资源
        cursor.close()
        conn.close()

