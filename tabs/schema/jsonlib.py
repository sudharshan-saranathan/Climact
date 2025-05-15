import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform

from tabs.schema import graph
from custom import *
from actions import *

from PyQt6.QtWidgets import QGraphicsObject

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
    def create_json(_entity: Entity, _eclass: EntityClass):

        # Determine prefix:
        prefix = "variable" \
                    if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR] \
                    else "parameter"

        # Create JSON-object:
        entity_obj = {
                    f"{prefix}-stream"   : str(_entity.stream),
                    f"{prefix}-symbol"   : _entity.symbol,
                    f"{prefix}-label"    : _entity.label,
                    f"{prefix}-units"    : _entity.units, 
                    f"{prefix}-strid"    : _entity.strid,
                    f"{prefix}-color"    : _entity.color.name(),
                    f"{prefix}-info"     : _entity.info,
                    f"{prefix}-value"    : _entity.value,
                    f"{prefix}-sigma"    : _entity.sigma,
                    f"{prefix}-minimum"  : _entity.minimum,
                    f"{prefix}-maximum"  : _entity.maximum,
                }
        
        # If entity is a variable, add node- and scene-position:
        if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            
            entity_obj.update({
                f"{prefix}-position" : {
                    "x": _entity.pos().x(),
                    "y": _entity.pos().y()
                },
                f"{prefix}-scenepos" : {
                    "x": _entity.scenePos().x(),
                    "y": _entity.scenePos().y()
                }
            })

        return entity_obj

    @staticmethod
    def serialize(_item: QGraphicsObject):

        if isinstance(_item, graph.Node):

            variables   = list()
            equations   = list()
            parameters  = list()

            variables = [
                JsonLib.create_json(_entity, EntityClass.VAR) 
                for _entity in _item[EntityClass.INP] | _item[EntityClass.OUT]
                if  _entity.isVisible()
            ]

            parameters = [
                JsonLib.create_json(_entity, EntityClass.PAR) 
                for _entity in _item[EntityClass.PAR]
            ]

            # JSON-composite:
            node_object = {
                "node-title"    : _item.title,
                "node-height"   : _item.boundingRect().height(),
                "node-scenepos" : {
                    "x": _item.scenePos().x(),
                    "y": _item.scenePos().y()
                },
                "parameters" : parameters,
                "variables"  : variables
            }

            return node_object

        if isinstance(_item, graph.StreamTerminal):

            stream_obj = {
                "terminal-direction"  : str(_item.socket.stream),
                "terminal-label"      : _item.socket.label,
                "terminal-strid"      : _item.socket.strid,
                "terminal-color"      : _item.socket.color.name(),
                "terminal-scenepos"   : {
                    "x": _item.scenePos().x(),
                    "y": _item.scenePos().y()
                }
            }

            return stream_obj

        if isinstance(_item, graph.Connector):

            connection_obj = {
                "origin-parent-uid" : _item.origin.parentItem().uid,
                "origin-label"      : _item.origin.label,
                "origin-scenepos"   : {
                    "x": _item.origin.scenePos().x(),
                    "y": _item.origin.scenePos().y()
                },
                "target-parent-uid" : _item.target.parentItem().uid,
                "target-label"      : _item.target.label,
                "target-scenepos": {
                    "x": _item.target.scenePos().x(),
                    "y": _item.target.scenePos().y()
                }
            }

            return connection_obj

        return None

    @staticmethod
    def encode_json(_canvas):

        # Debugging:
        print(f"- Encoding JSON for canvas: {_canvas.uid}")

        # Serialize selected items. If no items are selected, serialize all active (visible) items:
        items =      _canvas.selectedItems()    \
                if   _canvas.selectedItems()    \
                else \
                [_item for _item in _canvas.node_db if _canvas.node_db[_item]] + \
                [_item for _item in _canvas.term_db if _canvas.term_db[_item]] + \
                [_item for _item in _canvas.conn_db if _canvas.conn_db[_item]]

        # Serialize items and generate JSON-objects:
        node_array = [JsonLib.serialize(item) for item in items if isinstance(item, graph.Node)]
        conn_array = [JsonLib.serialize(item) for item in items if isinstance(item, graph.Connector)]
        term_array = [JsonLib.serialize(item) for item in items if isinstance(item, graph.StreamTerminal)]

        # Initialize JSON-objects:
        schematic = {
            "NODES"      : node_array,
            "TERMINALS"  : term_array,
            "CONNECTORS" : conn_array
        }

        # Return JSON-string:
        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode_json(_code: str, 
                    _canvas, 
                    _group_actions: bool = False
                    ):

        # Import canvas module:
        from tabs.schema.canvas import Canvas

        # Convert file contents to JSON-parsable:
        root = json.loads(_code)

        # Validate argument(s):
        if not isinstance(_code, str):      raise ValueError("Invalid JSON-code")
        if not isinstance(_canvas, Canvas): raise ValueError("Invalid `Canvas` object")

        # Initialize batch-actions:
        batch = BatchActions([])

        # Read node-data, create nodes:
        for element in root.get("NODES", []):

            xp   = element.get("node-scenepos", {}).get("x", 0.0)
            yp   = element.get("node-scenepos", {}).get("y", 0.0)
            spos = QPointF(xp, yp)
            name = element.get("node-title", "")

            print(f"- Creating node: {name}")

            # Create node with given size:
            height = int(element.get("node-height", {}))
            node   = _canvas.create_node(name, spos, False)

            node.title = name
            node.resize(height - 200)

            # Create corresponding action:
            action = CreateNodeAction(_canvas, node)

            if _group_actions:  batch.add_to_batch(action)  # Queue action
            else:               _canvas.manager.do(action)  # Execute it immediately

            # Load variable(s):
            for variable_obj in element.get("variables", []):

                eclass = variable_obj.get("variable-stream", 0)
                eclass = EntityClass.INP if eclass == "EntityClass.INP" else EntityClass.OUT

                xpos   = variable_obj.get("variable-position", {}).get("x", 0.0)
                ypos   = variable_obj.get("variable-position", {}).get("y", 0.0)

                # Create variable, don't push the action to the undo-stack yet:
                variable = node.create_handle(
                    QPointF(xpos, ypos),
                    eclass
                )

                variable.symbol  = variable_obj.get("variable-symbol", "")
                variable.info    = variable_obj.get("variable-info")
                variable.label   = variable_obj.get("variable-label")
                variable.units   = variable_obj.get("variable-units")
                variable.value   = str(variable_obj.get("variable-value", ""))
                variable.sigma   = str(variable_obj.get("variable-sigma", ""))
                variable.minimum = str(variable_obj.get("variable-minimum", ""))
                variable.maximum = str(variable_obj.get("variable-maximum", ""))

                stream = _canvas.find_stream(variable_obj.get("variable-strid", ""))
                variable.strid = stream.strid
                variable.color = stream.color
                variable.sig_item_updated.emit(variable)

                variable.rename(variable.label)
                variable_action = CreateHandleAction(node, variable)

                # Add action to batch:
                if _group_actions:  batch.add_to_batch(variable_action)
                else:               _canvas.manager.do(variable_action)

            # Load parameter(s):
            for parameter_obj in element.get("parameters", []):

                parameter = Entity()
                parameter.symbol  = parameter_obj.get("parameter-symbol", "")
                parameter.info    = parameter_obj.get("parameter-info")
                parameter.label   = parameter_obj.get("parameter-label")
                parameter.units   = parameter_obj.get("parameter-units")
                parameter.value   = str(parameter_obj.get("parameter-value", ""))
                parameter.sigma   = str(parameter_obj.get("parameter-sigma", ""))
                parameter.minimum = str(parameter_obj.get("parameter-minimum", ""))
                parameter.maximum = str(parameter_obj.get("parameter-maximum", ""))

                stream = _canvas.find_stream(parameter_obj.get("parameter-strid", ""))
                parameter.strid = stream.strid
                parameter.color = stream.color

                # Add parameter to dictionary:
                node[EntityClass.PAR][parameter] = EntityState.ACTIVE

        # Load in / outflows:
        for element in root.get("TERMINALS", []):

            # Get name and position:
            xp   = element.get("terminal-scenepos", {}).get("x", 0.0)
            yp   = element.get("terminal-scenepos", {}).get("y", 0.0)
            spos = QPointF(xp, yp).toPoint()
            name = element.get("terminal-label", "")

            # Create source or sink:
            if  element.get("terminal-direction", "") == "EntityClass.OUT":

                terminal = _canvas.create_terminal(EntityClass.OUT, spos)
                action   = CreateStreamAction(_canvas, terminal)

                stream = _canvas.find_stream(element.get("terminal-strid", ""))
                terminal.socket.strid = stream.strid
                terminal.socket.color = stream.color
                terminal.socket.sig_item_updated.emit(terminal.socket)

                if _group_actions:   batch.add_to_batch(action)      # Queue action
                else:               _canvas.manager.do(action)       # Execute it immediately

            elif element.get("terminal-direction", "") == "EntityClass.INP":

                terminal = _canvas.create_terminal(EntityClass.INP, spos)
                action   = CreateStreamAction(_canvas, terminal)

                stream = _canvas.find_stream(element.get("terminal-strid", ""))
                terminal.socket.strid = stream.strid
                terminal.socket.color = stream.color
                terminal.socket.sig_item_updated.emit(terminal.socket)

                if _group_actions:   batch.add_to_batch(action)      # Queue action
                else:               _canvas.manager.do(action)       # Execute it immediately

        # Execute batch-actions. This will insert nodes and flows into the scene:
        batch.execute()

        # Now setup connections:
        for json_obj in root.get("CONNECTORS", []):

            sxpos = json_obj.get("origin-scenepos", {}).get("x", 0.0)
            sypos = json_obj.get("origin-scenepos", {}).get("y", 0.0)
            txpos = json_obj.get("target-scenepos", {}).get("x", 0.0)
            typos = json_obj.get("target-scenepos", {}).get("y", 0.0)

            origin = _canvas.itemAt(QPointF(sxpos, sypos), QTransform())
            target = _canvas.itemAt(QPointF(txpos, typos), QTransform())

            if (
                    isinstance(origin, graph.Handle) and
                    isinstance(target, graph.Handle)
            ):

                connector = graph.Connector(_canvas.create_cuid(), 
                                            origin, 
                                            target, 
                                            True
                                            )
                connector.sig_item_removed.connect(_canvas.on_item_removed)

                # Add connector to database:
                _canvas.conn_db[connector] = True
                _canvas.addItem(connector)

                # Add action to batch:
                batch.add_to_batch(ConnectHandleAction(_canvas, connector))

        # Log and execute:
        logging.info(f"{len(batch.actions)} actions grouped")
        _canvas.manager.do(batch)


