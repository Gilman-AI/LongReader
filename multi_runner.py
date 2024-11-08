"""Basic framework for running asynchronous tasks in Directed Acyclic Graphs."""

import inspect

from anyio import create_memory_object_stream
from anyio.streams.memory import MemoryObjectSendStream


def create_dag_node(
    this_func: callable,
    send_to: list[MemoryObjectSendStream],
    dynamic_params: list[str] | None = None
) -> tuple[callable, MemoryObjectSendStream]:

    """Create a DAG (Directed Acyclic Graph) node from a given function.

    Args:
      this_func (callable):
        The function to be wrapped as a DAG node. It must return a dictionary
        representing the output data.
      send_to (list[MemoryObjectSendStream]):
        A list of send streams to which the output data will be returned.

    Returns in a tuple:
      callable:
        The async wrapper function, which should be passed to a task group via
        `start_soon`, not awaited.
      MemoryObjectSendStream:
        The send stream for the node. Remember these need to be cloned if
        used more than once.

    The wrapper function waits until all the required input parameters have been
    sent, evaluates the given function, and sends the output data to the
    specified send streams. The wrapper function can only be called once, as the
    receive stream will be closed after the first iteration.
    """
    send_stream, receive_stream = create_memory_object_stream()
    if dynamic_params is None:
        params = list(inspect.signature(this_func).parameters.keys())
    else:
        params = dynamic_params

    async def wrapper():
        # Collate data
        input_data = {}
        async with receive_stream:
            async for key, value in receive_stream:
                input_data[key] = value
                if all([param in input_data for param in params]):
                    break
        # Evaluate function; must return a dictionary
        output_data = await this_func(**input_data)
        # Send data
        for stream in send_to:
            async with stream:
                for key, value in output_data.items():
                    await stream.send((key, value))
    return wrapper, send_stream
