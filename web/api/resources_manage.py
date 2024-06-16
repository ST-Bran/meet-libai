import os
import shutil
import uuid
from typing import Dict, Optional

import mysql
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from starlette.responses import JSONResponse, FileResponse, StreamingResponse

from lang_chain.qianwen_chat import qianwen_sync_call_streaming
from model.graph_entity.search_model import INSTANCE as GRAPH_ENTITY_SEARCHER
from model.model_base import ModelBase
from model.rag.retriever_model import INSTANCE as RAG_RETRIEVER
from qa.function_tool import outline_generate_tool
from web.audio.tts import test_2_audio, AUDIO_DIRECTORY

__MODEL_INSTANCE: Dict[str, ModelBase] = {
    GRAPH_ENTITY_SEARCHER.name: GRAPH_ENTITY_SEARCHER,
    RAG_RETRIEVER.name: RAG_RETRIEVER,
}

# 配置MySQL数据库连接
DATABASE_URL = "mysql+pymysql://root:admin@localhost:3306/knowledge_base"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 获取当前文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 生成本地多媒体资源存储路径
UPLOAD_DIRECTORY = os.path.join(current_dir, "..", "..", "data", "corpus", "multimedia_resources")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# 保存每个请求需要发送的文件总数的状态
total_files = {}


# 定义数据库模型
class MuseumCollection(Base):
    __tablename__ = "museum_collection"
    item_name = Column(String(255), nullable=False, comment='藏品名称')
    item_id = Column(String(50), primary_key=True, nullable=False, comment='藏品编号')
    description = Column(Text, comment='描述')
    date = Column(String(50), comment='时间')
    location = Column(String(255), comment='地点')
    person = Column(String(255), comment='人物')
    event = Column(Text, comment='事件')
    revolutionary_stage = Column(String(255), comment='革命阶段')
    important_meeting = Column(String(255), comment='重要会议')
    military_action = Column(String(255), comment='军事行动')
    social_movement = Column(String(255), comment='社会运动')
    type = Column(String(255), comment='类型')
    material = Column(String(255), comment='原始材质')
    dimensions = Column(String(255), comment='原始尺寸')
    condition = Column(String(255), comment='状态')
    keywords = Column(Text, comment='关键词')
    language = Column(String(50), comment='语言')
    digitization_method = Column(String(255), comment='数字化方法')
    file_format = Column(String(255), comment='数字文件格式')
    basic_info = Column(String(50), comment='基本信息')


def register_routes(app: FastAPI):
    @app.post('/resource/upload',
              description="多媒体资源上传",
              tags=["多媒体资源上传"])
    def upload_multimedia_resource(
            file: UploadFile = File(..., description="上传资源"),
            description: str = Form(..., description="描述"),
            date: Optional[str] = Form(None, description="时间"),
            location: Optional[str] = Form(None, description="地点"),
            person: Optional[str] = Form(None, description="人物"),
            event: Optional[str] = Form(None, description="事件"),
            revolutionary_stage: Optional[str] = Form(None, description="革命阶段"),
            important_meeting: Optional[str] = Form(None, description="重要会议"),
            military_action: Optional[str] = Form(None, description="军事行动"),
            social_movement: Optional[str] = Form(None, description="社会运动"),
            resource_type: Optional[str] = Form(None, description="类型"),
            material: Optional[str] = Form(None, description="原始材质"),
            dimensions: Optional[str] = Form(None, description="原始尺寸"),
            condition: Optional[str] = Form(None, description="状态"),
            keywords: Optional[str] = Form(None, description="关键词"),
            language: Optional[str] = Form(None, description="语言"),
            digitization_method: Optional[str] = Form(None, description="数字化方法"),
            file_format: Optional[str] = Form(None, description="数字文件格式"),
            basic_info: Optional[str] = Form(None, description="基本信息")
    ):
        """
        上传多媒体资源并建立标签库
        """
        try:
            # Ensure the upload directory exists
            os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

            # Generate a unique ID for the file
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            file_path = os.path.join(UPLOAD_DIRECTORY, file_id + file_extension)

            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Insert file information into the database
            db = SessionLocal()
            new_item = MuseumCollection(
                item_name=file.filename,
                item_id=file_id,
                description=description,
                date=date,
                location=location,
                person=person,
                event=event,
                revolutionary_stage=revolutionary_stage,
                important_meeting=important_meeting,
                military_action=military_action,
                social_movement=social_movement,
                type=resource_type,
                material=material,
                dimensions=dimensions,
                condition=condition,
                keywords=keywords,
                language=language,
                digitization_method=digitization_method,
                file_format=file_format,
                basic_info=basic_info
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            return JSONResponse(content={"message": "File uploaded successfully", "file_id": file_id})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            file.file.close()
        return {"resource_id": resource_id, "filename": file.filename}

    @app.post('/generate_outline')
    def build(background_tasks: BackgroundTasks,
              query: Optional[str] = Form(..., description="输入"),
              request_id: Optional[str] = Form(..., description="请求id")
              ):
        # 同步返回
        response = process_data(query, request_id)
        return {"data": response}
        # 添加任务到后台执行
        # background_tasks.add_task(process_data, query, request_id)
        # 立即返回响应
        # return {"message": "任务正在后台执行"}

    @app.post('/inference')
    def build(query: Optional[str] = Form(..., description="输入")):
        return StreamingResponse(qianwen_sync_call_streaming(query), media_type="text/plain")


    @app.get('/audio_result')
    def build(request_id: Optional[str] = Form(..., description="请求id")):
        # 立即返回响应
        return {"message": "任务正在后台执行"}

    @app.get("/api/get_audio")
    def stream(background_tasks: BackgroundTasks,
               request_id: Optional[str] = Form(..., description="请求id")
               ):
        files_list = []
        for root, dirs, files in os.walk(AUDIO_DIRECTORY):
            for file in files:
                if file.startswith(request_id + '---') and file.endswith('.wav'):
                    files_list.append(file)
            # 按照number进行排序
            files_list.sort(key=lambda x: int(x.split('---')[-1].split('.')[0]))

            # 如果request_id不存在，抛出一个404错误
            if request_id not in total_files:
                raise HTTPException(status_code=404, detail="Request ID not found")

            # 如果所有文件都已发送，返回一个特殊标识
            if total_files[request_id] <= 0:
                return {"message": "All files have been sent."}
            else:
                file_path = os.path.join(root, files_list[0])
                total_files[request_id] -= 1  # 更新需要发送的文件总数
                background_tasks.add_task(remove_file, file_path)
                return FileResponse(file_path, media_type='audio/wav')

    def process_data(query: str, request_id: str):
        outline = outline_generate_tool(query)
        result_dict = {"outline": outline, "resources_abs_path": ""}
        # 将文件总数保存在服务器上
        # total_files[request_id] = len(outline)
        # for bullypoint in outline:
        #     content = bullypoint["content"]
        #     number = bullypoint["bullypoint"]
        #     file_name = f'{request_id}---{number}'
        #     test_2_audio(content, file_name)
        return result_dict

    def remove_file(path: str):
        os.remove(path)
