from fablab.common import FAB_MARK, FabKeys, FabTypes
from typing import Any, Dict, Callable, List, Hashable


class Serializer:
    _MEM_IGNORE_TYPES = (float, int, str)

    def __init__(self):
        self.memo: Dict[int, Any] = {}
        self.stack: List[Any] = []
        self.meta_stack: List[Any] = []

    def save(self, obj: Any):
        self.save_any(obj)
        return self.stack[0]

    def save_any(self, obj: Any):
        """Main internal entry point for serializing an object.

        Args:
            obj (Any): The object to serialize.
        """
        if type(obj) not in Serializer._MEM_IGNORE_TYPES and id(obj) in self.memo:
            self.save_ref(obj)
            return

        idx = len(self.memo)
        self.memo[id(obj)] = (idx, obj)

        saver = self.dispatch.get(type(obj))
        if saver is None:
            # Must be a custom class, so use a generic class saver.
            saver = self.dispatch[FabTypes.CLASS_INSTANCE]
        saver(self, obj)

    def push_context(self):
        """Pushes the main stack onto the meta_stack and creates a new stack."""
        self.meta_stack.append(self.stack)
        self.stack = []

    def pop_context(self):
        """Pops the top item off the meta stack onto the main stack."""
        self.stack = self.meta_stack.pop()

    def put(self, obj: Any):
        """Puts an object onto the main stack.

        Args:
            obj (Any): The object to put on the stack.
        """
        self.stack.append(obj)

    def save_ref(self, obj: Any):
        """Saves an item as a references.

        If an object has already been serialized, additional references to the object
        should be saved as a special reference to the first serialized object. This
        way, the object will be reconstructed appropriately in multiple places.
        """
        idx, _ = self.memo[id(obj)]
        ref_dict = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.REFERENCE,
                FabKeys.MEMO_ID: idx,
            },
        }
        self.put(ref_dict)

    # Methods below this point are dispatched through the dispatch table

    dispatch: Dict[Any, Callable] = {}

    def save_float(self, obj: float):
        """Saves a float.

        Args:
            obj (float): The float to save.
        """
        self.put(obj)

    dispatch[float] = save_float

    def save_int(self, obj: int):
        """Saves an int.

        Args:
            obj (int): The int to save.
        """
        self.put(obj)

    dispatch[int] = save_int

    def save_str(self, obj: str):
        """Saves a string.

        Args:
            obj (str): The string to save.
        """
        self.put(obj)

    dispatch[str] = save_str

    def save_tuple(self, obj: tuple):
        """Saves a tuple.

        Args:
            obj (tuple): The tuple to save.
        """
        saved_items: List[Any] = []
        config = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.TUPLE,
                FabKeys.ITEM_LIST: saved_items,
                FabKeys.MEMO_ID: self.memo[id(obj)][0],
            }
        }
        self.put(config)
        self.push_context()
        for item in obj:
            self.save_any(item)

        saved_items.extend(self.stack)
        self.pop_context()

    dispatch[tuple] = save_tuple

    def save_list(self, obj: list):
        """Saves a list.

        Args:
            obj (list): The list to save.
        """
        saved_items: List[Any] = []
        config = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.LIST,
                FabKeys.ITEM_LIST: saved_items,
                FabKeys.MEMO_ID: self.memo[id(obj)][0],
            }
        }
        self.put(config)
        self.push_context()

        for item in obj:
            self.save_any(item)

        saved_items.extend(self.stack)
        self.pop_context()

    dispatch[list] = save_list

    def save_dict(self, obj: dict):
        """Saves a dictionary.

        Args:
            obj (dict): The dictionary to save.
        """
        saved_items: Dict[Hashable, Any] = {}
        config = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.DICT,
                FabKeys.ITEM_DICT: saved_items,
                FabKeys.MEMO_ID: self.memo[id(obj)][0],
            }
        }
        self.put(config)
        self.push_context()

        for key, val in obj.items():
            self.save_any(key)
            self.save_any(val)

        # We expected key-value pairs in the stack, so make sure there's a even number
        assert len(self.stack) % 2 == 0

        key = None
        for item in self.stack:
            if key is None:
                key = item
                continue

            saved_items[key] = item
            key = None

        self.pop_context()

    dispatch[dict] = save_dict

    def save_type(self, obj: type):
        """Saves a type.

        Args:
            obj (object): The object to save.
        """
        config = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.TYPE,
                FabKeys.CLASS: obj.__name__,
                FabKeys.MODULE: obj.__module__,
            }
        }

        self.put(config)

    dispatch[type] = save_type

    def save_class_instance(self, obj: object):
        """Saves a generic class instance.

        Args:
            obj (object): The object to save.
        """
        saved_items: Dict[Hashable, Any] = {}
        config = {
            FAB_MARK: {
                FabKeys.TYPE: FabTypes.CLASS_INSTANCE,
                FabKeys.CLASS: obj.__class__.__name__,
                FabKeys.MODULE: obj.__module__,
                FabKeys.MEMO_ID: self.memo[id(obj)][0],
                FabKeys.ITEM_DICT: saved_items,
            }
        }

        self.put(config)
        self.push_context()

        for key, val in obj.__dict__.items():
            self.save_any(key)
            self.save_any(val)

        # We expected key-value pairs in the stack, so make sure there's a even number
        if len(self.stack) % 2 != 0:
            raise ValueError("Unpacking class failed!")

        keys = self.stack[0::2]
        values = self.stack[1::2]
        for key, value in zip(keys, values):
            saved_items[key] = value

        self.pop_context()

    dispatch[FabTypes.CLASS_INSTANCE] = save_class_instance


def save(obj: Any) -> dict:
    """Saves an object and returns the serialized dictionary representation.

    Args:
        obj (Any): The object to save.

    Returns:
        dict: The object serialized as a JSON-compatible dictionary.
    """

    serializer = Serializer()
    return serializer.save(obj)
