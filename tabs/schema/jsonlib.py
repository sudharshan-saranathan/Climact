import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform
from PyQt6.QtWidgets import QGraphicsObject, QMessageBox

from tabs.schema import graph
from custom      import *
from actions     import *

class JsonLib:
    """
    Class for serializing and deserializing schematics (nodes and connectors)
    to and from JSON format for the canvas-based process modeling application.

    Static Methods:
    ---------------
    - serialize(item):
        Serializes a single `Node` or `Connector` object to a JSON-compatible dictionary.
        Includes _node position, size, equations, and variables; or connector endpoints.

    - encode_json(canvas):
        Serializes all selected items from the canvas (or all nodes and connectors if none are selected)3
        into a JSON string. Used for exporting schematics or dragging between scenes.

    - decode_json(code: str, canvas):
        Parses a schematic JSON string and reconstructs the corresponding nodes, variables, and connectors
        on the given `Canvas`. All actions are grouped into a single undoable `BatchAction`.
    """

    @staticmethod
    def entity_to_json(_entity: Entity, _eclass: EntityClass):

        # Determine prefix:
        if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            prefix = "variable"
        elif _eclass == EntityClass.PAR:
            prefix = "parameter"
        else:
            logging.warning(f"Expected argument of type `EntityClass`, skipping JSON!")
            return None

        # Create JSON-object:
        entity_obj = {
                    f"{prefix}-eclass"   : _entity.eclass.name,
                    f"{prefix}-symbol"   : _entity.symbol,
                    f"{prefix}-label"    : _entity.label,
                    f"{prefix}-units"    : _entity.units, 
                    f"{prefix}-strid"    : _entity.strid,
                    f"{prefix}-info"     : _entity.info,
                    f"{prefix}-value"    : _entity.value,
                    f"{prefix}-sigma"    : _entity.sigma,
                    f"{prefix}-minimum"  : _entity.minimum,
                    f"{prefix}-maximum"  : _entity.maximum,
                }
        
        # For variables, add coordinates relative to _node and canvas:
        if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            
            entity_obj.update({
                f"{prefix}-position" : {            # Position relative to _node
                    "x": _entity.pos().x(),         
                    "y": _entity.pos().y()
                },
                f"{prefix}-scenepos" : {            # Position relative to canvas
                    "x": _entity.scenePos().x(),
                    "y": _entity.scenePos().y()
                }
            })

        # Return dictionary:
        return entity_obj

    @staticmethod
    def json_to_entity(
        _entity: Entity,        # Entity object to be updated.
        _eclass: EntityClass,   # Entity's class
        _object: json,          # JSON-dictionary containing entity's attributes.
        _symbol: bool = True    # Whether to set the symbol from the JSON code
    ):

        # Determine prefix:
        if _eclass in [
            EntityClass.INP,
            EntityClass.OUT,
            EntityClass.VAR]:   prefix = "variable"

        elif _eclass == EntityClass.PAR:    prefix = "parameter"
        else:   raise ValueError(f"Invalid entity class: {_eclass}")

        # If the flag is set, copy the symbol:
        if _symbol: _entity.symbol = _object.get(f"{prefix}-symbol")

        # Read other attribute(s):
        _entity.label   = _object.get(f"{prefix}-label")
        _entity.units   = _object.get(f"{prefix}-units")
        _entity.info    = _object.get(f"{prefix}-info")
        _entity.strid   = _object.get(f"{prefix}-strid")
        _entity.value   = _object.get(f"{prefix}-value")
        _entity.sigma   = _object.get(f"{prefix}-sigma")
        _entity.minimum = _object.get(f"{prefix}-minimum")
        _entity.maximum = _object.get(f"{prefix}-maximum")

    @staticmethod
    def serialize(_item: QGraphicsObject):
        """
        Serializes a single `QGraphicsObject` to a JSON object.

        Args:
            _item (QGraphicsObject): The `QGraphicsObject` to serialize.

        Returns:
            dict: A JSON-object containing the item's serialized attributes and children.
        """

        # If the instance is a _node, serialize the _node's variables, parameters, and equations:
        if isinstance(_item, graph.Node):

            # Construct a list of the _node's active variables:
            variables = [
                JsonLib.entity_to_json(entity, EntityClass.VAR)
                for entity, state in _item[EntityClass.VAR].items()
                if  state == EntityState.ACTIVE
            ]

            # Construct a list of the _node's active parameters:
            parameters = [
                JsonLib.entity_to_json(entity, EntityClass.PAR)
                for entity, state in _item[EntityClass.PAR].items()
                if  state == EntityState.ACTIVE
            ]

            # Create a list of equations:
            equations = _item[EntityClass.EQN]

            # JSON-composite:
            node_object = {
                "node-title"    : _item.title,                      # Node's title
                "node-height"   : _item.boundingRect().height(),    # Node's height
                "node-scenepos" : {                                 # Node's scene-position
                    "x": _item.scenePos().x(),
                    "y": _item.scenePos().y()
                },
                "parameters"  : parameters,                         # Node's active parameters
                "variables"   : variables,                          # Node's active variables
                "equations"   : equations                           # Node's equations
            }

            # Return the _node's JSON object:
            return node_object

        # If the instance is a terminal, serialize the terminal's attributes:
        if isinstance(_item, graph.StreamTerminal):

            # Create JSON-object:
            stream_obj = {
                "terminal-eclass"   : _item.socket.eclass.name,
                "terminal-label"    : _item.socket.label,
                "terminal-strid"    : _item.socket.strid,
                "terminal-scenepos" : {
                    "x": _item.scenePos().x(),
                    "y": _item.scenePos().y()
                }
            }

            # Return the terminal's JSON object:
            return stream_obj

        # If the instance is a connector, serialize the connector's attributes:
        if isinstance(_item, graph.Connector):

            # Create JSON-object:
            connection_obj = {
                "origin-parent-uid" : _item.origin.parentItem().uid,
                "origin-eclass"     : _item.origin.eclass.name,
                "origin-label"      : _item.origin.label,
                "origin-scenepos"   : {
                    "x": _item.origin.scenePos().x(),
                    "y": _item.origin.scenePos().y()
                },
                "target-parent-uid" : _item.target.parentItem().uid,
                "target-eclass"     : _item.target.eclass.name,
                "target-label"      : _item.target.label,
                "target-scenepos": {
                    "x": _item.target.scenePos().x(),
                    "y": _item.target.scenePos().y()
                }
            }

            # Return the connector's JSON object:
            return connection_obj

        # If the instance is not a _node, terminal, or connector, return None:
        return None

    @staticmethod
    def encode(_canvas):
        """
        Serializes all selected items from the canvas (or all active items if no items are selected)
        and returns a JSON string.

        Args:
            _canvas (Canvas): The canvas, whose items are to be serialized.

        Returns:
            str: A JSON string containing the serialized items.
        """

        item_list = (
            _canvas.selectedItems()  if _canvas.selectedItems() else
            [_item for _item, _state in _canvas.node_db.items() if _state] +     # Active nodes
            [_item for _item, _state in _canvas.term_db.items() if _state] +     # Active terminals 
            [_item for _item, _state in _canvas.conn_db.items() if _state]       # Active connectors
        )

        # Fetch serialized JSON objects for each item-type:
        node_array = [JsonLib.serialize(_item) for _item in item_list if isinstance(_item, graph.Node)]
        conn_array = [JsonLib.serialize(_item) for _item in item_list if isinstance(_item, graph.Connector)]
        term_array = [JsonLib.serialize(_item) for _item in item_list if isinstance(_item, graph.StreamTerminal)]

        # Initialize JSON objects:
        schematic = {
            "NODES"      : node_array,  # Add all active nodes
            "TERMINALS"  : term_array,  # Add all active terminals
            "CONNECTORS" : conn_array   # Add all active connectors
        }

        # Return JSON string:
        return json.dumps(schematic, indent=4)

    @staticmethod
    def decode(_code: str,
               _canvas,
               _combine: bool = False
               ):
        """
        Parses a schematic JSON string and reconstructs the corresponding nodes, variables, and connectors
        on the given `Canvas`. All actions are grouped into a single undoable `BatchAction`.

        Args:
            _code (str): The JSON string to parse.
            _canvas (Canvas): The canvas to reconstruct the schematic on.
            _combine (bool): Whether to combine the actions into a single undoable `BatchAction`.

        Returns:
            None
        """

        # Import canvas module (required for executing canvas operations):
        from tabs.schema.canvas import Canvas

        # Create a symbol map to track how variable-symbols are changed during JSON-decoding:
        _symmap = dict()

        # Initialize convenience-variables:
        root  = json.loads(_code)
        batch = BatchActions([])

        # Validate argument(s):
        if not isinstance(_code, str):      raise ValueError("Invalid JSON code")
        if not isinstance(_canvas, Canvas): raise ValueError("Invalid `Canvas` object")

        # Read JSON and execute operations:
        # Nodes:
        for node_json in root.get("NODES") or []:

            height = node_json.get("node-height")
            title  = node_json.get("node-title")
            npos   = QPointF(node_json.get("node-scenepos").get("x"),
                            node_json.get("node-scenepos").get("y")
                            )

            _node = _canvas.create_node(
                title,  # Title
                npos,   # Coordinate
                False   # Do not create a corresponding action
            )

            _node.resize(int(height) - 150) # Adjust _node's height
            _canvas.node_db[_node] = True   # Add _node to canvas' database:
            _canvas.addItem(_node)          # Add _node to canvas

            # Add action to batch:
            batch.add_to_batch(CreateNodeAction(_canvas, _node))

            # Add variable(s):
            for var_json in node_json.get("variables") or []:

                # Get variable's EntityClass:
                eclass = EntityClass.INP if (
                    var_json.get("variable-eclass") == "INP" or 
                    var_json.get("variable-eclass") == "EntityClass.INP"
                ) \
                else EntityClass.OUT

                # Get variable's coordinate:
                hpos = QPointF(
                    var_json.get("variable-position").get("x"),
                    var_json.get("variable-position").get("y")
                )

                # Instantiate new variable with given EntityClass and coordinate:
                _var = _node.create_handle(eclass, hpos)

                # Read other attribute(s):
                JsonLib.json_to_entity(
                    _var,
                    eclass,
                    var_json,
                    False
                )

                # Update variable's color and label:
                _var.rename(_var.label)
                _var.create_stream(_var.strid)
                _var.sig_item_updated.emit(_var)    # Emit signal to notify application of changes

                # Add the variable to the node's database, and modify the node's equations to use the variable's new symbol:
                _node[eclass, _var] = EntityState.ACTIVE

                # Add action to batch:
                batch.add_to_batch(CreateHandleAction(_node, _var))

            # Add parameter(s):
            for par_json in node_json.get("parameters") or []:

                # Instantiate new parameter:
                _par = Entity()
                _par.eclass = EntityClass.PAR

                # Read other attribute(s):
                JsonLib.json_to_entity(_par, EntityClass.PAR, par_json)

                # Add parameter to _node's database:
                _node[EntityClass.PAR, _par] = EntityState.ACTIVE

            # Add equations(s):
            if node_json.get("equations") or []:
                _node[EntityClass.EQN, None] = [
                    equation for equation in node_json.get("equations")
                ]

        # Terminals:
        for _term_json in root.get("TERMINALS") or []:

            # Get terminal's EntityClass and coordinate:
            eclass = EntityClass.INP if (
                _term_json.get("terminal-eclass") == "INP" or 
                _term_json.get("terminal-eclass") == "EntityClass.INP"
            ) \
            else EntityClass.OUT

            # Get terminal's coordinate:
            tpos = QPointF(
                _term_json.get("terminal-scenepos").get("x"),
                _term_json.get("terminal-scenepos").get("y")
            )

            # Create terminal:
            _terminal = _canvas.create_terminal(eclass, tpos)
            _terminal.socket.rename(_term_json.get("terminal-label"))
            _terminal.socket.create_stream(_term_json.get("terminal-strid"))
            _terminal.socket.sig_item_updated.emit(_terminal.socket)

            # Add terminal to the database and canvas:
            _canvas.term_db[_terminal] = True
            _canvas.addItem(_terminal)

        # Connections:
        for conn_json in root.get("CONNECTORS") or []:

            # Origin handle's scene-position:
            opos = QPointF(
                conn_json.get("origin-scenepos").get("x"),
                conn_json.get("origin-scenepos").get("y")
            )

            # Target handle's scene-position:
            tpos = QPointF(
                conn_json.get("target-scenepos").get("x"),
                conn_json.get("target-scenepos").get("y")
            )

            origin = _canvas.itemAt(opos, QTransform()) # Origin-reference
            target = _canvas.itemAt(tpos, QTransform()) # Target-reference

            if not isinstance(origin, graph.Handle):    continue
            if not isinstance(target, graph.Handle):    continue

            # Establish a new connection:
            try:

                # Create a new connector:
                connector = graph.Connector(_canvas.create_cuid(),
                                            origin,
                                            target,
                                            False
                                            )

                # Add connector to database and canvas:
                _canvas.conn_db[connector] = True
                _canvas.addItem(connector)

                # Add connector-creation action to batch:
                batch.add_to_batch(ConnectHandleAction(_canvas, connector))

            # If an exception occurs, print error:
            except Exception as exception:
                print(f"{exception}")
                logging.exception(f"Connector creation skipped due to an exception: {exception}")

        # Execute batch:
        if _combine: _canvas.manager.do(batch)



