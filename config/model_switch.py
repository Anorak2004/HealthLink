"""
AI模型切换配置模块
支持 API调用 -> 本地模型 无缝切换
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import httpx
import yaml

class BaseModelProvider(ABC):
    """模型提供者基类"""
    
    @abstractmethod
    async def process_text(self, text: str, task: str = "ner") -> Dict[str, Any]:
        """处理文本"""
        pass
    
    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """处理音频"""
        pass

class APIModelProvider(BaseModelProvider):
    """API模型提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        self.nlp_config = config['ai_models']['nlp']['api']
        self.asr_config = config['ai_models']['asr']['api']
        self.client = httpx.AsyncClient()
    
    async def process_text(self, text: str, task: str = "ner") -> Dict[str, Any]:
        """调用NLP API处理文本"""
        try:
            response = await self.client.post(
                f"{self.nlp_config['endpoint']}/process",
                json={
                    "text": text,
                    "task": task
                },
                headers={
                    "Authorization": f"Bearer {self.nlp_config['api_key']}",
                    "Content-Type": "application/json"
                },
                timeout=self.nlp_config['timeout']
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # 如果启用了fallback，返回简化结果
            if self._is_fallback_enabled():
                return self._fallback_nlp_result(text)
            raise e
    
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """调用ASR API处理音频"""
        try:
            files = {"audio": ("audio.wav", audio_data, "audio/wav")}
            response = await self.client.post(
                f"{self.asr_config['endpoint']}/transcribe",
                files=files,
                headers={
                    "Authorization": f"Bearer {self.asr_config['api_key']}"
                },
                timeout=self.asr_config['timeout']
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if self._is_fallback_enabled():
                return self._fallback_asr_result()
            raise e
    
    def _is_fallback_enabled(self) -> bool:
        """检查是否启用fallback"""
        config = load_model_config()
        return config['ai_models'].get('fallback_enabled', False)
    
    def _fallback_nlp_result(self, text: str) -> Dict[str, Any]:
        """NLP fallback结果"""
        # 简单的关键词匹配作为fallback
        keywords = self._load_keywords()
        entities = []
        
        for category, terms in keywords.items():
            for term in terms:
                if term in text:
                    entities.append({
                        "text": term,
                        "label": category,
                        "confidence": 0.5,
                        "start": text.find(term),
                        "end": text.find(term) + len(term)
                    })
        
        return {
            "entities": entities,
            "confidence": 0.5,
            "fallback": True
        }
    
    def _fallback_asr_result(self) -> Dict[str, Any]:
        """ASR fallback结果"""
        return {
            "text": "[音频转写失败，请手动输入]",
            "confidence": 0.0,
            "fallback": True
        }
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """加载关键词列表"""
        keywords_path = os.path.join(os.path.dirname(__file__), "asr_keywords.json")
        with open(keywords_path, 'r', encoding='utf-8') as f:
            return json.load(f)

class LocalModelProvider(BaseModelProvider):
    """本地模型提供者（预留接口）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.nlp_config = config['ai_models']['nlp']['local']
        self.asr_config = config['ai_models']['asr']['local']
        self._nlp_model = None
        self._asr_model = None
    
    async def process_text(self, text: str, task: str = "ner") -> Dict[str, Any]:
        """使用本地NLP模型处理文本"""
        if self._nlp_model is None:
            self._load_nlp_model()
        
        # 这里是本地模型调用的占位实现
        # 实际使用时需要根据具体模型库（如transformers）来实现
        return {
            "entities": [],
            "confidence": 0.8,
            "model": "local",
            "note": "本地模型实现待完善"
        }
    
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """使用本地ASR模型处理音频"""
        if self._asr_model is None:
            self._load_asr_model()
        
        # 本地ASR模型调用占位实现
        return {
            "text": "[本地ASR模型待实现]",
            "confidence": 0.8,
            "model": "local"
        }
    
    def _load_nlp_model(self):
        """加载本地NLP模型"""
        # 预留：加载transformers模型
        # from transformers import AutoTokenizer, AutoModel
        # self._nlp_model = AutoModel.from_pretrained(self.nlp_config['model_path'])
        pass
    
    def _load_asr_model(self):
        """加载本地ASR模型"""
        # 预留：加载whisper或其他ASR模型
        # import whisper
        # self._asr_model = whisper.load_model(self.asr_config['model_path'])
        pass

def load_model_config() -> Dict[str, Any]:
    """加载模型配置"""
    config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_model_provider(config: Dict[str, Any] = None) -> BaseModelProvider:
    """创建模型提供者"""
    if config is None:
        config = load_model_config()
    
    provider_type = config['ai_models']['nlp']['provider']
    
    if provider_type == 'api':
        return APIModelProvider(config)
    elif provider_type == 'local':
        return LocalModelProvider(config)
    else:
        raise ValueError(f"Unsupported model provider: {provider_type}")

# 全局模型提供者实例
_model_provider = None

def get_model_provider() -> BaseModelProvider:
    """获取全局模型提供者"""
    global _model_provider
    if _model_provider is None:
        _model_provider = create_model_provider()
    return _model_provider

async def process_clinical_text(text: str) -> Dict[str, Any]:
    """处理临床文本的便捷函数"""
    provider = get_model_provider()
    return await provider.process_text(text, task="clinical_ner")

async def transcribe_audio(audio_data: bytes) -> Dict[str, Any]:
    """音频转写的便捷函数"""
    provider = get_model_provider()
    return await provider.process_audio(audio_data)