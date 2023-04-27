from typing import Any, Dict, List, Optional, Sequence
from gpt_index.indices.base import BaseGPTIndex
from gpt_index.indices.composability.graph import ComposableGraph
from gpt_index.indices.registry import INDEX_STRUCT_TYPE_TO_INDEX_CLASS
from gpt_index.storage.storage_context import StorageContext

import logging

logger = logging.getLogger(__name__)


def load_index_from_storage(
    storage_context: Optional[StorageContext] = None,
    index_id: Optional[str] = None,
    **kwargs: Any,
) -> BaseGPTIndex:
    storage_context = StorageContext.from_defaults()

    index_ids: Optional[Sequence[str]]
    if index_id is None:
        index_ids = None
    else:
        index_ids = [index_id]

    indices = load_indices_from_storage(storage_context, index_ids=index_ids, **kwargs)

    if len(indices) == 0:
        raise ValueError(
            "No index in storage context, check if you specified the right persist_dir."
        )
    elif len(indices) > 1:
        raise ValueError(
            f"Expected to load a single index, but got {len(indices)} instead. "
            "Please specify index_id."
        )

    return indices[0]


def load_indices_from_storage(
    storage_context: Optional[StorageContext] = None,
    index_ids: Optional[Sequence[str]] = None,
    **kwargs: Any,
) -> List[BaseGPTIndex]:
    storage_context = storage_context or StorageContext.from_defaults()

    if index_ids is None:
        logger.info("Loading all indices.")
        index_structs = storage_context.index_store.index_structs()
    else:
        logger.info(f"Loading indices with ids: {index_ids}")
        index_structs = [
            storage_context.index_store.get_index_struct(index_id)
            for index_id in index_ids
        ]

    indices = []
    for index_struct in index_structs:
        type_ = index_struct.get_type()
        index_cls = INDEX_STRUCT_TYPE_TO_INDEX_CLASS[type_]
        index = index_cls(
            index_struct=index_struct, storage_context=storage_context, **kwargs
        )
        indices.append(index)
    return indices


def load_graph_from_storage(
    root_id: str,
    storage_context: Optional[StorageContext] = None,
    **kwargs: Any,
) -> ComposableGraph:
    storage_context = storage_context or StorageContext.from_defaults()

    indices = load_indices_from_storage(storage_context, index_ids=None, **kwargs)
    all_indices = {index.index_id: index for index in indices}
    graph = ComposableGraph(all_indices=all_indices, root_id=root_id)
    return graph
