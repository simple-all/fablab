import importlib
from typing import Any, List, Dict, Hashable
from fablab.common import FAB_MARK, FabKeys, FabTypes
from functools import partial


def is_buildable(item: Any) -> bool:
    if not isinstance(item, dict):
        return False

    return FAB_MARK in item


class Builder:
    def __init__(self):
        self.memo = {}
        self.stack = []
        self.meta_stack = []
        self.jobs = []
        self.meta_jobs = []

    def put(self, obj: Any):
        self.stack.append(obj)

    def push_context(self):
        self.meta_stack.append(self.stack)
        self.stack = []

    def pop_context(self):
        self.stack = self.meta_stack.pop()

    def push_jobs(self):
        self.meta_jobs.append(self.jobs)
        self.jobs = []

    def pop_jobs(self):
        self.jobs = self.meta_jobs.pop()

    def do_jobs(self):
        for job in self.jobs:
            job()

        self.jobs.clear()

    def load(self, items: list):
        self.load_any(items)

        while self.jobs:
            self.do_jobs()
            # TODO: Investigate if there's ever a case when meta jobs are not completed
            # if self.meta_jobs:
            #     self.pop_jobs()

        return self.stack[0]

    def load_any(self, obj: Any):
        if not is_buildable(obj):
            self.put(obj)
            return

        self.load_fab(obj)

    def load_fab(self, config: dict):
        fab_info = config[FAB_MARK]
        fab_type = fab_info[FabKeys.TYPE]

        loader = self.dispatch[fab_type]
        loader(self, config)

    dispatch = {}

    def load_tuple(self, config: dict):
        fab_info = config[FAB_MARK]

        self.push_jobs()

        fini_job = partial(self.fini_tuple, config)
        self.jobs.append(fini_job)

        self.push_context()
        for item in fab_info[FabKeys.ITEM_LIST]:
            self.load_any(item)

        self.do_jobs()
        self.pop_jobs()

    dispatch[FabTypes.TUPLE] = load_tuple

    def fini_tuple(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]
        new_tuple = tuple(self.stack)
        self.pop_context()
        self.put(new_tuple)
        self.memo[memo_id] = new_tuple

    def load_list(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]
        new_list: List[Any] = []
        self.memo[memo_id] = new_list
        self.put(new_list)

        fini_job = partial(self.fini_list, config)

        self.jobs.append(fini_job)

    dispatch[FabTypes.LIST] = load_list

    def fini_list(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]

        list_obj: list = self.memo[memo_id]

        self.push_context()
        self.push_jobs()
        for item in fab_info[FabKeys.ITEM_LIST]:
            self.load_any(item)

        self.do_jobs()
        self.pop_jobs()

        list_obj.extend(self.stack)
        self.pop_context()

    def load_dict(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]

        new_dict: Dict[Hashable, Any] = {}
        self.memo[memo_id] = new_dict

        self.put(new_dict)
        fini_job = partial(self.fini_dict, config)

        self.jobs.append(fini_job)

    dispatch[FabTypes.DICT] = load_dict

    def fini_dict(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]

        dict_obj: dict = self.memo[memo_id]

        self.push_context()
        self.push_jobs()
        for key, val in fab_info[FabKeys.ITEM_DICT].items():
            self.load_any(key)
            self.load_any(val)

        self.do_jobs()
        self.pop_jobs()

        # We expected key-value pairs in the stack, so make sure there's a even number
        assert len(self.stack) % 2 == 0

        key = None
        for item in self.stack:
            if key is None:
                key = item
                continue

            dict_obj[key] = item
            key = None

        self.pop_context()

    def load_reference(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]
        item = self.memo[memo_id]

        self.put(item)

    dispatch[FabTypes.REFERENCE] = load_reference

    def load_type(self, config: dict):
        """Builds a class from a FabLab dictionary."""
        fab_info = config[FAB_MARK]
        module_name = fab_info[FabKeys.MODULE]
        class_name = fab_info[FabKeys.CLASS]

        module_obj = importlib.import_module(module_name)
        class_obj = getattr(module_obj, class_name)

        self.put(class_obj)

    dispatch[FabTypes.TYPE] = load_type

    def load_class_instance(self, config: dict):
        """Builds a class instance from a FabLab dictionary.

        Args:
            config (dict): A FabLab dictionary.

        Returns:
            Any: The constructed object.
        """
        # Get the fab information
        fab_info = config[FAB_MARK]
        module_name = fab_info[FabKeys.MODULE]
        class_name = fab_info[FabKeys.CLASS]

        # Get the class and construct an instance
        module_obj = importlib.import_module(module_name)
        class_obj = getattr(module_obj, class_name)
        instance: object = class_obj.__new__(class_obj)

        memo_id = fab_info[FabKeys.MEMO_ID]
        self.memo[memo_id] = instance
        self.put(instance)

        fini_job = partial(self.fini_class_instance, config)

        self.jobs.append(fini_job)

    def fini_class_instance(self, config: dict):
        fab_info = config[FAB_MARK]
        memo_id = fab_info[FabKeys.MEMO_ID]

        instance: dict = self.memo[memo_id]

        self.push_context()
        self.push_jobs()
        for key, val in fab_info[FabKeys.ITEM_DICT].items():
            self.load_any(key)
            self.load_any(val)

        self.do_jobs()
        self.pop_jobs()

        # We expected key-value pairs in the stack, so make sure there's a even number
        assert len(self.stack) % 2 == 0

        key = None
        for item in self.stack:
            if key is None:
                key = item
                continue

            instance.__dict__[key] = item
            key = None

        self.pop_context()

    dispatch[FabTypes.CLASS_INSTANCE] = load_class_instance


def load(items: list) -> list:
    builder = Builder()
    return builder.load(items)
