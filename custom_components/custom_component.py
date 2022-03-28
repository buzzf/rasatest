from typing import Dict, Text, Any, List, Type

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.nlu.featurizers.featurizer import Featurizer
from rasa.nlu.tokenizers.tokenizer import Tokenizer
from bert_serving.client import ConcurrentBertClient
from tqdm import tqdm
import numpy as np


# TODO: Correctly register your component with it's type
@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.INTENT_CLASSIFIER], is_trainable=True
)
class BertVectorsFeaturizer(Featurizer, GraphComponent):
    @classmethod
    def required_components(cls) -> List[Type]:
        """Components that should be included in the pipeline before this component."""
        return [Tokenizer]

    @staticmethod
    def required_packages() -> List[Text]:
        """Any extra python dependencies required for this component to run."""
        return ['numpy']

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        """Returns the component's default config."""
        return {
            **Featurizer.get_default_config(),
            # specifies the language of the subword segmentation model
        }

    def __init__(self, component_config=None):
        super(BertVectorsFeaturizer, self).__init__(component_config)
        ip = self._config['ip']
        port = self._config['port']
        port_out = self._config['port_out']
        show_server_config = self._config['show_server_config']
        output_fmt = self._config['output_fmt']
        check_version = self._config['check_version']
        timeout = self._config['timeout']
        identity = self._config['identity']
        # analyzer = self._config['analyzer']
        # token_pattern = self._config['token_pattern']
        # stop_words = self._config['stop_words']
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

    @classmethod
    def create(
            cls,
            config: Dict[Text, Any],
            model_storage: ModelStorage,
            resource: Resource,
            execution_context: ExecutionContext,
    ) -> GraphComponent:
        """Creates a new component (see parent class for full docstring)."""
        return cls(config, execution_context.node_name)

    def _get_text_feature(self, message):
        all_tokens = []
        # msg.text是用户的输入
        for msg in message:
            all_tokens.append(msg.text)
        bert_embedding = self.bc.encode(all_tokens, is_tokenized=False)
        return np.squeeze(bert_embedding)

    def train(self, training_data: TrainingData):
        batch_size = self.component_config['batch_size']

        epochs = len(training_data.training_examples) // batch_size + \
                 int(len(training_data.training_examples) % batch_size > 0)

        for ep in tqdm(range(epochs), desc="Epochs"):
            end_idx = (ep + 1) * batch_size
            start_idx = ep * batch_size
            examples = training_data.intent_examples[start_idx:end_idx]
            tokens_text = self._get_message_text(examples)
            X = np.array(tokens_text)

            for i, example in enumerate(examples):
                if len(examples) > 1:
                    example.set(
                        "text_features", self.add_features_to_message(example, X[i]))
                else:
                    example.set(
                        "text_features", self.add_features_to_message(example, X))

    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        # TODO: Implement this if your component augments the training data with
        #       tokens or message features which are used by other components
        #       during training.
        # components during training.
        ...

        return training_data

    def _get_message_text(self, message):
        all_tokens = []

        for msg in message:
            all_tokens.append(msg.text)

        bert_embedding = self.bc.encode(all_tokens, is_tokenized=False)
        return np.squeeze(bert_embedding)

    def process(self, messages: List[Message]) -> List[Message]:
        # TODO: This is the method which Rasa Open Source will call during inference.
        message_text = self._get_message_text(messages)

        messages.set("text_features", self._combine_with_existing_text_features(
            messages, message_text))
        for message in messages:
            for attribute in DENSE_FEATURIZABLE_ATTRIBUTES:
                self._set_features(message, attribute)
        return messages
