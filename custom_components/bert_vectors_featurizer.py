from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
import json
from typing import Any, Optional, Text
import numpy as np
from rasa.nlu.featurizers import Featurizer
# from rasa.nlu.training_data import Message
from rasa.shared.nlu.training_data.message import Message
from rasa.nlu.components import Component
from rasa.nlu.model import Metadata
from bert_serving.client import ConcurrentBertClient
from tqdm import tqdm


class BertVectorsFeaturizer(Featurizer):
    provides = ['text_features', 'result_log']  # 组建产生的输出
    defaults = {
        'ip': 'localhost',
        'port': 5555,
        'port_out': 5556,
        'show_server_config': False,
        'output_fmt': 'ndarray',
        'check_version': True,
        'timeout': 5000,
        'identity': None,
        'batch_size': 128
    }

    @classmethod
    def required_packages(cls):
        return ['numpy', 'bert_serving', 'sklearn']

    def __init__(self, component_config=None):
        super(BertVectorsFeaturizer, self).__init__(component_config)
        ip = self.component_config['ip']
        port = self.component_config['port']
        port_out = self.component_config['port_out']
        show_server_config = self.conponent_config['show_server_config']
        output_fmt = self.component_config['output_fmt']
        check_version = self.component_config['check_version']
        timeout = self.component_config['timeout']
        identity = self.component_config['identity']
        # analyzer = self.component_config['analyzer']
        # token_pattern = self.component_config['token_pattern']
        # stop_words = self.component_config['stop_words']
        try:
            self.bc = ConcurrentBertClient(
                ip=ip,
                port=int(port),
                port_out=int(port_out),
                show_server_config=show_server_config,
                output_fmt=output_fmt,
                check_version=check_version,
                timeout=int(timeout),
                identity=identity
            )
        except Exception as e:
            print('bert-service-exception', e)

    def _get_text_feature(self, message):
        all_tokens = []
        # msg.text是用户的输入
        for msg in message:
            all_tokens.append(msg.text)
        bert_embedding = self.bc.encode(all_tokens, is_tokenized=False)
        return np.squeeze(bert_embedding)

    def train(self, training_data, cfg=None, **kwargs):
        batch_size = self.component_config['batch_size']
        epochs = len(training_data.intent_examples) // batch_size + int(len(training_data.intent_examples) % batch_size > 0)

        for ep in tqdm(range(epochs), desc='Epochs'):
            end_idx = (ep + 1) * batch_size
            start_idx = ep * batch_size
            examples = training_data.intent_examples[start_idx:end_idx]
            tokens_text = self._get_text_feature(examples)
            X = np.array(tokens_text)

            for i, example in enumerate(examples):
                examples.set('text_features', self._combine_with_existing_features(example, X[i]))

    def process(self, message, **kwargs):
        composed_query = json.loads(message.text, encoding='utf-8')
        query = composed_query.get('question', '')
        theme_info = composed_query.get('theme_info', [])  # [{'id': '', 'object': ['id1', 'id2']}]
        message.text = query
        text_feature = self._get_text_feature([message])
        message.set('question', query, add_to_output=True)
        message.set('theme_info', theme_info, add_to_output=True)
        message.set('text_features', self._combine_with_existing_features(message, text_feature))

    @classmethod
    def load(
            cls,
            meta,
            model_dir=None,  # type: Text
            model_metadata=None,  # type: Metadata
            cached_component=None,  # type: Optional[Component]
            **kwargs  # type: **Any
    ):
        return cls(meta)
























