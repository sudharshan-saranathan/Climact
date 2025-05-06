import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform

from core.category import Category
from core.resource import Resource
from tabs.schema    import graph
from tabs.schema.action import CreateNodeAction, BatchActions, CreateHandleAction, ConnectHandleAction, \
    CreateStreamAction
from tabs.schema.graph import Node, Connector, Stream


class JsonLib:
    """
    Utility class for serializing and deserializing schematics (nodes and connectors)
    to and from JSON format for the canvas-based process modeling application.

    Static Methods:
    ---------------
    - serialize(item):
        Serializes a single `Node` or `Connector` object to a JSON-compatible dictionary.
        Includes node position, size, equations, and variables; or connector endpoints.

    - encode_json(canvas):
        Serializes all selected items from the canvas (or all nodes and connectors if none are selected)
        into a JSON string. Used for exporting schematics or dragging between scenes.

    - decode_json(code: str, canvas):
        Parses a schematic JSON string and reconstructs the corresponding nodes, variables, and connectors
        on the given `Canvas`. All actions are grouped into a single undoable `BatchAction`.
    """

    @staticmethod
    def serialize(item):

        if isinstance(item, graph.Node):

            variables   = list()
            equations   = list()
            parameters  = list()

            # Serialize variable information:
            for variable in item.variables:
                variable_obj = {
                    "variable-symbol"   : str(variable.symbol),
                    "variable-stream"   : str(variable.stream),
                    "variable-label"    : variable.label,
                    "variable-units"    : variable.units,
                    "variable-cname"    : variable.cname,
                    "variable-info"     : variable.info,
                    "variable-value"    : variable.value,
                    "variable-sigma"    : variable.sigma,
                    "variable-minimum"  : variable.minimum,
                    "variable-maximum"  : variable.maximum,
                    "variable-position" : {
                        "x": variable.pos().x(),
                        "y": variable.pos().y()
                    }
                }
                variables.append(variable_obj)

            # Serialize parameter information:
            for parameter in item.parameters:
                parameter_obj = {
                    "parameter-symbol"   : str(parameter.symbol),
                    "parameter-stream"   : str(parameter.stream),
                    "parameter-label"    : parameter.label,
                    "parameter-units"    : parameter.units,
                    "parameter-cname"    : parameter.cname,
                    "parameter-info"     : parameter.info,
                    "parameter-value"    : parameter.value,
                    "parameter-sigma"    : parameter.sigma,
                    "parameter-minimum"  : parameter.minimum,
                    "parameter-maximum"  : parameter.maximum,
                }
                parameters.append(parameter_obj)

            # Serialize equations:
            for equation in item.equations:
                equations.append(equation)

            # JSON-composite:
            node_object = {
                "variables"  : variables,
                "node-name"  : item.name,
                "node-type"  : 0,
                "node-height": item.boundingRect().height(),
                "node-position": {
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                },
                "parameters" : parameters,
                "equations"  : equations
            }

            return node_object

        if isinstance(item, graph.Stream):

            stream_obj = {
                "flow-type"       : str(item.stream),
                "flow-label"      : item.label,
                "flow-cname"      : item.socket.cname,
                "flow-position"   : {
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                }
            }

            return stream_obj

        if isinstance(item, graph.Connector):

            connection_obj = {
                "connection-origin": {
                    "x": item.origin.scenePos().x(),
                    "y": item.origin.scenePos().y()
                },
                "connection-target": {
                    "x": item.target.scenePos().x(),
                    "y": item.target.scenePos().y()
                }
            }

            return connection_obj

        return None

    @staticmethod
    def encode_json(canvas):

        # If no items are explicitly selected, serialize all items:
        selection = canvas.selectedItems()
        items = selection if selection else canvas.node_items | canvas.flow_items | canvas.edge_items

        # Initialize JSON-objects:
        schematic  = {}
        node_array = []
        flow_array = []
        link_array = []

        # Serialize items:
        for item in items:

            # Serialize nodes:
            if isinstance(item, Node) and canvas.node_items[item]:
                node_array.append(JsonLib.serialize(item))

            # Serialize streams:
            if isinstance(item, Stream) and canvas.flow_items[item]:
                flow_array.append(JsonLib.serialize(item))

            # Serialize links:
            elif isinstance(item, Connector) and canvas.edge_items[item]:
                link_array.append(JsonLib.serialize(item))

        schematic["NODES"] = node_array
        schematic["FLOWS"] = flow_array
        schematic["CONNECTORS"] = link_array

        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode_json(code: str, canvas, group_actions: bool = False):

        with open("debug_code.json", "w", encoding="utf-8") as f:
            f.write(code)

        # Convert file contents to JSON-parsable:
        root = json.loads(code)

        # Import canvas module:
        from tabs.schema.canvas import Canvas
        if not isinstance(canvas, Canvas):
            return

        # Initialize batch-actions:
        batch = BatchActions([])

        # Load nodes:
        for element in root.get("NODES", []):

            xp   = element.get("node-position", {}).get("x", 0.0)
            yp   = element.get("node-position", {}).get("y", 0.0)
            spos = QPointF(xp, yp).toPoint()

            _name = element.get("node-name", "")
            _type = element.get("node-type", 0)
            logging.info(f"Loading data for `{_name}`")

            # Create node with given size:
            height = int(element.get("node-height", {}))
            node   = canvas.create_node(cpos=spos, name=_name, push=False)
            node.resize(height - 200)

            # Execute action:
            action  = CreateNodeAction(canvas, node)
            if group_actions:
                batch.add_to_batch(action)      # Queue action

            else:
                canvas.manager.do(action)       # Execute it immediately

            # Load variable(s):
            for variable_obj in element.get("variables", []):

                stream = variable_obj.get("variable-stream", 0)
                stream = graph.StreamType.INP if stream == "StreamType.INP" else graph.StreamType.OUT

                xpos   = variable_obj.get("variable-position", {}).get("x", 0.0)
                ypos   = variable_obj.get("variable-position", {}).get("y", 0.0)

                # Create variable, don't push the action to the undo-stack yet:
                variable = node.create_handle(
                    QPointF(xpos, ypos),
                    node.unique_symbol(stream),
                    stream,
                )

                variable.info    = variable_obj.get("variable-info")
                variable.label   = variable_obj.get("variable-label")
                variable.units   = variable_obj.get("variable-units")
                variable.value   = variable_obj.get("variable-value", "")
                variable.sigma   = variable_obj.get("variable-sigma", "")
                variable.symbol  = variable_obj.get("variable-symbol", "")
                variable.minimum = variable_obj.get("variable-minimum", "")
                variable.maximum = variable_obj.get("variable-maximum", "")

                category = Category.find_category_by_label(variable_obj.get("variable-cname", ""))
                variable.cname = category.cname
                variable.color = category.color
                variable.sig_item_updated.emit(variable)

                variable.rename(variable.label)
                variable_action = CreateHandleAction(node, variable)

                # Execute action:
                if group_actions:
                    batch.add_to_batch(variable_action)
                else:
                    canvas.manager.do(variable_action)

            # Load parameter(s):
            for parameter_obj in element.get("parameters", []):

                parameter = Resource()
                parameter.info    = parameter_obj.get("parameter-info")
                parameter.label   = parameter_obj.get("parameter-label")
                parameter.units   = parameter_obj.get("parameter-units")
                parameter.symbol  = parameter_obj.get("parameter-symbol", "")
                parameter.value   = parameter_obj.get("parameter-value", "")
                parameter.sigma   = parameter_obj.get("parameter-sigma", "")
                parameter.minimum = parameter_obj.get("parameter-minimum", "")
                parameter.maximum = parameter_obj.get("parameter-maximum", "")

                category = Category.find_category_by_label(parameter_obj.get("parameter-cname", ""))
                parameter.cname = category.cname
                parameter.color = category.color

                # Add parameter to dictionary:
                node.parameters[parameter] = True

            # Add equations
            node.equations = set(element.get("equations"))

        # Load in / outflows:
        for element in root.get("FLOWS", []):

            # Get position:
            xp   = element.get("flow-position", {}).get("x", 0.0)
            yp   = element.get("flow-position", {}).get("y", 0.0)
            spos = QPointF(xp, yp).toPoint()

            # Get attributes:
            _name = element.get("flow-label", "")
            _type = element.get("flow-type" , "")

            # Create source or sink:
            if _type == "StreamType.OUT":
                stream = canvas.create_source(cpos=spos, name=_name, push=False)
                action = CreateStreamAction(canvas, stream)

                category = Category.find_category_by_label(element.get("flow-cname", ""))
                stream.socket.cname = category.cname
                stream.socket.color = category.color
                stream.socket.sig_item_updated.emit(stream.socket)

                if group_actions:   batch.add_to_batch(action)      # Queue action
                else:               canvas.manager.do(action)       # Execute it immediately

            elif _type == "StreamType.INP":
                stream = canvas.create_sink(cpos=spos, name=_name, push=False)
                action = CreateStreamAction(canvas, stream)

                category = Category.find_category_by_label(element.get("flow-cname", ""))
                stream.socket.cname = category.cname
                stream.socket.color = category.color
                stream.socket.sig_item_updated.emit(stream.socket)

                if group_actions:   batch.add_to_batch(action)      # Queue action
                else:               canvas.manager.do(action)       # Execute it immediately

        # Execute batch-actions. This will insert nodes and flows into the scene:
        batch.execute()

        # Now setup connections:
        for json_obj in root.get("CONNECTORS", []):

            sxpos = json_obj.get("connection-origin", {}).get("x", 0.0)
            sypos = json_obj.get("connection-origin", {}).get("y", 0.0)
            txpos = json_obj.get("connection-target", {}).get("x", 0.0)
            typos = json_obj.get("connection-target", {}).get("y", 0.0)

            origin = canvas.itemAt(QPointF(sxpos, sypos), QTransform())
            target = canvas.itemAt(QPointF(txpos, typos), QTransform())

            if (
                    isinstance(origin, graph.Handle) and
                    isinstance(target, graph.Handle)
            ):

                connector = graph.Connector(None,
                                            overwrite=False,
                                            origin=origin,
                                            target=target,
                                            symbol=canvas.unique_symbol())
                connector.sig_item_removed.connect(canvas.on_item_removed)

                # Add connector to database:
                canvas.edge_items[connector] = True

                # Add action to batch:
                batch.add_to_batch(ConnectHandleAction(canvas, connector))

        # Log and execute:
        logging.info(f"{len(batch.actions)} actions grouped")
        canvas.manager.do(batch)


