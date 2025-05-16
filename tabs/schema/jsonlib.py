import json
import logging

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QTransform

from tabs.schema import graph
from custom import *
from actions import *

from PyQt6.QtWidgets import QGraphicsObject

from tabs.schema.graph import Connector


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
    def entity_to_json(_entity: Entity, _eclass: EntityClass):

        # Determine prefix:
        prefix = "variable" \
                    if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR] \
                    else "parameter"

        # Create JSON-object:
        entity_obj = {
                    f"{prefix}-eclass"   : str(_entity.eclass),
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
    def json_to_entity(_entity: Entity,
                       _eclass: EntityClass,
                       _object: json):

        _prefix = "variable" if _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR] else "parameter"
        _entity.symbol  = _object.get(f"{_prefix}-symbol")
        _entity.label   = _object.get(f"{_prefix}-label")
        _entity.units   = _object.get(f"{_prefix}-units")
        _entity.info    = _object.get(f"{_prefix}-info")
        _entity.strid   = _object.get(f"{_prefix}-strid")
        _entity.value   = _object.get(f"{_prefix}-value")
        _entity.sigma   = _object.get(f"{_prefix}-sigma")
        _entity.value   = _object.get(f"{_prefix}-value")
        _entity.minimum = _object.get(f"{_prefix}-minimum")
        _entity.maximum = _object.get(f"{_prefix}-maximum")

        print(_entity.symbol, _entity.eclass)

    @staticmethod
    def serialize(_item: QGraphicsObject):

        if isinstance(_item, graph.Node):

            variables   = list()
            equations   = list()
            parameters  = list()

            variables = [
                JsonLib.entity_to_json(_entity, EntityClass.VAR)
                for _entity in _item[EntityClass.INP] | _item[EntityClass.OUT]
                if  _entity.isVisible()
            ]

            parameters = [
                JsonLib.entity_to_json(_entity, EntityClass.PAR)
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
                "terminal-class"    : str(_item.socket.eclass),
                "terminal-label"    : _item.socket.label,
                "terminal-strid"    : _item.socket.strid,
                "terminal-color"    : _item.socket.color.name(),
                "terminal-scenepos" : {
                    "x": _item.scenePos().x(),
                    "y": _item.scenePos().y()
                }
            }

            return stream_obj

        if isinstance(_item, graph.Connector):

            connection_obj = {
                "origin-parent-uid" : _item.origin.parentItem().uid,
                "origin-eclass"     : str(_item.origin.eclass),
                "origin-label"      : _item.origin.label,
                "origin-scenepos"   : {
                    "x": _item.origin.scenePos().x(),
                    "y": _item.origin.scenePos().y()
                },
                "target-parent-uid" : _item.target.parentItem().uid,
                "target-eclass"     : str(_item.target.eclass),
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
                    _combine: bool = False
                    ):

        # Import canvas module:
        from tabs.schema.canvas import Canvas

        # Initialize convenience-variables:
        root  = json.loads(_code)
        batch = BatchActions([])

        # Validate argument(s):
        if not isinstance(_code, str):      raise ValueError("Invalid JSON-code")
        if not isinstance(_canvas, Canvas): raise ValueError("Invalid `Canvas` object")

        # Read JSON and execute operations:
        # Nodes:
        for node_json in root.get("NODES"):

            title = node_json.get("node-title")
            npos  = QPointF(node_json.get("node-scenepos").get("x"),
                            node_json.get("node-scenepos").get("y")
                            )

            _node = _canvas.create_node(title,
                                        npos,
                                        False
                                        )
            _node.resize(int(node_json.get("node-height")) - 150)
            _canvas.node_db[_node] = True   # Add node to canvas' database:
            _canvas.addItem(_node)          # Add node to canvas

            # Add action to batch:
            batch.add_to_batch(CreateNodeAction(_canvas, _node))

            # Add variable(s):
            for var_json in node_json.get("variables"):

                eclass = EntityClass.INP if var_json.get("variable-eclass") == "EntityClass.INP" else EntityClass.OUT
                hpos   = QPointF(var_json.get("variable-position").get("x"),
                                 var_json.get("variable-position").get("y")
                                 )

                # Variable:
                _var = _node.create_handle(hpos, eclass)
                _node[eclass, _var] = EntityState.ACTIVE

                # Read other attribute(s):
                JsonLib.json_to_entity(_var, eclass, var_json)
                _var.color = _canvas.find_stream(_var.strid).color
                _var.rename(_var.label)

                # Add action to batch:
                batch.add_to_batch(CreateHandleAction(_node, _var))

            # Add parameter(s):
            for par_json in node_json.get("parameters"):

                # Parameter:
                _par = Entity()
                _par.eclass = EntityClass.PAR

                # Read other attribute(s):
                JsonLib.json_to_entity(_par, EntityClass.PAR, par_json)

                # Add to node:
                _node[EntityClass.PAR, _par] = EntityState.ACTIVE

            # Add equations(s):
            if node_json.get("equations"):  _node[EntityClass.EQN, None] = [equation for equation in node_json.get("equations")]

        # Terminals:
        for term_json in root.get("TERMINALS"):

            eclass = EntityClass.INP if term_json.get("terminal-eclass") == "EntityClass.INP" else EntityClass.OUT
            tpos   = QPointF(term_json.get("terminal-scenepos").get("x"),
                             term_json.get("terminal-scenepos").get("y"),
                             )

            # Create terminal:
            _terminal = _canvas.create_terminal(eclass, tpos)
            _terminal.socket.rename(term_json.get("terminal-label"))
            _terminal.socket.strid = term_json.get("terminal-strid")
            _terminal.socket.color = _canvas.find_stream(_terminal.socket.strid).color
            _terminal.socket.sig_item_updated.emit(_terminal.socket)

            # Add terminal to database and canvas:
            _canvas.term_db[_terminal] = True
            _canvas.addItem(_terminal)

        # Connections:
        for conn_json in root.get("CONNECTORS"):

            opos = QPointF(conn_json.get("origin-scenepos").get("x"),   # Scene-position of the origin handle
                           conn_json.get("origin-scenepos").get("y")
                           )

            tpos = QPointF(conn_json.get("target-scenepos").get("x"),   # Scene-position of the target handle
                           conn_json.get("target-scenepos").get("y")
                           )

            origin = _canvas.itemAt(opos, QTransform()) # Reference to the origin handle
            target = _canvas.itemAt(tpos, QTransform()) # Reference to the target handle

            # Create connector:
            try:
                connector = Connector(_canvas.create_cuid(),
                                      origin,
                                      target,
                                      False
                                      )

                # Add connector to canvas:
                _canvas.conn_db[connector] = True
                _canvas.addItem(connector)

            except Exception as exception:
                print(f"An exception occurred: {exception}")



